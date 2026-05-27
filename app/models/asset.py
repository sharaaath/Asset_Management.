from datetime import datetime
from app import db

class Asset(db.Model):
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    purchased_from = db.Column(db.String(100))
    purchased_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    assignments = db.relationship('Assignment', backref='asset', lazy=True)
    
    @property
    def status(self):
        from app.models.assignment import Assignment
        active_assignment = Assignment.query.filter_by(
            asset_id=self.id, 
            returned_date=None
        ).first()
        return 'ASSIGNED' if active_assignment else 'AVAILABLE'
    
    @property
    def assigned_to(self):
        from app.models.assignment import Assignment
        from app.models.employee import Employee
        active_assignment = Assignment.query.filter_by(
            asset_id=self.id, 
            returned_date=None
        ).first()
        if active_assignment:
            return Employee.query.get(active_assignment.employee_id)
        return None