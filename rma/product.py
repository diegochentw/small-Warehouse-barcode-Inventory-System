from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify, session
from rma.auth import login_required
from rma.db import get_db
from . import serialize_datetime
from datetime import datetime, timedelta
import json
from flask_cors import cross_origin # just for DataTables prevent Cors problem
import logging
logging.basicConfig(level=logging.DEBUG)
import sqlite3

bp_product = Blueprint('product', __name__, url_prefix='/products')

@bp_product.route('/')
@login_required
def products():
    db = get_db()
    products = db.execute('''
        SELECT p.product_id, ps.category_id, ps.product_name, ps.model_name, p.product_sn, p.erp_no, ps.ean_code, ps.upc_code, p.created_date, cg.category_name, p.manufacturing_date
        FROM product p
        LEFT JOIN product_sku ps ON p.sku_id = ps.sku_id
        LEFT JOIN category cg ON ps.category_id = cg.category_id
        ORDER BY p.created_date DESC
    ''').fetchall()

    json_results = []       
    for product in products:
        product_dict = {
            'product_id': product['product_id'],
            'category_id': product['category_id'],
            'product_name': product['product_name'],
            'model_name': product['model_name'],
            'product_sn': product['product_sn'],
            'erp_no': product['erp_no'],
            'ean_code': product['ean_code'],
            'upc_code': product['upc_code'],
            'manufacturing_date': serialize_datetime(product['manufacturing_date']),
            'created_date': serialize_datetime(product['created_date']),  
            'category_name': product['category_name']
        }
        json_results.append(product_dict)
    try:
        with open('rma/json/products.json', 'w') as json_file:
            json.dump(json_results, json_file, default=serialize_datetime)
    except Exception as e:
        print(f"An error occurred: {e}")

    return render_template('product/index.html', products = products)


# @audit-ok 顯示產品數量
@bp_product.route('/amount')
@login_required
def products_amount():
    db = get_db()
    products = db.execute('''
        SELECT ps.sku_id, ps.category_id, ps.product_name, ps.model_name, p.product_id, p.product_sn, p.erp_no, p.manufacturing_date, p.created_date,
            ps.ean_code, ps.upc_code, cg.category_name, 
            COUNT(p.product_id) AS product_count
        FROM product_sku ps
        LEFT JOIN product p ON p.sku_id = ps.sku_id AND p.product_id IS NOT NULL
        LEFT JOIN category cg ON ps.category_id = cg.category_id
        GROUP BY ps.sku_id, ps.category_id, ps.product_name, ps.model_name, ps.ean_code, ps.upc_code, cg.category_name, p.created_date
        HAVING COUNT(p.product_id) > 0
        ORDER BY ps.created_date DESC

    ''').fetchall()

    json_results = []       
    for product in products:
        product_dict = {
            'product_id': product['product_id'],
            'category_id': product['category_id'],
            'product_name': product['product_name'],
            'model_name': product['model_name'],
            'product_count': product['product_count'],            
            'product_sn': product['product_sn'],
            'erp_no': product['erp_no'],
            'ean_code': product['ean_code'],
            'upc_code': product['upc_code'],
            'manufacturing_date': serialize_datetime(product['manufacturing_date']),
            'created_date': serialize_datetime(product['created_date']),  
            'category_name': product['category_name']
        }
        json_results.append(product_dict)
    try:
        with open('rma/json/amount.json', 'w') as json_file:
            json.dump(json_results, json_file, default=serialize_datetime)
    except Exception as e:
        print(f"An error occurred: {e}")

    return render_template('product/amount.html', products = products)

# @audit-ok 新增SKU

