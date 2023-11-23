from flask import Blueprint, render_template, request, url_for, flash, redirect
from rma.auth import login_required
from rma.db import get_db
from . import serialize_datetime
import json
import logging

bp_scan_in = Blueprint('scan_in', __name__, url_prefix='/shipment/scan_in')

@bp_scan_in.route('/shipment_update/<int:shipment_id>', methods=('GET', 'POST'))
@login_required
def shipment_update(shipment_id):
    db = get_db()
    shipment = db.execute('SELECT * FROM shipment WHERE shipment_id = ?', (shipment_id,)).fetchone()

    if shipment is None:
        flash('Shipment not found')
        return redirect(url_for('overview.shipment.scan_in'))

    if request.method == 'POST':
        new_shipment_id = request.form['shipment_id']
        customer_id = request.form['customer_id']
        note = request.form['note']

        error = None

        # 做一些有效性檢查，比如 shipment_id 和 customer_id 是否有效
        if not new_shipment_id or not customer_id:
            error = 'Invalid input'

        if error is not None:
            flash(error)
        else:
            db.execute(
            '''
                UPDATE shipment SET shipment_id = ?, customer_id = ?, note = ?
                WHERE shipment_id = ?
            ''',
            (new_shipment_id, customer_id, note, shipment_id)
            )
            db.commit()
            return redirect(url_for('overview.shipment.scan_in'))
        
    return render_template('shipment/update.html', shipment=shipment)
