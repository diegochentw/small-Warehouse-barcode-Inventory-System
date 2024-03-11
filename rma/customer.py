from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify, current_app
from rma.auth import login_required
from rma.db import get_db
from . import serialize_datetime
import os

from datetime import datetime, timedelta
import json
from flask_cors import cross_origin # just for DataTables prevent Cors problem

import pandas as pd
from flask import send_file

bp_customer = Blueprint('customer', __name__, url_prefix='/customers')

# @audit-ok 列表
@bp_customer.route('/')
@login_required
def customers():
    db = get_db()
    customers = db.execute(
        'SELECT c.customer_id, c.customer_name, c.contact, c.type, c.phone, c.email, c.address, c.created_date, c.notes '
        ' FROM customer c'
        ' ORDER BY created_date DESC'
    ).fetchall()

    json_results = []
    for customer in customers:
        customer_dict = {
            'customer_id': customer['customer_id'],
            'customer_name': customer['customer_name'],
            'type': customer['type'],
            'contact': customer['contact'],
            'phone': customer['phone'],
            'email': customer['email'],
            'address': customer['address'],
            'created_date': serialize_datetime(customer['created_date']),
            'notes': customer['notes'],
        }
        json_results.append(customer_dict)

    with open('rma/json/customers.json', 'w') as json_file:
         json.dump(json_results, json_file, default=serialize_datetime)

    return render_template('customer/index.html', customers = customers )

# @audit-ok 新增客戶
@bp_customer.route('/customer_create', methods=('GET', 'POST'))
@login_required
def customer_create():

    if  request.method == 'POST':
        customer_name = request.form['customer_name']
        contact = request.form['contact']
        type = request.form['type']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        notes = request.form['notes']

        error = None

        if not type:
            error = '客戶類型為必填.'

        if error is not None:
            flash(error)    
        else:
            db = get_db()    
            db.execute(
                'INSERT INTO customer (customer_name, contact, type, phone, email, address, notes )'
                ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                (customer_name, contact, type, phone, email, address, notes )
            )
            db.commit()
            return redirect(url_for('overview.customer.customers'))
        
    return render_template('customer/create.html', customers = customers )   

def get_customer(customer_id):
    db = get_db()
    customer = db.execute(
        'SELECT c.customer_id, c.customer_name, c.contact, c.type, c.phone, c.email, c.address, c.created_date, c.notes '
        ' FROM customer c'
        ' WHERE c.customer_id = ?',
        (customer_id, )
    ).fetchone()

    return customer

# @audit-ok 更新客戶
# 沒有帶到customer_name

@bp_customer.route('/customer_update/<int:customer_id>', methods=('GET', 'POST'))
@login_required
def customer_update(customer_id):
    db = get_db()
    customer = db.execute('SELECT * FROM customer WHERE customer_id = ?', (customer_id,)).fetchone()
    
    if customer is None:
        # Handle the case where the customer is not found
        flash("Customer not found.")
        return redirect(url_for('overview.customer.customers'))

    if  request.method == 'POST':
        customer_id = request.form['customer_id']
        customer_name = request.form['customer_name']
        contact = request.form['contact']
        type = request.form['type']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        notes = request.form['notes']

        error = None

        if not type:
            error = '客戶類型為必填.'

        if error is not None:
            flash(error)    
        else:
            db = get_db()    
            db.execute(
                'UPDATE customer SET customer_name = ?, contact = ?, type = ?, phone = ?, email = ?, address = ?, notes = ?'
                ' WHERE customer_id = ?',(customer_name, contact, type, phone, email, address, notes, customer_id )
            )
            db.commit()
            return redirect(url_for('overview.customer.customers'))
    return render_template('customer/update.html', customer_id=customer_id, customer=customer)

# @audit-ok 刪除

