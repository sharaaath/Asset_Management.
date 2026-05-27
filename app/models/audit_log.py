from datetime import datetime
from app import db
import json

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer)
    
    @staticmethod
    def log(action, table_name, record_id=None, old_value=None, new_value=None, user_id=None):
        log_entry = AuditLog(
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            user_id=user_id
        )
        db.session.add(log_entry)
        db.session.commit()
