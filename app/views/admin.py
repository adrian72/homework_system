from . import admin_bp
from flask import render_template

@admin_bp.route('/dashboard')
def dashboard():
    return render_template('admin/dashboard.html')
