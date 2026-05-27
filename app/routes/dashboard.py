from flask import Blueprint, render_template, redirect, url_for
from app import db
from app.models.asset import Asset
from app.models.employee import Employee
from app.models.assignment import Assignment

bp = Blueprint('dashboard', __name__)

@bp.route('/')
def index():
    total_assets = Asset.query.count()
    assigned_assets = Assignment.query.filter(Assignment.returned_date.is_(None)).count()
    available_assets = total_assets - assigned_assets
    total_employees = Employee.query.count()
    
    employees_with_assets = db.session.query(Employee.id).join(Assignment).filter(
        Assignment.returned_date.is_(None)
    ).distinct().count()
    
    return render_template('dashboard.html',
                           total_assets=total_assets,
                           assigned_assets=assigned_assets,
                           available_assets=available_assets,
                           total_employees=total_employees,
                           employees_with_assets=employees_with_assets)