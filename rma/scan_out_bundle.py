from flask import Blueprint, render_template, request, url_for, flash, redirect
from . import serialize_datetime
from rma.auth import login_required
from rma.db import get_db
import logging
import json
import time

bp_scan_out = Blueprint('scan_out', __name__, url_prefix='/shipment/scan_out')

def get_product_id(product_sn):
    # Replace this with a function that retrieves the product_id based on product_sn
    # You need to query your database to find the product_id for a given product_sn
    db = get_db()
    result = db.execute('SELECT product_id FROM product WHERE product_sn = ?', (product_sn,))
    product = result.fetchone()
    if product:
        return product['product_id']
    return None 

# @audit-ok 列表

@bp_scan_out.route('/')
@login_required
def scan_out():
    db = get_db()
    shipments_out = db.execute('''
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
        WHERE s.type = '出倉'
        ORDER BY s.created_date DESC
    ''').fetchall()


    json_results = []
    for shipment_out in shipments_out:
        shipment_out_dict = {
            'shipment_id': shipment_out['shipment_id'],
            'type': shipment_out['type'],
            'category_name': shipment_out['category_name'],            
            'product_sn': shipment_out['product_sn'],
            'customer_name': shipment_out['customer_name'],
            'product_name': shipment_out['product_name'],
            'note': shipment_out['note'],            
            'created_date': serialize_datetime(shipment_out['shipment_date']),
        }
        json_results.append(shipment_out_dict)

    with open('rma/json/shipments_out.json', 'w') as json_file:
         json.dump(json_results, json_file, default=serialize_datetime)

    return render_template('shipment/scan_out.html', shipments_out = shipments_out )

# @audit-ok 單品出倉

@bp_scan_out.route('/scan_out_single', methods=('GET', 'POST'))
@login_required
def scan_out_single():
    customers = None
    db = get_db()

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product_sn = request.form['product_sn']
        note = request.form['note']

        error = None

        if not product_sn:
            error = '請至少輸入一個產品序號'
        if error is not None:
            flash(error)          
        else:
            db = get_db()

            existing_product_query = '''
                SELECT sp.shipment_id 
                FROM shipment_product sp
                JOIN shipment s ON sp.shipment_id = s.shipment_id
                WHERE sp.product_id = (SELECT product_id FROM product WHERE product_sn = ? )
                AND s.type = "出倉"
            '''
            existing_shipment = db.execute(existing_product_query, (product_sn,)).fetchone()

            rma_check_query = '''
                SELECT rma.rma_id 
                FROM rma
                JOIN rma_product rp ON rma.rma_id = rp.rma_id
                WHERE rp.product_id = (SELECT product.product_id FROM product WHERE product.product_sn = ? )
            '''

            inventory_check_query = '''
                SELECT 
                    SUM(CASE WHEN s.type = '進倉' THEN 1 ELSE 0 END) - 
                    SUM(CASE WHEN s.type = '出倉' THEN 1 ELSE 0 END) AS net_inflow
                FROM shipment_product sp
                JOIN shipment s ON sp.shipment_id = s.shipment_id
                WHERE sp.product_id = (
                    SELECT product_id 
                    FROM product 
                    WHERE product_sn = ? 
                )
                GROUP BY sp.product_id
            '''
            net_inflow = db.execute(inventory_check_query, (product_sn,)).fetchone()
            if net_inflow and net_inflow['net_inflow'] > 0:
                # 如果庫存足夠，檢查是否存在出倉和 RMA 紀錄
                has_rma = db.execute(rma_check_query, (product_sn,)).fetchone()

                if existing_shipment and not has_rma:
                    flash(f'出倉成功，需注意此產品序號{product_sn}曾有出倉紀錄且再次進貨')
                    proceed_with_shipment = True
                elif existing_shipment and has_rma:
                    flash(f'產品序號{product_sn}已有出倉紀錄，但因為有RMA紀錄，所以允許再度出倉')
                    proceed_with_shipment = True
                else:
                    # 沒有出倉紀錄或者有 RMA 紀錄
                    proceed_with_shipment = True
            else:
                flash(f'產品序號 {product_sn} 的庫存不足無法出倉，請檢查是否需要二次以上進貨紀錄')
                proceed_with_shipment = False

            # If it's okay to proceed with shipment, insert records into the database
            if proceed_with_shipment:
                try:
                    #1st step: insert into shipment table
                    db.execute(
                        'INSERT INTO shipment (customer_id, note, type) VALUES (?, ?, "出倉")',
                        (customer_id, note)
                    )
                    shipment_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

                    product_id = get_product_id(product_sn)
                    if product_id is not None:
                        #2nd step: insert into shipment_product table
                        db.execute(
                            'INSERT INTO shipment_product (shipment_id, product_id) VALUES (?, ?)',
                            (shipment_id, product_id)
                        )
                    category_query = '''
                    SELECT category_id 
                    FROM product p
                    JOIN product_sku ps ON ps.sku_id = p.sku_id
                    WHERE product_id = ?
                    '''
                    category_id = db.execute(category_query, (product_id,)).fetchone()[0]

                    #3rd step: update the category_id
                    update_shipment_query = 'UPDATE shipment SET category_id = ? WHERE shipment_id = ?'
                    db.execute(update_shipment_query, (category_id, shipment_id))
                    
                    db.commit()
                    
                    flash('出倉成功')
                except Exception as e:
                    logging.error(f"SQL Error: {e}")
                    db.rollback()

    if customers is None:
        db = get_db()
        customers = db.execute('SELECT customer_id, customer_name FROM customer').fetchall()

    return render_template('shipment/scan_out_single.html', customers = customers)