@bp_product.route('/product_create_sku', methods=('GET', 'POST'))
@login_required
def product_create_sku():
    categories = None

    if request.method == 'POST':
        category_id = request.form['category_id']
        product_name = request.form['product_name']
        model_name = request.form['model_name']
        ean_code = request.form['ean_code']
        upc_code = request.form['upc_code']

        error = None

        if not ean_code:
            error = 'EAN Code為必填.'

        if error is not None:
            flash(error)    

        else:
            db = get_db()    
            db.execute(
                'INSERT INTO product_sku (category_id, product_name, model_name, ean_code, upc_code )'
                ' VALUES (?, ?, ?, ?, ?)',
                (category_id, product_name, model_name, ean_code, upc_code)
            )
                            
            db.commit()
            flash('新增商品成功')
            return redirect(url_for('overview.product.product_create_sku'))
        
    if categories is None:
        db = get_db()
        categories = db.execute('SELECT category_id, category_name FROM category').fetchall()

    products_skus = db.execute('''
        SELECT ps.sku_id, ps.category_id, ps.product_name, ps.model_name, ps.ean_code, ps.upc_code, cg.category_name, ps.created_date
        FROM product_sku ps
        JOIN category cg ON ps.category_id = cg.category_id
        ORDER BY ps.created_date DESC
    ''').fetchall()


    json_results = []       
    for product_sku in products_skus:
        product_dict = {
            'sku_id': product_sku['sku_id'],
            'category_id': product_sku['category_id'],
            'category_name': product_sku['category_name'],
            'product_name': product_sku['product_name'],
            'model_name': product_sku['model_name'],
            'ean_code': product_sku['ean_code'],
            'upc_code': product_sku['upc_code'],
            'created_date': serialize_datetime(product_sku['created_date']),
        }
        json_results.append(product_dict)

    with open('rma/json/product_skus.json', 'w') as json_file:
         json.dump(json_results, json_file, default=serialize_datetime)        

    return render_template('product/create_sku.html', categories=categories, products_skus=products_skus)    

# @audit  更新SKU
# 類別資料非動態

@bp_product.route('/product_sku_update/<int:sku_id>', methods=('GET', 'POST'))
@login_required
def product_update_sku(sku_id):
    db = get_db()
    product_sku = db.execute(
        '''
        SELECT ps.sku_id, ps.category_id, ps.product_name, ps.model_name, ps.ean_code, ps.upc_code, cg.category_name, ps.created_date
        FROM product_sku ps
        JOIN category cg ON ps.category_id = cg.category_id
        WHERE ps.sku_id = ?
        ''',
        (sku_id,)
    ).fetchone()

    if product_sku is None:
        flash("找不到該商品代碼，無法更新!")
        return redirect(url_for('overview.product.products_skus'))

    if request.method == 'POST':
        new_category_id = request.form['category_id'].strip()
        product_name = request.form['product_name'].strip()
        model_name = request.form['model_name'].strip()
        ean_code = request.form['ean_code'].strip().upper()
        upc_code = request.form['upc_code'].strip()

        validation_error = None

        if not model_name:
            validation_error = '產品型號為必填'

        duplicate_sku = db.execute(
            'SELECT sku_id FROM product_sku WHERE ean_code = ? AND sku_id != ?',
            (ean_code, sku_id)
        ).fetchone()

        if duplicate_sku:
            validation_error = 'EAN碼必須唯一，該EAN碼已存在於其他商品代碼'

        if validation_error is None:
            try:
                db.execute(
                    'UPDATE product_sku SET category_id = ?, product_name = ?, model_name = ?, ean_code = ?, upc_code = ? WHERE sku_id = ?',
                    (new_category_id, product_name, model_name, ean_code, upc_code, sku_id)
                )
                db.commit()
                return redirect(url_for('overview.product.product_create_sku'))
            except sqlite3.IntegrityError as e:
                flash(str(e))
        else:
            flash(validation_error)

    categories = db.execute('SELECT category_id, category_name FROM category').fetchall()

    return render_template('product/update_sku.html', product_sku=product_sku, categories=categories)

# @audit 刪除SKU
@bp_product.route('/product_sku_delete/<int:sku_id>', methods=('GET', 'POST'))
@login_required
def product_delete_sku(sku_id):
    db = get_db()
    db.execute('DELETE FROM product_sku WHERE sku_id = ?', (sku_id,))
    db.commit()
    return redirect(url_for('overview.product.product_create_sku'))

# @audit-ok 綁定序號-單一

@bp_product.route('/product_create_single', methods=('GET', 'POST'))
@login_required
def product_create_single():
    categories = None

    if request.method == 'POST':
        sku_id = request.form['sku_id']  # 從前端獲取已存在的SKU ID
        product_sn = request.form['product_sn'].strip() #240418 清除前後空白
        erp_no = request.form['erp_no']
        manufacturing_date = request.form['manufacturing_date']

        error = None

        if not product_sn:
            error = '產品序號為必填.'

        if error is not None:
            flash(error)    
        else:
            db = get_db()    
            if manufacturing_date:
                manufacturing_date += " 00:00:00"

            existing_product_sn_query = 'SELECT product_sn FROM product WHERE product_sn = ?'
            existing_product_sn = db.execute(existing_product_sn_query, (product_sn,)).fetchone()

            if existing_product_sn:
                flash(f'產品序號{product_sn}已存在，無法再次新增')
            else:
                db.execute(
                    'INSERT INTO product (sku_id, erp_no, product_sn, manufacturing_date)'
                    ' VALUES (?, ?, ?, ?)',
                    (sku_id, erp_no, product_sn, manufacturing_date)
                )
                                
                db.commit()
                flash(f'序號 {product_sn} 已新增')
                return redirect(url_for('overview.product.products'))
        
    if categories is None:
        db = get_db()
        categories = db.execute('SELECT category_id, category_name FROM category').fetchall()
        
    # 取得所有可用的SKU ID以供選擇
    skus = db.execute('SELECT sku_id, product_name FROM product_sku').fetchall()

    return render_template('product/create_single.html', categories=categories, skus=skus)

