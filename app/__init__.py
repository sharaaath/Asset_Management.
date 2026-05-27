from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from app.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bootstrap = Bootstrap()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    bootstrap.init_app(app)
    
    from app.routes import auth, dashboard, assets, employees, export
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(assets.bp)
    app.register_blueprint(employees.bp)
    app.register_blueprint(export.bp)
    
    with app.app_context():
        from app.models import asset, employee, assignment, user, audit_log
        db.create_all()
        from app.routes.auth import create_default_admin
        create_default_admin()
    
    return app