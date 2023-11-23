from flask import Blueprint, jsonify
from flask_cors import cross_origin # just for DataTables prevent Cors problem
import json
from rma.db import get_db

bp_json = Blueprint('json', __name__, url_prefix='/json')   

def load_json_data(file_path):
    try:
        with open(file_path, 'r') as json_file:
            return jsonify(json.load(json_file))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return jsonify({"error": str(e)}), 500

@bp_json.route('/overview_products', methods=['GET'])
@cross_origin()
def overview_products():
    return load_json_data('rma/json/overview_products.json')

@bp_json.route('/overview_customers', methods=['GET'])
@cross_origin()
def get_customer_data_overview():
    return load_json_data('rma/json/overview_customers.json')

@bp_json.route('/overview_shipments', methods=['GET'])
@cross_origin()
def get_shipment_data_overview():
    return load_json_data('rma/json/overview_shipments.json')

@bp_json.route('/product', methods=['GET'])
@cross_origin() 
def get_product_data():
    return load_json_data('rma/json/products.json')

@bp_json.route('/amount', methods=['GET'])
@cross_origin() 
def get_product_amount():
    return load_json_data('rma/json/amount.json')

@bp_json.route('/product_sku', methods=['GET'])
@cross_origin() 
def get_product_sku():
    return load_json_data('rma/json/product_skus.json')

@bp_json.route('/customer', methods=['GET'])
@cross_origin() 
def get_customer_data():
    return load_json_data('rma/json/customers.json')

@bp_json.route('/shipment_in', methods=['GET'])
@cross_origin() 
def get_shipment_data():
    return load_json_data('rma/json/shipments_in.json')

@bp_json.route('/shipment_out', methods=['GET'])
@cross_origin() 
def get_shipment_out_data():
    return load_json_data('rma/json/shipments_out.json')

@bp_json.route('/rma', methods=['GET'])
@cross_origin() 
def get_rma():
    return load_json_data('rma/json/rma.json')

@bp_json.route('/search_sku_stock', methods=['GET'])
@cross_origin() 
def get_product_search_sku_stock():
    return load_json_data('rma/json/product_search_sku_stock.json')





@bp_json.route('/json/product/<product_sn>', methods=['GET'])
def get_product_info(product_sn):
    db = get_db()
    cur = db.cursor()  # Get a cursor object from the connection
    cur.execute("SELECT * FROM product WHERE product_sn = ?", (product_sn,))
    product = cur.fetchone()

    if product:
        # Convert the sqlite3.Row object to a dictionary
        product_dict = {col[0]: product[idx] for idx, col in enumerate(cur.description)}
        return jsonify(product_dict)
    else:
        return jsonify({"error": "Product not found"}), 404

