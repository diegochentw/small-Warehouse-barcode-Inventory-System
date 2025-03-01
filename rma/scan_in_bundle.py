from flask import Blueprint, render_template, request, url_for, flash, redirect
from rma.auth import login_required
from rma.db import get_db
from . import serialize_datetime
import json
import logging
import traceback
import time
import re

bp_scan_in = Blueprint('scan_in', __name__, url_prefix='/shipment/scan_in')

# @audit-info 列表
@bp_scan_in.route('/')
@login_required
def scan_in():
    db = get_db()
    shipments = db.execute('''
        SELECT 
            s.shipment_id, s.type, s.created_date AS shipment_date, s.note, 
            c.customer_name, c.contact, c.type AS customer_type, c.phone, c.email, c.address, c.notes AS customer_notes,
            sp.product_id,
            cg.category_name,               
            ps.ean_code, ps.upc_code, ps.model_name, ps.product_name, ps.created_date AS product_sku_created_date,
            p.sku_id, p.erp_no, p.product_sn, p.manufacturing_date, p.creator
        FROM shipment s
        JOIN customer c ON s.customer_id = c.customer_id
        JOIN shipment_product sp ON s.shipment_id = sp.shipment_id
        JOIN category cg ON cg.category_id = ps.category_id
        JOIN product p ON sp.product_id = p.product_id
        JOIN product_sku ps ON p.sku_id = ps.sku_id
        WHERE s.type = '進倉'
        ORDER BY s.created_date DESC
    ''').fetchall()


    json_results = []
    for shipment in shipments:
        shipment_dict = {
            'shipment_id': shipment['shipment_id'],
            'type': shipment['type'],
            'category_name': shipment['category_name'],            
            'product_sn': shipment['product_sn'],
            'customer_name': shipment['customer_name'],
            'product_name': shipment['product_name'],
            'note': shipment['note'],            
            'created_date': serialize_datetime(shipment['shipment_date']),
        }
        json_results.append(shipment_dict)

    with open('rma/json/shipments_in.json', 'w') as json_file:
         json.dump(json_results, json_file, default=serialize_datetime)

    return render_template('shipment/scan_in.html', shipments = shipments )

def get_product_id(product_sn):
    # Replace this with a function that retrieves the product_id based on product_sn
    # You need to query your database to find the product_id for a given product_sn
    db = get_db()
    result = db.execute('SELECT product_id FROM product WHERE product_sn = ?', (product_sn,))
    product = result.fetchone()
    if product:
        return product['product_id']
    return None 

# @audit-ok 單筆進貨
@bp_scan_in.route('/scan_in_single', methods=('GET', 'POST'))
@login_required
def scan_in_single():
    customers = None    

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product_sn = request.form['product_sn']  # Get a list of product serial numbers
        note = request.form['note']

        error = None

        if not product_sn:
            error = '請至少輸入一個產品序號'
        if error is not None:
            flash(error)
        else:
            try:
                db = get_db()

                # Check if the product serial number already exists in the shipment_product table
                existing_product_query = '''
                SELECT sp.shipment_id 
                FROM shipment_product sp 
                JOIN product p ON sp.product_id = p.product_id 
                WHERE p.product_sn = ?
                '''
                existing_shipment = db.execute(existing_product_query, (product_sn,)).fetchone()
                
                if existing_shipment:
                    flash(f'產品序號{product_sn}已有進貨紀錄，無法再度進貨')

                else:

                    # Insert into shipment table first, but without category_id at the beginning
                    db.execute(
                        'INSERT INTO shipment (customer_id, note, type) VALUES (?, ?, "進倉")',
                        (customer_id, note)
                    )
                    shipment_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]  # Get the ID of the newly inserted shipment

                    product_id = get_product_id(product_sn)
                    logging.info(f"Retrieved product_id: {product_id} for product_sn: {product_sn}")

                    if product_id is not None:
                        # Insert into shipment_product table
                        db.execute(
                            'INSERT INTO shipment_product (shipment_id, product_id) VALUES (?, ?)', 
                            (shipment_id, product_id)
                        )
                       
                        # Fetch category_id based on product_id
                        # TODO:
                        category_query = '''
                            SELECT p.product_id, ps.product_name 
                            FROM product p
                            JOIN product_sku ps ON p.sku_id = ps.sku_id
                            WHERE p.product_id = ?
                        '''
                        category_id = db.execute(category_query, (product_id,)).fetchone()[0]
                        
                        # Now, update the shipment entry with the fetched category_id
                        update_shipment_query = 'UPDATE shipment SET category_id = ? WHERE shipment_id = ?'
                        db.execute(update_shipment_query, (category_id, shipment_id))
                        db.commit()
                        flash('進倉成功')                       
                    else:
                        logging.warning(f"No matching product_id found for product_sn: {product_sn}")
                        flash('找不到匹配的產品序號')

                    return redirect(url_for('overview.shipment.scan_in'))

            except Exception as e:
                # logging.error(f"SQL Error: {e}")
                logging.error(f"SQL Error: {e}\n{traceback.format_exc()}")
                db.rollback()

    if customers is None:
        db = get_db()
        customers = db.execute('SELECT customer_id, customer_name FROM customer').fetchall()    

    return render_template('shipment/scan_in_single.html', customers = customers)

