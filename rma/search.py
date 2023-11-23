from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify
from rma.db import get_db
from datetime import datetime, timedelta
from rma.auth import login_required

bp_search = Blueprint('search', __name__, url_prefix='/search')

@bp_search.route('/', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        product_sn = request.form.get('product_sn')
        return search_database(product_sn)
    return render_template('search/index.html')

def add_hours_to_datetime(datetime_obj, hours):
    """Add hours to a datetime object."""
    if datetime_obj:
        return datetime_obj + timedelta(hours=hours)
    return None

def search_database(product_sn):

    db = get_db()
    cursor = db.cursor()
 
    # Include created_date in your SQL queries
    # Search for product info
    cursor.execute("""
        SELECT *, p.created_date
        FROM product p
        JOIN product_sku ps ON p.sku_id = ps.sku_id
        WHERE p.product_sn = ?
    """, (product_sn,))
    product_info = cursor.fetchall()

    if product_info:
        manufacturing_date = product_info[0]['manufacturing_date']

    else:
        manufacturing_date = None

    # Search for RMA records
    cursor.execute("""
        SELECT *, request_date
        FROM rma_product
        INNER JOIN rma ON rma_product.rma_id = rma.rma_id
        WHERE product_id IN (
            SELECT product_id FROM product WHERE product_sn = ?
        )
    """, (product_sn,))
    rma_info = cursor.fetchall()

    # Search for Shipment records
    cursor.execute("""
        SELECT shipment.*, customer.customer_name, shipment.created_date
        FROM shipment_product
        INNER JOIN shipment ON shipment_product.shipment_id = shipment.shipment_id
        INNER JOIN customer ON shipment.customer_id = customer.customer_id
        WHERE product_id IN (
            SELECT product_id FROM product WHERE product_sn = ?
        )
    """, (product_sn,))
    shipment_info = cursor.fetchall()

    # Search for Customer records
    cursor.execute("""
        SELECT *, created_date
        FROM customer
        INNER JOIN rma ON customer.customer_id = rma.customer_id
        WHERE rma_id IN (
            SELECT rma_id FROM rma_product WHERE product_id IN (
                SELECT product_id FROM product WHERE product_sn = ?
            )
        )
    """, (product_sn,))
    customer_info = cursor.fetchall()
 
    all_records = []

    # 加入產品信息
    for record in product_info:
        adjusted_date = add_hours_to_datetime(record['created_date'], 8)
        all_records.append({'type': 'Product', 'date': adjusted_date, 'details': record})

    # 加入RMA信息
    for record in rma_info:
        adjusted_date = add_hours_to_datetime(record['request_date'], 8)
        all_records.append({'type': 'RMA', 'date': adjusted_date, 'details': record})

    # 加入出貨信息
    for record in shipment_info:
        adjusted_date = add_hours_to_datetime(record['created_date'], 8)
        all_records.append({'type': 'Shipment', 'date': adjusted_date, 'details': record})


    # 根據日期排序
    current_time = datetime.now()

    manufacturing_duration = None

    if manufacturing_date is not None:
        manufacturing_duration = current_time - manufacturing_date
        delta = current_time - manufacturing_date
        days = delta.days
        years = days // 365
        remaining_days = days % 365
    else:
        years = None
        remaining_days = None

    all_records.sort(key=lambda x: x['date'], reverse=False)
    
    return render_template('search/timeline.html', records=all_records, manufacturing_duration=manufacturing_duration, remaining_days = remaining_days, years = years, product_sn=product_sn)