# @audit-ok 批次出倉

@bp_scan_out.route('/scan_out_batch', methods=('GET', 'POST'))
@login_required
def scan_out_batch():
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
                    'INSERT INTO shipment (customer_id, type, note) VALUES (?, "出倉",?)',
                    (customer_id, note)
                )
                shipment_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]  # Get the ID of the newly inserted shipment
                logging.info(f"Inserted shipment with ID: {shipment_id}")
                batch_successful = True

                for product_sn in product_sn_list:
                    existing_product_query = '''
                    SELECT sp.shipment_id 
                    FROM shipment_product sp
                    JOIN shipment s ON sp.shipment_id = s.shipment_id
                    WHERE sp.product_id = (SELECT product_id FROM product WHERE product_sn = ? )
                    AND s.type = "出倉"
                    '''
                    existing_shipment = db.execute(existing_product_query, (product_sn,)).fetchone()
                    rma_check_query = '''
                        SELECT rma.rma_id 
                        FROM rma
                        JOIN rma_product rp ON rma.rma_id = rp.rma_id
                        WHERE rp.product_id = (SELECT product.product_id FROM product WHERE product.product_sn = ? )
                    '''
                    inventory_check_query = '''
                        SELECT 
                            SUM(CASE WHEN s.type = '進倉' THEN 1 ELSE 0 END) - 
                            SUM(CASE WHEN s.type = '出倉' THEN 1 ELSE 0 END) AS net_inflow
                        FROM shipment_product sp
                        JOIN shipment s ON sp.shipment_id = s.shipment_id
                        WHERE sp.product_id = (
                            SELECT product_id 
                            FROM product 
                            WHERE product_sn = ? 
                        )
                        GROUP BY sp.product_id
                    '''
                    
                    net_inflow = db.execute(inventory_check_query, (product_sn,)).fetchone()

                    if net_inflow and net_inflow['net_inflow'] > 0:
                        # 如果庫存足夠則允許出倉
                            proceed_with_shipment = True
                    else:
                        flash(f'產品序號 {product_sn} 的庫存不足無法出倉，請檢查是否需要再次進倉')
                        proceed_with_shipment = False
                        batch_successful = False
                        continue

                    if proceed_with_shipment:
                        product_id = get_product_id(product_sn)
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
                if batch_successful:
                    flash('出倉成功')
                return redirect(url_for('overview.scan_out'))

            except Exception as e:
                logging.error(f"SQL Error: {e}")
                db.rollback()

    if customers is None:
        db = get_db()
        customers = db.execute('SELECT customer_id, customer_name FROM customer').fetchall()    

    return render_template('shipment/scan_out_batch.html', customers=customers)

def generate_serial_numbers(start_sn, end_sn):
    start_alpha = ''.join(filter(str.isalpha, start_sn))
    start_num = ''.join(filter(str.isdigit, start_sn))
    
    end_alpha = ''.join(filter(str.isalpha, end_sn))
    end_num = ''.join(filter(str.isdigit, end_sn))
    
    if start_alpha != end_alpha:
        raise ValueError("英文字母部分不相同.")
    
    return [
        start_alpha + str(i).zfill(len(start_num))
        for i in range(int(start_num), int(end_num) + 1)
    ]

# @audit-info 序號範圍出倉

@bp_scan_out.route('/scan_out_range', methods=('GET', 'POST'))
def scan_out_range():
    db = get_db()
    customers = db.execute('SELECT customer_id, customer_name FROM customer').fetchall()
    
    if request.method == 'POST':
        start_time = time.time()  # Start timestamp
        
        customer_id = request.form['customer_id']
        start_product_sn = request.form['start_product_sn']
        end_product_sn = request.form['end_product_sn']

        try:
            product_sn_list = generate_serial_numbers(start_product_sn, end_product_sn)

        except ValueError as ve:
            flash(str(ve))
            return render_template('shipment/scan_out_range.html', customers=customers)

        if not product_sn_list:
            flash('請至少輸入一個產品序號')
            return render_template('shipment/scan_out_range.html', customers=customers)

        # 檢查序號的庫存情況
        serials_with_positive_stock = []
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

            # 判斷庫存是否大於0
            if net_inflow and net_inflow[0] > 0:
                serials_with_positive_stock.append(sn)

        # 過濾掉庫存不足的序號
        product_sn_list = [sn for sn in product_sn_list if sn in serials_with_positive_stock]

        if not product_sn_list:
            flash('無庫存足夠的產品序號可出倉')
            return render_template('shipment/scan_out_range.html', customers=customers)

        # 出倉操作
        db.execute('INSERT INTO shipment (customer_id, type) VALUES (?, "出倉")', (customer_id,))
        shipment_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        product_ids = {sn: get_product_id(sn) for sn in product_sn_list}
        data_to_insert = [(shipment_id, product_ids[sn]) for sn in product_sn_list if product_ids[sn] is not None]
        db.executemany('INSERT INTO shipment_product (shipment_id, product_id) VALUES (?, ?)', data_to_insert)

        db.commit()
        flash('出倉成功')
        return redirect(url_for('overview.scan_out.scan_out'))

    return render_template('shipment/scan_out_range.html', customers=customers)

