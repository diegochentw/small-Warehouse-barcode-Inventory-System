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

            has_rma = db.execute(rma_check_query, (product_sn,)).fetchone()

            proceed_with_shipment = False

            if existing_shipment and not has_rma:
                flash(f'產品序號{product_sn}已有出倉紀錄，無法再度出倉')
            elif existing_shipment and has_rma:
                flash(f'產品序號{product_sn}已有出倉紀錄，但因為有RMA紀錄，所以允許再度出倉')
                proceed_with_shipment = True
            else:
                proceed_with_shipment = True

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
                    has_rma = db.execute(rma_check_query, (product_sn,)).fetchone()

                    proceed_with_shipment = False

                    if existing_shipment and not has_rma:
                        flash(f'產品序號{product_sn}已有出倉紀錄，無法再度出倉')
                        batch_successful = False
                    elif existing_shipment and has_rma:
                        flash(f'產品序號{product_sn}提醒!已有出倉紀錄，因存在RMA紀錄所以允許再度出倉')
                        proceed_with_shipment = True
                    else:
                        proceed_with_shipment = True

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

# @audit-info 批次出倉資料
@bp_scan_out.route('/scan_out_range', methods=('GET', 'POST'))
def scan_out_range():
    customers = None
    
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

        error = None
        if not product_sn_list:
            error = '請至少輸入一個產品序號'
        
        if error is not None:
            flash(error)
        else:
            db_start_time = time.time()  # DB operations start timestamp
            try:
                db = get_db()

                # Insert shipment
                db.execute('INSERT INTO shipment (customer_id, type) VALUES (?, "出倉")', (customer_id,))
                shipment_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

                # Get product IDs in bulk
                product_ids = {sn: get_product_id(sn) for sn in product_sn_list}

                # Batch insert for shipment_product
                data_to_insert = [(shipment_id, product_ids[sn]) for sn in product_sn_list if product_ids[sn] is not None]
                db.executemany('INSERT INTO shipment_product (shipment_id, product_id) VALUES (?, ?)', data_to_insert)

                # Get category_ids in bulk
                category_start_time = time.time()  # Category fetch start timestamp
                product_ids_values = list(filter(None, product_ids.values()))
                category_query = '''
                SELECT p.product_id, ps.product_name 
                FROM product p
                JOIN product_sku ps ON p.sku_id = ps.sku_id WHERE product_id IN ({})
                '''.format(', '.join(['?']*len(product_ids_values)))
                categories = db.execute(category_query, product_ids_values).fetchall()
                category_mapping = {row[0]: row[1] for row in categories}

                # Update shipment with category_id
                for product_id in product_ids_values:
                    update_shipment_query = 'UPDATE shipment SET category_id = ? WHERE shipment_id = ?'
                    db.execute(update_shipment_query, (category_mapping[product_id], shipment_id))

                db.commit()
                flash('出倉成功')
                logging.info(f"Total DB operations time: {time.time() - db_start_time:.2f} seconds.")
                return redirect(url_for('overview.scan_out.scan_out'))

            except Exception as e:
                logging.error(f"SQL Error: {e}")
                db.rollback()

    if customers is None:
        db = get_db()
        fetch_start_time = time.time()  # Customer fetch start timestamp
        customers = db.execute('SELECT customer_id, customer_name FROM customer').fetchall()
        logging.info(f"Time taken to fetch customers: {time.time() - fetch_start_time:.2f} seconds.")    

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
