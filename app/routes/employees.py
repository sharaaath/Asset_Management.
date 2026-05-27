from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app import db
from app.models.employee import Employee
from app.models.assignment import Assignment
from app.models.audit_log import AuditLog
from datetime import datetime
import html
import os
import uuid

bp = Blueprint('employees', __name__, url_prefix='/employees')

@bp.route('/list')
def list():
    search_query = request.args.get('search', '')
    company_filter = request.args.get('company', '')
    
    query = Employee.query
    
    if search_query:
        query = query.filter(
            (Employee.name.ilike(f'%{search_query}%')) |
            (Employee.employee_id.ilike(f'%{search_query}%')) |
            (Employee.position.ilike(f'%{search_query}%'))
        )
    
    if company_filter:
        query = query.filter(Employee.company == company_filter)
    
    employees = query.order_by(Employee.created_at.desc()).all()
    
    companies = db.session.query(Employee.company).filter(Employee.company.isnot(None)).distinct().all()
    companies = [c[0] for c in companies if c[0]]
    
    return render_template('employees_list.html',
                           employees=employees,
                           search_query=search_query,
                           company_filter=company_filter,
                           companies=companies)

@bp.route('/detail/<int:employee_id>')
def detail(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    assignments = Assignment.query.filter_by(employee_id=employee_id).order_by(Assignment.assigned_date.desc()).all()
    return render_template('employee_detail.html', employee=employee, assignments=assignments)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        employee_id_val = request.form.get('employee_id')
        name = request.form.get('name')
        position = request.form.get('position')
        company = request.form.get('company')

        if not name:
            flash('Employee name is required.', 'danger')
            return render_template('employee_form.html')
        if not employee_id_val:
            flash('Employee ID is required.', 'danger')
            return render_template('employee_form.html')
        if len(name) > 100:
            flash('Employee name must be 100 characters or less.', 'danger')
            return render_template('employee_form.html')
        if len(employee_id_val) > 50:
            flash('Employee ID must be 50 characters or less.', 'danger')
            return render_template('employee_form.html')
        
        photo = request.files.get('photo')
        photo_url = None
        
        if photo and photo.filename:
            filename = f"emp_{employee_id_val}_{uuid.uuid4().hex[:8]}_{photo.filename}"
            upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            photo_path = os.path.join(upload_folder, filename)
            photo.save(photo_path)
            photo_url = f'/static/uploads/{filename}'
        
        existing = Employee.query.filter_by(employee_id=employee_id_val).first()
        if existing:
            flash(f'Employee with ID "{employee_id_val}" already exists! Please use a different ID.', 'danger')
            return redirect(url_for('employees.list'))
        
        employee = Employee(
            employee_id=employee_id_val,
            name=name,
            position=position,
            company=company,
            photo_url=photo_url
        )
        db.session.add(employee)
        db.session.commit()
        

        
        AuditLog.log('CREATE', 'employees', employee.id,
                    new_value={'name': name, 'employee_id': employee_id_val},
                    user_id=current_user.id)
        
        flash(f'Employee "{name}" added successfully!', 'success')
        return redirect(url_for('employees.list'))
    
    return render_template('employee_form.html')

@bp.route('/edit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        old_values = {'name': employee.name, 'position': employee.position, 'company': employee.company}
        
        name = request.form.get('name', '').strip()
        if not name:
            flash('Employee name is required.', 'danger')
            return render_template('employee_form.html', employee=employee)
        if len(name) > 100:
            flash('Employee name must be 100 characters or less.', 'danger')
            return render_template('employee_form.html', employee=employee)
        employee.name = name
        employee.position = request.form.get('position')
        employee.company = request.form.get('company')
        
        photo = request.files.get('photo')
        if photo and photo.filename:
            filename = f"emp_{employee.id}_{uuid.uuid4().hex[:8]}_{photo.filename}"
            upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            photo_path = os.path.join(upload_folder, filename)
            photo.save(photo_path)
            employee.photo_url = f'/static/uploads/{filename}'
        
        db.session.commit()
        
        AuditLog.log('UPDATE', 'employees', employee.id,
                    old_value=old_values,
                    new_value={'name': employee.name},
                    user_id=current_user.id)
        
        flash(f'Employee "{employee.name}" updated successfully!', 'success')
        return redirect(url_for('employees.detail', employee_id=employee.id))
    
    return render_template('employee_form.html', employee=employee)

@bp.route('/delete/<int:employee_id>', methods=['POST'])
@login_required
def delete(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    active_assignments = Assignment.query.filter_by(employee_id=employee_id, returned_date=None).count()
    if active_assignments > 0:
        flash('Cannot delete employee with active asset assignments! Please return all assets first.', 'danger')
        return redirect(url_for('employees.detail', employee_id=employee_id))
    
    AuditLog.log('DELETE', 'employees', employee.id,
                old_value={'name': employee.name, 'employee_id': employee.employee_id},
                user_id=current_user.id)
    
    db.session.delete(employee)
    db.session.commit()
    
    flash(f'Employee "{employee.name}" deleted successfully!', 'success')
    return redirect(url_for('employees.list'))

@bp.route('/print/<int:employee_id>')
@login_required
def print_report(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    assignments = Assignment.query.filter_by(employee_id=employee_id).order_by(Assignment.assigned_date.desc()).all()
    
    now_ist = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    safe_name = html.escape(employee.name)
    safe_emp_id = html.escape(employee.employee_id)
    safe_position = html.escape(employee.position or 'N/A')
    safe_company = html.escape(employee.company or 'N/A')
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Employee Asset Report - {safe_name}</title>
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
        .status-active {{ color: #27ae60; font-weight: bold; }}
        .status-returned {{ color: #7f8c8d; }}
        .footer {{ margin-top: 40px; text-align: center; color: #7f8c8d; font-size: 13px; border-top: 1px solid #dee2e6; padding-top: 20px; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 13px; font-weight: 500; }}
        .badge-success {{ background: #27ae60; color: white; }}
        .badge-warning {{ background: #f39c12; color: white; }}
    </style>
</head>
<body>
    <h1>Employee Asset Report</h1>
    <div class="info">
        <p><strong>Employee Name:</strong> {safe_name}</p>
        <p><strong>Employee ID:</strong> {safe_emp_id}</p>
        <p><strong>Position:</strong> {safe_position}</p>
        <p><strong>Company:</strong> {safe_company}</p>
        <p><strong>Report Generated:</strong> {now_ist} IST</p>
    </div>
    
    <h2>Currently Assigned Assets ({len([a for a in assignments if a.returned_date is None])})</h2>
    <table>
        <tr>
            <th>Asset Name</th>
            <th>Serial Number</th>
            <th>Category</th>
            <th>Employee ID</th>
            <th>Assigned Date</th>
            <th>Notes</th>
            <th>Status</th>
        </tr>"""
    
    currently_assigned = [a for a in assignments if a.returned_date is None]
    if currently_assigned:
        for a in currently_assigned:
            notes = a.notes or '-'
            safe_asset_name = html.escape(a.asset.name)
            safe_asset_serial = html.escape(a.asset.serial_number)
            safe_asset_cat = html.escape(a.asset.category)
            safe_emp_id = html.escape(a.employee.employee_id)
            safe_notes = html.escape(notes)
            html_content += f"""<tr>
                <td>{safe_asset_name}</td>
                <td>{safe_asset_serial}</td>
                <td>{safe_asset_cat}</td>
                <td><code>{safe_emp_id}</code></td>
                <td class="nowrap">{a.assigned_date.strftime('%Y-%m-%d %H:%M:%S')}</td>
                <td>{safe_notes}</td>
                <td class="status-active"><span class="badge badge-success">In Use</span></td>
            </tr>"""
    else:
        html_content += "<tr><td colspan='7' style='text-align:center;'>No currently assigned assets</td></tr>"
    
    html_content += """</table>
    
    <h2>Assignment History ({total})</h2>
    <table>
        <tr>
            <th>Asset Name</th>
            <th>Serial Number</th>
            <th>Category</th>
            <th>Employee ID</th>
            <th>Assigned Date</th>
            <th>Returned Date</th>
            <th>Status</th>
            <th>Assign Notes</th>
            <th>Return Notes</th>
        </tr>""".format(total=len(assignments))
    
    for a in assignments:
        status_class = 'status-active' if a.returned_date is None else 'status-returned'
        status_text = 'In Use' if a.returned_date is None else 'Returned'
        badge_class = 'badge-success' if a.returned_date is None else 'badge-warning'
        returned = a.returned_date.strftime('%Y-%m-%d %H:%M:%S') if a.returned_date else '-'
        notes = a.notes or '-'
        return_notes = a.return_notes or '-'
        safe_asset_name = html.escape(a.asset.name)
        safe_asset_serial = html.escape(a.asset.serial_number)
        safe_asset_cat = html.escape(a.asset.category)
        safe_emp_id = html.escape(a.employee.employee_id)
        safe_notes = html.escape(notes)
        safe_return_notes = html.escape(return_notes)
        html_content += f"""<tr>
            <td>{safe_asset_name}</td>
            <td>{safe_asset_serial}</td>
            <td>{safe_asset_cat}</td>
            <td><code>{safe_emp_id}</code></td>
            <td class="nowrap">{a.assigned_date.strftime('%Y-%m-%d %H:%M:%S')}</td>
            <td class="nowrap">{returned}</td>
            <td class="{status_class}"><span class="badge {badge_class}">{status_text}</span></td>
            <td>{safe_notes}</td>
            <td>{safe_return_notes}</td>
        </tr>"""
    
    html_content += """</table>
    
    <div class="footer">
        <p>Asset Management System - Employee Report</p>
        <p>Generated on: {timestamp}</p>
    </div>
</body>
</html>""".format(timestamp=now_ist)
    
    filename = f"Employee_Report_{employee.employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    AuditLog.log('EXPORT', 'employees', employee.id,
                new_value={'employee': employee.name, 'type': 'Employee Report'},
                user_id=current_user.id)
    
    return Response(
        html_content,
        mimetype='text/html',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/html; charset=utf-8'
        }
    )

