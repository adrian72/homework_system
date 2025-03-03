# app/views/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
import datetime

auth_views = Blueprint('auth_views', __name__)

@auth_views.route('/')
def index():
    """首页路由"""
    if current_user.is_authenticated:
        if current_user.is_student():
            return redirect(url_for('student_views.dashboard'))
        elif current_user.is_teacher():
            return redirect(url_for('teacher_views.dashboard'))
        elif current_user.is_admin():
            return redirect(url_for('admin_views.dashboard'))
    return render_template('auth/login.html')

@auth_views.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('auth_views.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(username=username).first() or User.query.filter_by(email=username).first()
        
        if user and user.verify_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('auth_views.index'))
        
        flash('用户名或密码错误', 'danger')
    
    return render_template('auth/login.html')

@auth_views.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已成功登出', 'success')
    return redirect(url_for('auth_views.login'))

@auth_views.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('auth_views.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证密码
        if password != confirm_password:
            flash('两次密码输入不一致', 'danger')
            return render_template('auth/register.html')
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已被使用', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return render_template('auth/register.html')
        
        # 创建新用户
        user = User(username=username, email=email, role='student')
        user.password = password
        
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth_views.login'))
    
    return render_template('auth/register.html')

@auth_views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """用户个人资料页面"""
    if request.method == 'POST':
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 更新邮箱
        if email and email != current_user.email:
            # 检查邮箱是否已被其他用户使用
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != current_user.id:
                flash('邮箱已被其他用户使用', 'danger')
                return redirect(url_for('auth_views.profile'))
            
            current_user.email = email
            flash('邮箱更新成功', 'success')
        
        # 更新密码
        if current_password and new_password:
            if not current_user.verify_password(current_password):
                flash('当前密码不正确', 'danger')
                return redirect(url_for('auth_views.profile'))
            
            if new_password != confirm_password:
                flash('两次密码输入不一致', 'danger')
                return redirect(url_for('auth_views.profile'))
            
            current_user.password = new_password
            flash('密码更新成功', 'success')
        
        db.session.commit()
        return redirect(url_for('auth_views.profile'))
    
    return render_template('auth/profile.html')

# 注入全局上下文变量
@auth_views.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}
