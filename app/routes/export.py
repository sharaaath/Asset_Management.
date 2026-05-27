from flask import Blueprint, Response
from flask_login import login_required, current_user
from app.models.asset import Asset
from app.models.employee import Employee
from app.models.assignment import Assignment
from app.models.audit_log import AuditLog
from datetime import datetime
import html
import csv
import io

bp = Blueprint('export', __name__, url_prefix='/export')

@bp.route('/csv')
@login_required
def export_csv():
    filename = f"asset_report_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ASSET MANAGEMENT REPORT'])
    writer.writerow([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    writer.writerow([])
    
    writer.writerow(['=== ASSETS ==='])
    writer.writerow(['ID', 'Name', 'Serial Number', 'Category', 'Purchased From', 'Purchased Date', 'Status', 'Assigned To'])
    
    assets = Asset.query.all()
    for asset in assets:
        assigned_to = asset.assigned_to.name if asset.assigned_to else ''
        status = 'Assigned' if asset.assigned_to else 'Available'
        writer.writerow([
            asset.id,
            asset.name,
            asset.serial_number,
            asset.category,
            asset.purchased_from or '',
            asset.purchased_date.strftime('%Y-%m-%d') if asset.purchased_date else '',
            status,
            assigned_to
        ])
    
    writer.writerow([])
    writer.writerow(['=== EMPLOYEES ==='])
    writer.writerow(['ID', 'Employee ID', 'Name', 'Position', 'Company', 'Total Assets Assigned', 'Currently Assigned'])
    
    employees = Employee.query.all()
    for emp in employees:
        total_assigned = len(emp.assignments)
        current_assigned = len([a for a in emp.assignments if a.returned_date is None])
        writer.writerow([
            emp.id,
            emp.employee_id,
            emp.name,
            emp.position or '',
            emp.company or '',
            total_assigned,
            current_assigned
        ])
    
    writer.writerow([])
    writer.writerow(['=== ASSIGNMENT HISTORY ==='])
    writer.writerow(['Asset', 'Asset Serial', 'Employee', 'Employee ID', 'Assigned Date', 'Returned Date', 'Status', 'Assign Notes', 'Return Notes'])
    
    assignments = Assignment.query.order_by(Assignment.assigned_date.desc()).all()
    for a in assignments:
        status = 'Active' if a.returned_date is None else 'Returned'
        writer.writerow([
            a.asset.name,
            a.asset.serial_number,
            a.employee.name,
            a.employee.employee_id,
            a.assigned_date.strftime('%Y-%m-%d %H:%M'),
            a.returned_date.strftime('%Y-%m-%d %H:%M') if a.returned_date else 'N/A',
            status,
            a.notes or '',
            a.return_notes or ''
        ])
    
    AuditLog.log('EXPORT', 'reports', new_value={'format': 'CSV', 'filename': filename}, user_id=current_user.id)
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@bp.route('/html')
@login_required
def export_html():
    assets = Asset.query.all()
    employees = Employee.query.all()
    assignments = Assignment.query.order_by(Assignment.assigned_date.desc()).all()
    
    total_assets = len(assets)
    assigned_count = len([a for a in assignments if a.returned_date is None])
    available_count = total_assets - assigned_count
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Asset Management Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; margin: 40px; background: white; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 12px; font-size: 26px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 12px; font-size: 20px; }}
        .info {{ margin: 20px 0; padding: 16px; background: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef; }}
        .info p {{ margin: 6px 0; font-size: 15px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #f8f9fa; border: 1px solid #dee2e6; border-left: 4px solid #3498db; padding: 20px; border-radius: 8px; flex: 1; text-align: center; }}
        .summary-card h3 {{ margin: 0; font-size: 32px; color: #2c3e50; }}
        .summary-card p {{ margin: 5px 0 0 0; color: #7f8c8d; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
        th {{ background-color: #3498db; color: white; padding: 10px 12px; text-align: left; font-weight: 600; }}
        td {{ padding: 10px 16px; border: 1px solid #dee2e6; }}
        .nowrap {{ white-space: nowrap; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        .status-assigned {{ color: #27ae60; font-weight: bold; }}
        .status-available {{ color: #3498db; font-weight: bold; }}
        .status-returned {{ color: #7f8c8d; }}
        .badge {{ display: inline-block; padding: 3px 7px; border-radius: 4px; font-size: 13px; font-weight: 500; }}
        .badge-success {{ background: #27ae60; color: white; }}
        .badge-warning {{ background: #f39c12; color: white; }}
        .badge-secondary {{ background: #7f8c8d; color: white; }}
        .footer {{ margin-top: 40px; text-align: center; color: #7f8c8d; font-size: 13px; border-top: 1px solid #dee2e6; padding-top: 20px; }}
    </style>
</head>
<body>
    <h1>Asset Management Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>{total_assets}</h3>
                <p>Total Assets</p>
            </div>
            <div class="summary-card" style="border-left-color: #f39c12;">
                <h3>{assigned_count}</h3>
                <p>Assigned</p>
            </div>
            <div class="summary-card" style="border-left-color: #27ae60;">
                <h3>{available_count}</h3>
                <p>Available</p>
            </div>
        </div>
        
        <h2>Assets</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Serial Number</th>
                    <th>Category</th>
                    <th>Purchased From</th>
                    <th>Purchased Date</th>
                    <th>Status</th>
                    <th>Assigned To</th>
                </tr>
            </thead>
            <tbody>"""
    
    for asset in assets:
        assigned_to = html.escape(asset.assigned_to.name) if asset.assigned_to else '-'
        status_class = 'status-assigned' if asset.assigned_to else 'status-available'
        status_text = 'Assigned' if asset.assigned_to else 'Available'
        purchased_date = asset.purchased_date.strftime('%Y-%m-%d') if asset.purchased_date else '-'
        safe_name = html.escape(asset.name)
        safe_serial = html.escape(asset.serial_number)
        safe_cat = html.escape(asset.category)
        safe_purchased_from = html.escape(asset.purchased_from or '-')
        html_content += f"""
                <tr>
                    <td>{asset.id}</td>
                    <td>{safe_name}</td>
                    <td>{safe_serial}</td>
                    <td>{safe_cat}</td>
                    <td>{safe_purchased_from}</td>
                    <td class="nowrap">{purchased_date}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{assigned_to}</td>
                </tr>"""
    
    html_content += """
            </tbody>
        </table>
        
        <h2>Employees</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Employee ID</th>
                    <th>Name</th>
                    <th>Position</th>
                    <th>Company</th>
                    <th>Total Assigned</th>
                    <th>Currently Using</th>
                </tr>
            </thead>
            <tbody>"""
    
    for emp in employees:
        total_assigned = len(emp.assignments)
        current_assigned = len([a for a in emp.assignments if a.returned_date is None])
        safe_emp_id = html.escape(emp.employee_id)
        safe_name = html.escape(emp.name)
        safe_position = html.escape(emp.position or '-')
        safe_company = html.escape(emp.company or '-')
        html_content += f"""
                <tr>
                    <td>{emp.id}</td>
                    <td>{safe_emp_id}</td>
                    <td>{safe_name}</td>
                    <td>{safe_position}</td>
                    <td>{safe_company}</td>
                    <td>{total_assigned}</td>
                    <td>{current_assigned}</td>
                </tr>"""
    
    html_content += """
            </tbody>
        </table>
        
        <h2>Assignment History</h2>
        <table>
            <thead>
                <tr>
                    <th>Asset</th>
                    <th>Asset Serial</th>
                    <th>Employee</th>
                    <th>Employee ID</th>
                    <th>Assigned Date</th>
                    <th>Returned Date</th>
                    <th>Status</th>
                        <th>Assign Notes</th>
                        <th>Return Notes</th>
                </tr>
            </thead>
            <tbody>"""
    
    for a in assignments:
        status_class = 'status-assigned' if a.returned_date is None else 'status-returned'
        status_text = 'In Use' if a.returned_date is None else 'Returned'
        returned = a.returned_date.strftime('%Y-%m-%d %H:%M') if a.returned_date else '-'
        safe_asset_name = html.escape(a.asset.name)
        safe_asset_serial = html.escape(a.asset.serial_number)
        safe_emp_name = html.escape(a.employee.name)
        safe_emp_id = html.escape(a.employee.employee_id)
        safe_notes = html.escape(a.notes or '-')
        safe_return_notes = html.escape(a.return_notes or '-')
        html_content += f"""
                <tr>
                    <td>{safe_asset_name}</td>
                    <td><code>{safe_asset_serial}</code></td>
                    <td>{safe_emp_name}</td>
                    <td><code>{safe_emp_id}</code></td>
                    <td class="nowrap">{a.assigned_date.strftime('%Y-%m-%d %H:%M')}</td>
                    <td class="nowrap">{returned}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{safe_notes}</td>
                    <td>{safe_return_notes}</td>
                </tr>"""
    
    html_content += """
            </tbody>
        </table>
        
        <div class="footer">
            <p>Asset Management System - Complete Report</p>
        </div>
</body>
</html>"""
    
    filename = f"asset_report_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.html"
    AuditLog.log('EXPORT', 'reports', new_value={'format': 'HTML', 'filename': filename}, user_id=current_user.id)
    
    return Response(
        html_content,
        mimetype='text/html',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