# @audit-ok 批次增加產品 - 序號範圍
@bp_product.route('/product_create_batch_scope', methods=('GET', 'POST'))
@login_required
def product_create_batch_scope():
    categories = None

    if request.method == 'POST':
        sku_id = request.form['sku_id']  # 從前端獲取已存在的SKU ID        
        product_sn_prefix = request.form['product_sn_prefix']
        product_sn_range_start = int(request.form['product_sn_range_start'])
        product_sn_range_end = int(request.form['product_sn_range_end'])   
        erp_no = request.form['erp_no']             
        manufacturing_date = request.form['manufacturing_date']

        # 讀取使用者輸入的序號位數
        sn_digit_length = int(request.form['sn_digit_length'])

        error = None

        def is_valid_sn_prefix(prefix):
            """
            檢查前綴是否為字母或數字或包含斜線
            """
            for char in prefix:
                if not (char.isalnum() or char == '/' or char == '\\'):
                    return False
            return True

        if product_sn_range_start > product_sn_range_end:
            error = '序號範圍的結束值必須大於或等於序號範圍的起始值'
        elif not product_sn_prefix or product_sn_range_start <= 0 or product_sn_range_end <= 0:
            error = '請填寫完整前綴和序號範圍'
        #elif not product_sn_prefix.isalnum():
        elif not is_valid_sn_prefix(product_sn_prefix):
            error = '前綴僅允許字母/數字/斜線及反斜線'
            flash(error)

        if error is not None:
            flash(error)    
            
        else:
            if manufacturing_date:
                manufacturing_date += " 00:00:00"
            else:
                manufacturing_date = None

            db = get_db()

            for i in range(product_sn_range_start, product_sn_range_end + 1):
                # product_sn = f'{product_sn_prefix}{i:04d}'  # 根據序號範圍生成帶有前綴的產品序號
                product_sn = f'{product_sn_prefix}{i:0{sn_digit_length}d}'  # 使用使用者指定的序號位數來生成帶有前綴的產品序號

                try:
                    db.execute(
                        'INSERT INTO product (sku_id, erp_no, product_sn, manufacturing_date )'
                        ' VALUES (?, ?, ?, ?)',
                        (sku_id, erp_no, product_sn, manufacturing_date)
                    )
                except sqlite3.IntegrityError:
                    flash(f'產品序號 {product_sn} 已存在')
                    continue

            db.commit()
            flash(f'作業已完成')            
            return redirect(url_for('overview.product.products'))
        
    if categories is None:
        db = get_db()
        categories = db.execute('SELECT category_id, category_name FROM category').fetchall()

    skus = db.execute('SELECT sku_id, product_name FROM product_sku').fetchall()

    return render_template('product/create_batch_scope.html', categories=categories, skus=skus)   


# @audit-ok 更新產品 product_update
@bp_product.route('/product_update/<int:product_id>', methods=('GET', 'POST'))
@login_required
def product_updates(product_id):
    db = get_db()
    product = db.execute('''
        SELECT p.*, c.*, ps.*
        FROM product p 
        JOIN product_sku ps ON p.sku_id = ps.sku_id
        JOIN category c ON ps.category_id = c.category_id                
        WHERE p.product_id = ?
    ''', (product_id,)).fetchone()

    if product is None:
        # Handle the case where the product is not found
        session.pop('_flashes', None)
        flash("找不到該產品，無法更新!")
        return redirect(url_for('overview.product.products'))
    
    if  request.method == 'POST':
        product_id = request.form['product_id']
        erp_no = request.form['erp_no']
        product_sn = request.form['product_sn']
        manufacturing_date = request.form['manufacturing_date']

        manufacturing_date = request.form['manufacturing_date']
        # 將 "T" 替換為一個空格 " "
        manufacturing_date = manufacturing_date.replace("T", " ")
        # 將分和秒添加到日期時間字符串中
        manufacturing_date += ":00"

        error = None

        if not product_sn:
            error = '產品序號為必填.'

        if error is not None:
            flash(error)    
        else:
            db = get_db()
            db.execute(
                'UPDATE product SET erp_no = ?, product_sn = ?, manufacturing_date = ? WHERE product_id = ?',
                (erp_no, product_sn, manufacturing_date, product_id)
            )    
            db.commit()
            return redirect(url_for('overview.product.products'))
        
    return render_template('product/update.html', product = product)     