@bp_customer.route('/customer_delete/<int:customer_id>', methods=('GET', 'POST'))    
@login_required
def customer_delete(customer_id):
    if  request.method == 'POST':
        customer_id = request.form['customer_id']

        db = get_db()
        db.execute('DELETE FROM customer WHERE customer_id = ?', (customer_id, ))
        db.commit()
        return redirect(url_for('overview.customer.customers'))
    
# @audit 客戶出貨紀錄
def get_filtered_shipments(customer_id, start_date, end_date):
    db = get_db()
    sql_query = '''
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
        AND s.customer_id = ?
        AND s.created_date BETWEEN ? AND ?
        ORDER BY s.created_date DESC
    '''
    return db.execute(sql_query, (customer_id, start_date, end_date)).fetchall()

@bp_customer.route('/filter_shipments', methods=['GET', 'POST'])
@login_required
def filter_shipments():
    customers = get_db().execute('SELECT customer_id, customer_name FROM customer').fetchall()    
    shipments_out = []
    
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        shipments_out = get_filtered_shipments(customer_id, start_date, end_date)
        
    return render_template('customer/filtered_shipments.html', customers=customers, shipments_out=shipments_out)

@bp_customer.route('/export_shipments_to_excel', methods=['GET', 'POST'])
@login_required
def export_shipments_to_excel():
    customer_id = request.form.get('customer_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    # 建立數據庫連接
    db = get_db()
    customers = get_db().execute('SELECT customer_id, customer_name FROM customer').fetchall()
    customer_id = request.args.get('customer_id') if request.method == 'GET' else request.form.get('customer_id')
    # 直接執行SQL查詢
    sql_query = '''
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
    AND s.customer_id = ?
    AND s.created_date BETWEEN ? AND ?

    ORDER BY s.created_date DESC
    '''
    # 執行查詢，並將結果存儲在`shipments_out`中
    shipments_out = db.execute(sql_query, (customer_id, start_date, end_date)).fetchall()

    print("查詢結果的前五條記錄如下：")
    for record in shipments_out[:5]:
        print(record)

    if shipments_out:
        print("查詢結果不為空，共有 {} 條記錄。".format(len(shipments_out)))

    else:
        print("customer_id:",customer_id, start_date, end_date)
        print("查詢結果為空。")

    # 接下來的代碼與原本處理DataFrame和導出Excel文件的邏輯保持不變

    # 將查詢結果轉換為DataFrame，使用columns參數確保列名被設置
    # columns = ['Shipment ID', 'Type', 'Shipment Date', 'Note', 'Customer Name', 'Contact', 
    #               'Customer Type', 'Phone', 'Email', 'Address', 'Customer Notes', 'Product ID', 
    #               'Category Name', 'EAN Code', 'UPC Code', 'Model Name', 'Product Name', 
    #               'Product SKU Created Date', 'SKU ID', 'ERP No', 'Product SN', 
    #               'Manufacturing Date', 'Creator']
    columns = ['Shipment Date', 'Customer Name', 'Category Name', 'Model Name', 'Product Name', 'Product SN' 
               
                  ]

    selected_columns_data = [(shipment['shipment_date'], shipment['customer_name'], shipment['category_name'], 
                          shipment['model_name'], shipment['product_name'], shipment['product_sn']) 
                         for shipment in shipments_out]

    # df = pd.DataFrame(shipments_out, columns=columns)
    df = pd.DataFrame(selected_columns_data, columns=['Shipment Date', 'Customer Name', 'Category Name', 'Model Name', 'Product Name', 'Product SN'])


    # 使用Flask的current_app來獲取應用的實例路徑
    instance_path = current_app.instance_path
    
    # 構造Excel文件的完整路徑
    excel_path = os.path.join(instance_path, 'exports', 'shipments_out.xlsx')

    # 確保導出目錄存在
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    
    # 使用openpyxl引擎將DataFrame導出到Excel
    df.to_excel(excel_path, index=False, engine='openpyxl')
    
    # 返回文件供用戶下載
    return send_file(excel_path, as_attachment=True, download_name='shipments_out.xlsx')