# @audit-ok 批次進貨

@bp_scan_in.route('/scan_in_batch', methods=('GET', 'POST'))
@login_required
def scan_in_batch():
    customers = None    

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product_sn_list = request.form.getlist('product_sn[]')  # 取得所有產品序號
        note = request.form['note']

        logging.info(f"Received data: customer_id: {customer_id}, product_sn_list: {product_sn_list}")

        error = None

        if not product_sn_list:
            error = '請至少輸入一個產品序號'
        if error is not None:
            flash(error)
        else:
            try:
                db = get_db()

                db.execute(
                    'INSERT INTO shipment (customer_id, type, note) VALUES (?, "進倉",?)',
                    (customer_id, note)
                )
                shipment_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]  # Get the ID of the newly inserted shipment
                logging.info(f"Inserted shipment with ID: {shipment_id}")

                for product_sn in product_sn_list:
                    product_id = get_product_id(product_sn)
                    logging.info(f"Retrieved product_id: {product_id} for product_sn: {product_sn}")

                    if product_id is not None:
                        db.execute(
                            'INSERT INTO shipment_product (shipment_id, product_id) VALUES (?, ?)', 
                            (shipment_id, product_id)
                        )
                        logging.info(f"Inserted product_sn: {product_sn} with product_id: {product_id} into shipment_product")
                        
                        category_query = '''
                            SELECT ps.category_id
                            FROM product_sku ps
                            JOIN product p ON ps.sku_id = p.sku_id
                            WHERE product_id = ?                            
                        '''
                        category_id = db.execute(category_query, (product_id,)).fetchone()[0]
                        
                        update_shipment_query = 'UPDATE shipment SET category_id = ? WHERE shipment_id = ?'
                        db.execute(update_shipment_query, (category_id, shipment_id))

                db.commit()
                # flash('進倉成功')
                flash('進倉成功, 產品序號明細如下:')
                count = 0
                # flash(f'總共輸入{len(product_sn_list)} 筆資料')

                product_sn_string = ', '.join([product_sn for product_sn in product_sn_list if product_sn])  # 使用join()將產品序號串接成字串
                flash(product_sn_string)

                for product_sn in product_sn_list:
                    if product_sn:  # 檢查產品序號是否為空值
                        count += 1

                flash(f'有效產品序號數量: {count}')


                return redirect(url_for('overview.shipment.scan_in'))

            except Exception as e:
                logging.error(f"SQL Error: {e}")
                db.rollback()

    if customers is None:
        db = get_db()
        customers = db.execute('SELECT customer_id, customer_name FROM customer').fetchall()    

    return render_template('shipment/scan_in_batch.html', customers = customers)

def split_alpha_num(s):
    # 使用正規表達式比對序號列中的字母及數字
    matches = re.findall(r'[A-Za-z]+|\d+', s)

    # 增加判斷式做錯誤檢查，7/22 增加如果為純數字序號不會跳出報錯警告
    if not matches or (len(matches) < 2 and not s.isdigit()):
        raise ValueError(f"序號列 '{s}' 格式不正確")
    
    # 返回分割後的字母及數字
    return matches[:-1], matches[-1]  # 假設最後一個比對項目是數字