# @audit-ok 刪除產品
@bp_product.route('/product_delete/<int:product_id>', methods=('GET', 'POST'))    
@login_required
def product_delete(product_id):
    if  request.method == 'POST':
        product_id = request.form['product_id']

        db = get_db()
        db.execute('DELETE FROM product WHERE product_id = ?', (product_id, ))
        db.commit()
        return redirect(url_for('overview.product.products'))
    
# @audit-info 查詢即時庫存
@bp_product.route('/product_search_sku_stock', methods=('GET', 'POST'))
@login_required
def product_search_sku_stock():
    db = get_db()
    sku_stock = db.execute('''
        SELECT
            ps.model_name,
            SUM(CASE WHEN s.type = '進倉' THEN 1 ELSE 0 END) AS scan_in,
            SUM(CASE WHEN s.type = '出倉' THEN 1 ELSE 0 END) AS scan_out,
            SUM(CASE WHEN s.type = '進倉' THEN 1 ELSE 0 END) - 
            SUM(CASE WHEN s.type = '出倉' THEN 1 ELSE 0 END) AS stock,
            ps.product_name	
                           
            FROM shipment_product sp
            JOIN shipment s ON sp.shipment_id = s.shipment_id
            JOIN product p ON sp.product_id = p.product_id
            JOIN product_sku ps ON p.sku_id = ps.sku_id
            GROUP BY ps.model_name;
                                                      
   ''').fetchall()
    
    json_result = []
    for sku_stock in sku_stock:
        json_result.append({
            'product_name': sku_stock['product_name'],
            'model_name': sku_stock['model_name'],
            # 'serial_number': sku_stock['serial_number'], #產品序號
            'scan_in': sku_stock['scan_in'],
            'scan_out': sku_stock['scan_out'],
            'stock': sku_stock['stock'],
       
        })

    try:
        with open('rma/json/product_search_sku_stock.json', 'w', encoding='utf-8') as f:
            json.dump(json_result, f, indent=4)

    except Exception as e:
        print(f"Error: {e}")

    return render_template('product/search_sku_stock.html')

# @audit-info 查詢尚未出庫庫存的產品序號

@bp_product.route('/product_not_shipped/<model_name>', methods=['GET'])
@login_required
def product_not_shipped(model_name):
    db = get_db()

    product_sn = db.execute('''
        SELECT p.product_sn
        FROM product p
        JOIN product_sku ps ON p.sku_id = ps.sku_id
        WHERE ps.model_name = ?
          AND (
              SELECT COUNT(*) 
              FROM shipment_product sp
              JOIN shipment s ON sp.shipment_id = s.shipment_id
              WHERE sp.product_id = p.product_id AND s.type = '進倉'
          ) > (
              SELECT COUNT(*)
              FROM shipment_product sp
              JOIN shipment s ON sp.shipment_id = s.shipment_id
              WHERE sp.product_id = p.product_id AND s.type = '出倉'
          )
    ''', (model_name,)).fetchall()

    # 舊的查詢，無法顯示二次進貨的產品序號
    # product_sn = db.execute('''
    #     SELECT p.product_sn
    #     FROM product p
    #     JOIN product_sku ps ON p.sku_id = ps.sku_id
    #     WHERE ps.model_name = ?
    #       AND p.product_id NOT IN (
    #           SELECT sp.product_id 
    #           FROM shipment_product sp
    #           JOIN shipment s ON sp.shipment_id = s.shipment_id
    #           WHERE s.type = '出倉'
    #       )
    #       AND p.product_id IN (
    #           SELECT sp.product_id
    #           FROM shipment_product sp
    #           JOIN shipment s ON sp.shipment_id = s.shipment_id
    #           WHERE s.type = '進倉'
    #       )
    # ''', (model_name,)).fetchall()

    serial_numbers = [sn['product_sn'] for sn in product_sn]
    return jsonify(serial_numbers if serial_numbers else ["無未出庫產品"])
