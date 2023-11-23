from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify
from rma.auth import login_required
from rma.db import get_db
from rma.customer import bp_customer
from . import serialize_datetime
from datetime import datetime, timedelta
import json
from flask_cors import cross_origin # just for DataTables prevent Cors problem
import logging

bp_rma = Blueprint('rma', __name__, url_prefix='/rma')

# @audit-info 列表

@bp_rma.route('/')
@login_required
def rma():
    db = get_db()
    rma = db.execute('''
        SELECT 
            r.rma_id, r.customer_id, r.status_id, r.request_date, r.resolution_date, r.notes,
            c.customer_name, c.contact, c.type, c.phone, c.email, c.address, c.created_date, c.notes AS customer_notes,
            p.product_id, ps.product_name, ps.model_name, p.product_sn, p.erp_no, ps.ean_code, ps.upc_code, p.created_date AS product_created_date,
            rp.return_reason, rp.issue_category, rp.handling_method, rp.status AS rma_status 
        FROM rma r
        JOIN customer c ON r.customer_id = c.customer_id
        JOIN rma_product rp ON r.rma_id = rp.rma_id
        JOIN product p ON rp.product_id = p.product_id
        JOIN product_sku ps ON p.sku_id = ps.sku_id
        ORDER BY r.request_date DESC
    ''').fetchall()

    json_results = []
    for rma in rma:
        rma_dict = {
            'rma_id': rma['rma_id'],
            'request_date': serialize_datetime(rma['request_date']),            
            'customer_name': rma['customer_name'],
            'product_name': rma['product_name'],            
            'product_sn': rma['product_sn'],
            'return_reason': rma['return_reason'],
            'issue_category': rma['issue_category'],
            'handling_method': rma['handling_method'],
            'status': rma['rma_status']
        }
        json_results.append(rma_dict)

    with open('rma/json/rma.json', 'w') as json_file:
         json.dump(json_results, json_file, default=serialize_datetime)

    return render_template('rma/index.html', rma = rma )


# @audit-ok 新增 bug:使用者必須選擇處理方式，否則出現 error 400錯誤

@bp_rma.route('/rma_create', methods=['GET', 'POST'])
@login_required
def rma_create():
    db = get_db()
    customers = db.execute('SELECT customer_id, customer_name FROM customer').fetchall()

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product_sn = request.form['product_sn']
        return_reason = request.form['return_reason']
        issue_category = request.form['issue_category']
        handling_method = request.form.get('handling_method', '')
        status = request.form['status']
        error = None

        if not product_sn:
            error = 'Product serial number is required.'
            flash(error)

        if error is None:
            product = db.execute(
                'SELECT product_id FROM product WHERE product_sn = ?',
                (product_sn,)
            ).fetchone()

            if product is None:
                error = 'No product found with the given serial number.'
                flash(error)

        if error is None:
            db.execute(
                'INSERT INTO rma (customer_id) VALUES (?)',
                (customer_id,)
            )
            rma_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            db.execute(
                'INSERT INTO rma_product (rma_id, product_id, return_reason, issue_category, handling_method, status) VALUES (?, ?, ?, ?, ?, ?)',
                (rma_id, product['product_id'], return_reason, issue_category, handling_method, status)
            )
            db.commit()
            flash('RMA request has been successfully submitted.')
            return redirect(url_for('overview.rma.rma_create'))

        if error:
            return redirect(url_for('overview.rma.rma_create'))

    return render_template('rma/create.html', customers=customers)

# @audit-info 更新
@bp_rma.route('/rma_update/<int:rma_id>', methods=('GET', 'POST'))
@login_required
def rma_update(rma_id):
    db = get_db()
    rma = db.execute(
        '''        
        SELECT r.*, c.*, rp.issue_category, rp.handling_method, p.product_sn, rp.return_reason, rp.status
        FROM rma r
        JOIN customer c ON c.customer_id = r.customer_id
        JOIN rma_product rp ON rp.rma_id = r.rma_id
        JOIN product p ON p.product_id = rp.product_id
        WHERE r.rma_id = ?
        ''',        
        (rma_id,)
    ).fetchone()

    if rma is None:
        flash("RMA not found.")
        return redirect(url_for('overview.rma.rma'))
    
    if request.method == 'POST':
        return_reason = request.form['return_reason']
        issue_category = request.form['issue_category']
        handling_method = request.form['handling_method']
        status = request.form['status']

        db.execute(
        'UPDATE rma_product SET return_reason = ?, issue_category = ?, handling_method = ? , status = ? WHERE rma_id = ?',
        (return_reason, issue_category, handling_method, status, rma_id)
          )

        db.commit()
        flash('RMA已成功更新')
        return redirect(url_for('overview.rma.rma'))
        
    return render_template('rma/update.html', rma = rma)

# @audit-info 刪除
@bp_rma.route('/rma_delete/<int:rma_id>', methods=('POST',))
@login_required
def rma_delete(rma_id):
    db = get_db()
    db.execute('DELETE FROM rma WHERE rma_id = ?', (rma_id, ))
    db.commit()
    return redirect(url_for('overview.rma.rma'))


    