def generate_serial_numbers(start_sn, end_sn):
    start_parts, start_num = split_alpha_num(start_sn)
    end_parts, end_num = split_alpha_num(end_sn)

    # 驗證除了後段為數字外，其他部分是否一致
    if start_parts != end_parts:
        raise ValueError("批次序號的英文字母無法比對")

    num_length = len(start_num)
    serial_numbers = [
        ''.join(start_parts) + str(i).zfill(num_length)
        for i in range(int(start_num), int(end_num) + 1)
    ]
    return serial_numbers

try:
    start_product_sn = "ABC001"
    end_product_sn = "ABC010"
    product_sn_list = generate_serial_numbers(start_product_sn, end_product_sn)
    print(product_sn_list)
except ValueError as e:
    print(e)

# @audit-info 輸入序號範圍進貨

@bp_scan_in.route('/scan_in_range', methods=('GET', 'POST'))
def scan_in_range():
    db = get_db()
    customers = db.execute('SELECT customer_id, customer_name FROM customer').fetchall()

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        start_product_sn = request.form['start_product_sn']
        end_product_sn = request.form['end_product_sn']

        try:
            product_sn_list = generate_serial_numbers(start_product_sn, end_product_sn)
        except ValueError as ve:
            flash(str(ve))
            return render_template('shipment/scan_in_range.html', customers=customers)

        if not product_sn_list:
            flash('請至少輸入一個產品序號')
            return render_template('shipment/scan_in_range.html', customers=customers)

        # 檢查序號的庫存情況
        serials_can_be_stocked = []
        for sn in product_sn_list:
            net_inflow = db.execute(
                '''SELECT 
                    SUM(CASE WHEN s.type = '進倉' THEN 1 ELSE 0 END) - 
                    SUM(CASE WHEN s.type = '出倉' THEN 1 ELSE 0 END) AS net_inflow
                FROM shipment_product sp
                JOIN shipment s ON sp.shipment_id = s.shipment_id
                JOIN product p ON sp.product_id = p.product_id
                WHERE p.product_sn = ?
                GROUP BY sp.product_id''',
                (sn,)
            ).fetchone()

            # 判斷庫存是否為0或負數
            if net_inflow is None or net_inflow[0] <= 0:
                serials_can_be_stocked.append(sn)

        # 過濾掉不可進貨的序號
        product_sn_list = [sn for sn in product_sn_list if sn in serials_can_be_stocked]

        if not product_sn_list:
            flash('無有效的產品序號可進貨')
            return render_template('shipment/scan_in_range.html', customers=customers)

        # 插入資料到資料庫
        db.execute('INSERT INTO shipment (customer_id, type) VALUES (?, "進倉")', (customer_id,))
        shipment_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        product_ids = {sn: get_product_id(sn) for sn in product_sn_list if get_product_id(sn) is not None}
        data_to_insert = [(shipment_id, product_ids[sn]) for sn in product_sn_list if product_ids[sn] is not None]
        db.executemany('INSERT INTO shipment_product (shipment_id, product_id) VALUES (?, ?)', data_to_insert)
        
        db.commit()
        flash('進倉成功')
        return redirect(url_for('overview.scan_in.scan_in'))

    return render_template('shipment/scan_in_range.html', customers=customers)


# @audit-info 建立產品進貨

