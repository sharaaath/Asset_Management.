from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models.user import User
from app.models.audit_log import AuditLog

bp = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_default_admin():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin')
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        AuditLog.log('CREATE', 'users', admin.id, new_value={'username': 'admin'}, user_id=admin.id)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            AuditLog.log('LOGIN', 'users', user.id, user_id=user.id)
            flash('Welcome back!', 'success')
            next_page = request.args.get('next')
            if next_page:
                from urllib.parse import urlparse
                parsed = urlparse(next_page)
                if parsed.netloc or parsed.scheme:
                    next_page = None
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    AuditLog.log('LOGOUT', 'users', current_user.id, user_id=current_user.id)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('dashboard.index'))