# @audit-issue 出貨資料更新
# @bp_scan_out.route('/shipment_update/<int:shipment_id>', methods=('GET', 'POST'))
# @login_required
# def shipment_update(shipment_id):
#     db = get_db()
#     shipment = db.execute('''
#         SELECT 
#             s.shipment_id, s.type, s.created_date AS shipment_date, s.note, 
#             c.customer_name, c.contact, c.type AS customer_type, c.phone, c.email, c.address, c.notes AS customer_notes,
#             sp.product_id,
#             cg.category_name,               
#             ps.ean_code, ps.upc_code, ps.model_name, ps.product_name, ps.created_date AS product_sku_created_date,
#             p.sku_id, p.erp_no, p.product_sn, p.manufacturing_date, p.creator
#         FROM shipment s
#         JOIN customer c ON s.customer_id = c.customer_id
#         JOIN shipment_product sp ON s.shipment_id = sp.shipment_id
#         JOIN category cg ON cg.category_id = ps.category_id
#         JOIN product p ON sp.product_id = p.product_id
#         JOIN product_sku ps ON p.sku_id = ps.sku_id
#         WHERE s.shipment_id = ?
#     ''', (shipment_id,)).fetchone()

#     # 查詢所有客戶資料
#     customers = db.execute('SELECT customer_id, customer_name FROM customer').fetchall()

#     if shipment is None:
#         return redirect(url_for('overview.scan_out.scan_out'))
    
#     if request.method == 'POST':
#         # new_shipment_id = request.form['shipment_id']
#         customer_id = request.form['customer_id']
#         note = request.form['note']
#         error = None

#         if error:
#             return render_template('shipment/update.html', error=error, shipment=shipment, shipment_id=shipment_id)

#         if not customer_id:
#             error = '無效輸入'
#             return render_template('shipment/update.html', error=error, shipment_id=shipment_id)  # 添加錯誤訊息

#         else:
#             db.execute(
#             '''
#             UPDATE shipment SET customer_id = ?, note = ?
#             WHERE shipment_id = ?

#             ''',
#             (customer_id, note, shipment_id)
#             )
#             db.commit()
#             return redirect(url_for('overview.scan_out.scan_out'))
        
        
#     return render_template('shipment/scan_out_update.html', shipment_id = shipment_id, shipment=shipment, customers=customers)

@bp_scan_out.route('/shipment_update/<int:shipment_id>', methods=('GET', 'POST'))
@login_required
def shipment_update(shipment_id):
    shipment, customers = get_shipment_and_customers(shipment_id)

    if shipment is None:
        return redirect(url_for('overview.scan_out.scan_out'))

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        note = request.form['note']

        if not customer_id:
            error = '無效輸入'
            return render_template('shipment/scan_out_update.html', error=error, shipment_id=shipment_id)

        update_shipment(shipment_id, customer_id, note)
        return redirect(url_for('overview.scan_out.scan_out'))

    return render_template('shipment/scan_out_update.html', shipment=shipment, customers=customers)

def get_shipment_and_customers(shipment_id):
    db = get_db()
    # 按需進行數據庫查詢
    shipment = db.execute('SELECT * FROM shipment WHERE shipment_id = ?', (shipment_id,)).fetchone()
    customers = db.execute('SELECT customer_id, customer_name FROM customer').fetchall()
    return shipment, customers

def update_shipment(shipment_id, customer_id, note):
    db = get_db()
    db.execute('UPDATE shipment SET customer_id = ?, note = ? WHERE shipment_id = ?', (customer_id, note, shipment_id))
    db.commit()

# @audit-info 刪除資料
@bp_scan_out.route('/shipment_delete/<int:shipment_id>', methods=('GET', 'POST'))
@login_required
def shipment_delete(shipment_id):
    db = get_db()
    db.execute('DELETE FROM shipment_product WHERE shipment_id = ?', (shipment_id,))
    db.execute('DELETE FROM shipment WHERE shipment_id = ?', (shipment_id,))
    db.commit()
    return redirect(url_for('overview.scan_out.scan_out'))