@bp_scan_in.route('/create_and_scan_single_product', methods=('GET', 'POST'))
@login_required
def create_and_scan_single_product():
    customers = None
    categories = None

    db = get_db()
    customers = db.execute('SELECT customer_id, customer_name FROM customer').fetchall()
    categories = db.execute('SELECT category_id, category_name FROM category').fetchall()

    if request.method == 'POST':
        # 共同的參數
        product_sn = request.form['product_sn']
        # 產品建立參數
        category_id = request.form['category_id']
        product_name = request.form['product_name']
        model_name = request.form['model_name']
        erp_no = request.form['erp_no']
        ean_code = request.form['ean_code']
        upc_code = request.form['upc_code']
        manufacturing_date = request.form['manufacturing_date']
        # 掃碼參數
        customer_id = request.form['customer_id']
        note = request.form['note']

        error = None

        if not product_sn:
            error = '產品序號為必填'
        
        if error is not None:
            flash(error)
        else:
            try:
                existing_product_query = 'SELECT product_id FROM product WHERE product_sn = ?'
                existing_product = db.execute(existing_product_query, (product_sn,)).fetchone()
                
                if not existing_product:
                    # 進行產品建立
                    manufacturing_date += " 00:00:00"
                    db.execute(
                        'INSERT INTO product (category_id, product_name, model_name, erp_no, product_sn, ean_code, upc_code, manufacturing_date)'
                        ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                        (category_id, product_name, model_name, erp_no, product_sn, ean_code, upc_code, manufacturing_date)
                    )

                # 接著進行進貨掃碼
                product_id = get_product_id(product_sn)
                
                if product_id is not None:
                    db.execute(
                        'INSERT INTO shipment (customer_id, note, type) VALUES (?, ?, "進倉")',
                        (customer_id, note)
                    )
                    shipment_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                    db.execute(
                        'INSERT INTO shipment_product (shipment_id, product_id) VALUES (?, ?)',
                        (shipment_id, product_id)
                    )
                    
                    category_query = 'SELECT category_id FROM product WHERE product_id = ?'
                    category_id = db.execute(category_query, (product_id,)).fetchone()[0]
                    update_shipment_query = 'UPDATE shipment SET category_id = ? WHERE shipment_id = ?'
                    db.execute(update_shipment_query, (category_id, shipment_id))

                    db.commit()
                    flash('產品建立及進倉成功')
                else:
                    flash('找不到匹配的產品序號')
            
            except Exception as e:
                db.rollback()
                flash(f"發生錯誤: {e}")

        return redirect(url_for('overview.scan_in.scan_in'))

    return render_template('shipment/create_and_scan_single_product.html', customers=customers, categories=categories)


# @audit-issue 進貨資料更新
@bp_scan_in.route('/shipment_update/<int:shipment_id>', methods=('GET', 'POST'))
@login_required
def shipment_update(shipment_id):
    db = get_db()
    shipment = db.execute('''
        SELECT 
            s.shipment_id, s.type, s.created_date AS shipment_date, s.note, 
            c.customer_name, c.contact, c.type AS customer_type, c.phone, c.email, c.address, c.notes AS customer_notes,
            sp.product_id,
            cg.category_name,               
            ps.ean_code, ps.upc_code, ps.model_name, ps.product_name, ps.created_date AS product_sku_created_date,
            p.sku_id, p.erp_no, p.product_sn, p.manufacturing_date, p.creator
        FROM shipment s
        JOIN customer c ON s.customer_id = c.customer_id
        JOIN shipment_product sp ON s.shipment_id = sp.shipment_id
        JOIN category cg ON cg.category_id = ps.category_id
        JOIN product p ON sp.product_id = p.product_id
        JOIN product_sku ps ON p.sku_id = ps.sku_id
        WHERE s.shipment_id = ?
    ''', (shipment_id,)).fetchone()

    if shipment is None:
        return redirect(url_for('overview.scan_in.scan_in'))
    
    if request.method == 'POST':
        new_shipment_id = request.form['shipment_id']
        customer_id = request.form['customer_id']
        note = request.form['note']
        error = None

        if error:
            return render_template('shipment/update.html', error=error, shipment=shipment, shipment_id=shipment_id)

        if not new_shipment_id or not customer_id:
            error = '無效輸入'
            return render_template('shipment/update.html', error=error, shipment_id=shipment_id)  # 添加錯誤訊息

        else:
            db.execute(
            '''
            UPDATE shipment SET shipment_id = ?, customer_id = ?, note = ?
            WHERE shipment_id = ?

            ''',
            (new_shipment_id, customer_id, note, shipment_id)
            )
            db.commit()
            return redirect(url_for('overview.scan_in.scan_in'))
        
        
    return render_template('shipment/update.html', shipment_id = shipment_id, shipment=shipment)

# @audit-info 刪除資料
@bp_scan_in.route('/shipment_delete/<int:shipment_id>', methods=('GET', 'POST'))
@login_required
def shipment_delete(shipment_id):
    db = get_db()
    db.execute('DELETE FROM shipment_product WHERE shipment_id = ?', (shipment_id,))
    db.execute('DELETE FROM shipment WHERE shipment_id = ?', (shipment_id,))
    db.commit()
    return redirect(url_for('overview.scan_in.scan_in'))
