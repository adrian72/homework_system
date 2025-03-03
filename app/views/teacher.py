from . import teacher_bp
from flask import render_template

@teacher_bp.route('/dashboard')
def dashboard():
    return render_template('teacher/dashboard.html')
