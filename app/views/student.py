from . import student_bp
from flask import render_template

@student_bp.route('/dashboard')
def dashboard():
    return render_template('student/dashboard.html')

@student_bp.route('/homeworks/1')
def homework_detail():
    return render_template('student/homework_detail.html')
