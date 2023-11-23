from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify
from rma.auth import login_required
from rma.db import get_db
from . import serialize_datetime

from datetime import datetime, timedelta
import json
from flask_cors import cross_origin # just for DataTables prevent Cors problem

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
            # return redirect(url_for('overview.customer_details', customer_id=customer_id))


  # return redirect(url_for('overview.customer.customers', customer_id=customer_id))
  # return render_template('customer/update.html', customers_id = customer_id, customer = customer)   
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