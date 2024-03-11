from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify
from rma.auth import login_required
from rma.db import get_db
from . import serialize_datetime
from datetime import datetime, timedelta
import json
from flask_cors import cross_origin # just for DataTables prevent Cors problem
import logging

from rma.customer import bp_customer
from rma.jsonRoute import bp_json
from rma.rma import bp_rma
from rma.product import bp_product
from rma.scan_in_bundle import bp_scan_in
from rma.scan_out_bundle import bp_scan_out
from rma.search import bp_search

bp = Blueprint('overview', __name__)
bp.register_blueprint(bp_customer)
bp.register_blueprint(bp_json)
bp.register_blueprint(bp_rma)
bp.register_blueprint(bp_product)
bp.register_blueprint(bp_scan_in)
bp.register_blueprint(bp_scan_out)
bp.register_blueprint(bp_search)

@bp.route('/')
@login_required

# @audit-ok 產品

def index():
    db = get_db()
    products = db.execute('''
        SELECT ps.category_id, ps.product_name, ps.model_name, p.product_sn, p.erp_no, ps.ean_code, ps.upc_code, p.created_date, cg.category_name 
        FROM product p 
        JOIN category cg ON ps.category_id = cg.category_id 
        JOIN product_sku ps ON p.sku_id = ps.sku_id 
        ORDER BY p.created_date DESC LIMIT 10
    ''').fetchall()

    json_results = []
    for product in products:
        product_dict = {
            'category_id': product['category_id'],
            'product_name': product['product_name'],
            'model_name': product['model_name'],
            'product_sn': product['product_sn'],
            'erp_no': product['erp_no'],
            'ean_code': product['ean_code'],
            'upc_code': product['upc_code'],
            'created_date': serialize_datetime(product['created_date']),
            'category_name': product['category_name']
        }
        json_results.append(product_dict)

    with open('rma/json/overview_products.json', 'w') as json_file:
        json.dump(json_results, json_file, default=serialize_datetime)

# @audit-ok 客戶

    db = get_db()
    customers = db.execute(
        'SELECT c.customer_id, c.customer_name, c.contact, c.type, c.phone, c.email, c.address, c.created_date, c.notes '
        ' FROM customer c'
        ' ORDER BY created_date DESC LIMIT 10'
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

    with open('rma/json/overview_customers.json', 'w') as json_file:
        json.dump(json_results, json_file, default=serialize_datetime)

# @audit-ok 進出貨紀錄

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
        ORDER BY shipment_date DESC LIMIT 10
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

    with open('rma/json/overview_shipments.json', 'w') as json_file:
        json.dump(json_results, json_file, default=serialize_datetime)

    return render_template('overviews.html', products = products, customers = customers, shipments = shipments)      

