from datetime import datetime
from app import db

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100))
    company = db.Column(db.String(100))
    photo_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    assignments = db.relationship('Assignment', backref='employee', lazy=True)
    
    @property
    def currently_assigned_assets(self):
        from app.models.assignment import Assignment
        result = []
        for a in self.assignments:
            if a.returned_date is None and a.asset:
                result.append(a.asset)
        return result
    
    @property
    def returned_assets(self):
        result = []
        for a in self.assignments:
            if a.returned_date is not None and a.asset:
                result.append(a.asset)
        return result
    
    @property
    def initials(self):
        parts = self.name.split()
        if len(parts) >= 2:
            return parts[0][0].upper() + parts[1][0].upper()
        return parts[0][0].upper() if parts else '?'