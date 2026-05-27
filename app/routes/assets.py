from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from app import db
from app.models.asset import Asset
from app.models.employee import Employee
from app.models.assignment import Assignment
from app.models.audit_log import AuditLog
from datetime import datetime
import html

bp = Blueprint('assets', __name__, url_prefix='/assets')

@bp.route('/list')
def list():
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    
    query = Asset.query
    
    if search_query:
        query = query.filter(
            (Asset.name.ilike(f'%{search_query}%')) |
            (Asset.serial_number.ilike(f'%{search_query}%')) |
            (Asset.category.ilike(f'%{search_query}%'))
        )
    
    if category_filter:
        query = query.filter(Asset.category == category_filter)
    
    if status_filter == 'available':
        assigned_ids = db.session.query(Assignment.asset_id).filter(Assignment.returned_date.is_(None)).distinct()
        query = query.filter(~Asset.id.in_(assigned_ids))
    elif status_filter == 'assigned':
        assigned_ids = db.session.query(Assignment.asset_id).filter(Assignment.returned_date.is_(None)).distinct()
        query = query.filter(Asset.id.in_(assigned_ids))
    
    assets = query.order_by(Asset.created_at.desc()).all()
    
    categories = db.session.query(Asset.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('assets_list.html', 
                           assets=assets, 
                           search_query=search_query,
                           category_filter=category_filter,
                           status_filter=status_filter,
                           categories=categories)

@bp.route('/')
def index():
    return redirect(url_for('assets.list'))

@bp.route('/detail/<int:asset_id>')
def detail(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    assignments = Assignment.query.filter_by(asset_id=asset_id).order_by(Assignment.assigned_date.desc()).all()
    return render_template('asset_detail.html', asset=asset, assignments=assignments)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Asset name is required.', 'danger')
            return render_template('asset_form.html')
        serial_number = request.form.get('serial_number')
        category = request.form.get('category')
        purchased_from = request.form.get('purchased_from')
        purchased_date_str = request.form.get('purchased_date')
        
        purchased_date = None
        if purchased_date_str:
            try:
                purchased_date = datetime.strptime(purchased_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid purchase date format.', 'danger')
                return render_template('asset_form.html')
        
        if purchased_date and purchased_date > datetime.now().date():
            flash(f'Not able to add asset in the future date!', 'danger')
            return redirect(url_for('assets.add'))
        
        existing = Asset.query.filter_by(serial_number=serial_number).first()
        if existing:
            flash(f'Asset with Serial Number "{serial_number}" already exists! Please use a different serial number.', 'danger')
            return redirect(url_for('assets.list'))
        
        if len(name) > 100:
            flash('Asset name must be 100 characters or less.', 'danger')
            return render_template('asset_form.html')
        if len(serial_number) > 100:
            flash('Serial number must be 100 characters or less.', 'danger')
            return render_template('asset_form.html')
        if len(category) > 50:
            flash('Category must be 50 characters or less.', 'danger')
            return render_template('asset_form.html')
        if purchased_from and len(purchased_from) > 50:
            flash('Purchased from must be 50 characters or less.', 'danger')
            return render_template('asset_form.html')
        
        asset = Asset(
            name=name,
            serial_number=serial_number,
            category=category,
            purchased_from=purchased_from,
            purchased_date=purchased_date
        )
        db.session.add(asset)
        db.session.commit()
        
        AuditLog.log('CREATE', 'assets', asset.id, 
                    new_value={'name': name, 'serial_number': serial_number, 'category': category},
                    user_id=current_user.id)
        
        flash(f'Asset "{name}" added successfully!', 'success')
        return redirect(url_for('assets.list'))
    
    return render_template('asset_form.html')

@bp.route('/edit/<int:asset_id>', methods=['GET', 'POST'])
@login_required
def edit(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    
    if request.method == 'POST':
        old_values = {'name': asset.name, 'serial_number': asset.serial_number, 
                      'category': asset.category, 'purchased_from': asset.purchased_from}
        
        name = request.form.get('name', '').strip()
        if not name:
            flash('Asset name is required.', 'danger')
            return render_template('asset_form.html', asset=asset)
        serial_number = request.form.get('serial_number')
        category = request.form.get('category')
        purchased_from = request.form.get('purchased_from')
        
        if len(name) > 100:
            flash('Asset name must be 100 characters or less.', 'danger')
            return render_template('asset_form.html', asset=asset)
        if len(serial_number) > 100:
            flash('Serial number must be 100 characters or less.', 'danger')
            return render_template('asset_form.html', asset=asset)
        if len(category) > 50:
            flash('Category must be 50 characters or less.', 'danger')
            return render_template('asset_form.html', asset=asset)
        if purchased_from and len(purchased_from) > 50:
            flash('Purchased from must be 50 characters or less.', 'danger')
            return render_template('asset_form.html', asset=asset)
        
        asset.name = name
        asset.serial_number = serial_number
        asset.category = category
        asset.purchased_from = purchased_from
        purchased_date_str = request.form.get('purchased_date')
        if purchased_date_str:
            try:
                new_purchased_date = datetime.strptime(purchased_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid purchase date format.', 'danger')
                return render_template('asset_form.html', asset=asset)
            if new_purchased_date > datetime.now().date():
                flash(f'Not able to add asset in the future date!', 'danger')
                return redirect(url_for('assets.edit', asset_id=asset_id))
            asset.purchased_date = new_purchased_date
        
        db.session.commit()
        
        AuditLog.log('UPDATE', 'assets', asset.id, 
                    old_value=old_values,
                    new_value={'name': asset.name, 'serial_number': asset.serial_number},
                    user_id=current_user.id)
        
        flash(f'Asset "{asset.name}" updated successfully!', 'success')
        return redirect(url_for('assets.detail', asset_id=asset.id))
    
    return render_template('asset_form.html', asset=asset)

@bp.route('/delete/<int:asset_id>', methods=['POST'])
@login_required
def delete(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    
    AuditLog.log('DELETE', 'assets', asset_id,
                old_value={'name': asset.name, 'serial_number': asset.serial_number},
                user_id=current_user.id)
    
    Assignment.query.filter_by(asset_id=asset_id).delete()
    db.session.delete(asset)
    db.session.commit()
    
    flash(f'Asset "{asset.name}" deleted successfully!', 'success')
    return redirect(url_for('assets.list'))

@bp.route('/assign/<int:asset_id>', methods=['GET', 'POST'])
@login_required
def assign(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    employees = Employee.query.all()
    
    active_assignment = Assignment.query.filter_by(asset_id=asset_id, returned_date=None).first()
    if active_assignment:
        flash('This asset is already assigned to someone! Please return it first.', 'warning')
        return redirect(url_for('assets.detail', asset_id=asset_id))
    
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        notes = request.form.get('notes')
        
        assigned_date = datetime.now()
        
        assignment = Assignment(
            asset_id=asset_id,
            employee_id=employee_id,
            assigned_date=assigned_date,
            notes=notes
        )
        db.session.add(assignment)
        db.session.commit()
        
        employee = Employee.query.get(employee_id)
        AuditLog.log('ASSIGN', 'assignments', assignment.id,
                    new_value={'asset': asset.name, 'employee': employee.name, 'date': str(assigned_date)},
                    user_id=current_user.id)
        
        flash(f'Asset "{asset.name}" assigned to {employee.name}!', 'success')
        return redirect(url_for('assets.detail', asset_id=asset_id))
    
    return render_template('assign_asset.html', asset=asset, employees=employees, today=datetime.now().strftime('%Y-%m-%d'))

@bp.route('/return/<int:asset_id>', methods=['GET', 'POST'])
@login_required
def return_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    
    assignment = Assignment.query.filter_by(asset_id=asset_id, returned_date=None).first()
    if not assignment:
        flash('This asset is not currently assigned!', 'warning')
        return redirect(url_for('assets.detail', asset_id=asset_id))
    
    if request.method == 'POST':
        return_notes = request.form.get('return_notes')
        returned_date = datetime.now()
        
        if returned_date < assignment.assigned_date:
            flash(f'Return date cannot be before assigned date!', 'danger')
            return redirect(url_for('assets.return_asset', asset_id=asset_id))
        
        assignment.return_notes = return_notes
        assignment.returned_date = returned_date
        db.session.commit()
        
        employee = Employee.query.get(assignment.employee_id)
        AuditLog.log('RETURN', 'assignments', assignment.id,
                    new_value={'asset': asset.name, 'employee': employee.name, 'returned_date': str(returned_date)},
                    user_id=current_user.id)
        
        flash(f'Asset "{asset.name}" returned from {employee.name}!', 'success')
        return redirect(url_for('assets.detail', asset_id=asset_id))
    
    return render_template('return_asset.html', asset=asset, assignment=assignment)

@bp.route('/print/<int:asset_id>')
@login_required
def print_report(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    assignments = Assignment.query.filter_by(asset_id=asset_id).order_by(Assignment.assigned_date.desc()).all()
    
    now_ist = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    safe_name = html.escape(asset.name)
    safe_serial = html.escape(asset.serial_number)
    safe_category = html.escape(asset.category)
    safe_purchased_from = html.escape(asset.purchased_from or 'N/A')
    safe_status = ""
    if asset.assigned_to:
        safe_assigned_name = html.escape(asset.assigned_to.name)
        safe_status = f"<span class='badge badge-warning'>Assigned to {safe_assigned_name}</span>"
    else:
        safe_status = "<span class='badge badge-success'>Available</span>"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Asset Report - {safe_name}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; margin: 40px; background: white; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 12px; font-size: 26px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 12px; font-size: 20px; }}
        .info {{ margin: 20px 0; padding: 16px; background: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef; }}
        .info p {{ margin: 6px 0; font-size: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
        th, td {{ border: 1px solid #dee2e6; padding: 10px 16px; text-align: left; }}
        .nowrap {{ white-space: nowrap; }}
        th {{ background-color: #3498db; color: white; font-weight: 600; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        .status-assigned {{ color: #f39c12; font-weight: bold; }}
        .status-returned {{ color: #7f8c8d; }}
        .footer {{ margin-top: 40px; text-align: center; color: #7f8c8d; font-size: 13px; border-top: 1px solid #dee2e6; padding-top: 20px; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 13px; font-weight: 500; }}
        .badge-success {{ background: #27ae60; color: white; }}
        .badge-warning {{ background: #f39c12; color: white; }}
        .badge-secondary {{ background: #7f8c8d; color: white; }}
    </style>
</head>
<body>
    <h1>Asset Report</h1>
    <div class="info">
        <p><strong>Asset Name:</strong> {safe_name}</p>
        <p><strong>Serial Number:</strong> {safe_serial}</p>
        <p><strong>Category:</strong> {safe_category}</p>
        <p><strong>Purchased From:</strong> {safe_purchased_from}</p>
        <p><strong>Purchased Date:</strong> {asset.purchased_date.strftime('%Y-%m-%d') if asset.purchased_date else 'N/A'}</p>
        <p><strong>Current Status:</strong> {safe_status}</p>
        <p><strong>Report Generated:</strong> {now_ist} IST</p>
    </div>
    
    <h2>Assignment History ({len(assignments)})</h2>
    <table>
        <tr>
            <th>Employee</th>
            <th>Employee ID</th>
            <th>Asset Serial</th>
            <th>Assigned Date</th>
            <th>Returned Date</th>
            <th>Status</th>
            <th>Assign Notes</th>
            <th>Return Notes</th>
        </tr>"""
    
    for a in assignments:
        status_class = 'status-assigned' if a.returned_date is None else 'status-returned'
        status_text = 'In Use' if a.returned_date is None else 'Returned'
        badge_class = 'badge-warning' if a.returned_date is None else 'badge-secondary'
        returned = a.returned_date.strftime('%Y-%m-%d %H:%M:%S') if a.returned_date else '-'
        notes = a.notes or '-'
        return_notes = a.return_notes or '-'
        safe_emp_name = html.escape(a.employee.name)
        safe_emp_id = html.escape(a.employee.employee_id)
        safe_serial = html.escape(a.asset.serial_number)
        safe_notes = html.escape(notes)
        safe_return_notes = html.escape(return_notes)
        html_content += f"""<tr>
            <td>{safe_emp_name}</td>
            <td class="nowrap">{safe_emp_id}</td>
            <td><code>{safe_serial}</code></td>
            <td class="nowrap">{a.assigned_date.strftime('%Y-%m-%d %H:%M:%S')}</td>
            <td class="nowrap">{returned}</td>
            <td class="{status_class}"><span class="badge {badge_class}">{status_text}</span></td>
            <td>{safe_notes}</td>
            <td>{safe_return_notes}</td>
        </tr>"""
    
    html_content += """</table>
    
    <div class="footer">
        <p>Asset Management System - Asset Report</p>
        <p>Generated on: {timestamp}</p>
    </div>
</body>
</html>""".format(timestamp=now_ist)
    
    filename = f"Asset_Report_{asset.serial_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    AuditLog.log('EXPORT', 'assets', asset.id,
                new_value={'asset': asset.name, 'serial_number': asset.serial_number, 'type': 'Asset Report'},
                user_id=current_user.id)
    
    return Response(
        html_content,
        mimetype='text/html',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/html; charset=utf-8'
        }
    )
