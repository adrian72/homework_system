from flask import Blueprint, redirect, url_for, render_template

student_bp = Blueprint('student', __name__, url_prefix='/student')
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@student_bp.route('/')
def student_index():
    return redirect(url_for('student.dashboard'))

@teacher_bp.route('/')
def teacher_index():
    return redirect(url_for('teacher.dashboard'))

@admin_bp.route('/')
def admin_index():
    return redirect(url_for('admin.dashboard'))

from . import student, teacher, admin
