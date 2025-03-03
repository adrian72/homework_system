# app/api/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import db
from app.models import User
from app.utils.auth import generate_token, validate_token
import re
import jwt
from datetime import datetime, timedelta
from app.utils.wordpress_client import check_wp_credentials

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    """注册新用户"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'student')
    
    # 验证必填字段
    if not username or not email or not password:
        return jsonify({'message': '用户名、邮箱和密码都是必填项'}), 400
    
    # 验证邮箱格式
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return jsonify({'message': '邮箱格式不正确'}), 400
    
    # 检查用户名和邮箱是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'message': '用户名已被使用'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'message': '邮箱已被注册'}), 400
    
    # 验证角色
    if role not in ['student', 'teacher', 'admin']:
        return jsonify({'message': '角色不合法'}), 400
    
    # 创建新用户
    user = User(username=username, email=email, role=role)
    user.password = password
    
    db.session.add(user)
    db.session.commit()
    
    # 生成JWT令牌
    token = generate_token(user.id)
    
    return jsonify({
        'message': '注册成功',
        'user': user.to_dict(),
        'token': token
    }), 201


@auth.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # 验证必填字段
    if not username or not password:
        return jsonify({'message': '用户名和密码都是必填项'}), 400
    
    # 查找用户（支持用户名或邮箱登录）
    user = User.query.filter_by(username=username).first() or User.query.filter_by(email=username).first()
    
    if user is None or not user.verify_password(password):
        return jsonify({'message': '用户名或密码错误'}), 401
    
    # 登录用户
    login_user(user)
    
    # 生成JWT令牌
    token = generate_token(user.id)
    
    return jsonify({
        'message': '登录成功',
        'user': user.to_dict(),
        'token': token
    }), 200


@auth.route('/wp-login', methods=['POST'])
def wordpress_login():
    """WordPress API登录"""
    data = request.get_json()
    wp_username = data.get('wp_username')
    wp_password = data.get('wp_password')
    
    if not wp_username or not wp_password:
        return jsonify({'message': 'WordPress用户名和密码都是必填项'}), 400
    
    # 验证WordPress凭据
    wp_user = check_wp_credentials(wp_username, wp_password)
    if not wp_user:
        return jsonify({'message': 'WordPress凭据验证失败'}), 401
    
    # 查找或创建用户
    user = User.query.filter_by(wp_user_id=wp_user['id']).first()
    if not user:
        # 创建新用户
        username = f"wp_{wp_user['username']}"
        email = wp_user.get('email', f"{username}@example.com")
        
        # 确保用户名唯一
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}_{counter}"
            counter += 1
        
        user = User(
            username=username,
            email=email,
            role='student',
            wp_user_id=wp_user['id'],
            avatar_url=wp_user.get('avatar_url')
        )
        user.password = wp_password  # 使用WordPress密码作为本地密码
        
        db.session.add(user)
        db.session.commit()
    
    # 登录用户
    login_user(user)
    
    # 生成JWT令牌
    token = generate_token(user.id)
    
    return jsonify({
        'message': '登录成功',
        'user': user.to_dict(),
        'token': token
    }), 200


@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    logout_user()
    return jsonify({'message': '登出成功'}), 200


@auth.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取当前用户信息"""
    return jsonify({
        'user': current_user.to_dict()
    }), 200


@auth.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新用户信息"""
    data = request.get_json()
    
    # 用户只能修改部分字段
    if 'email' in data:
        email = data['email']
        # 验证邮箱格式
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            return jsonify({'message': '邮箱格式不正确'}), 400
        
        # 确保邮箱未被其他用户使用
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user.id:
            return jsonify({'message': '邮箱已被其他用户使用'}), 400
        
        current_user.email = email
    
    if 'password' in data:
        new_password = data['password']
        current_password = data.get('current_password')
        
        # 验证当前密码
        if not current_password or not current_user.verify_password(current_password):
            return jsonify({'message': '当前密码不正确'}), 400
        
        current_user.password = new_password
    
    if 'avatar_url' in data:
        current_user.avatar_url = data['avatar_url']
    
    db.session.commit()
    
    return jsonify({
        'message': '个人信息更新成功',
        'user': current_user.to_dict()
    }), 200


@auth.route('/token/verify', methods=['POST'])
def verify_token():
    """验证JWT令牌"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'message': '令牌是必填项'}), 400
    
    # 验证令牌
    user_id = validate_token(token)
    if not user_id:
        return jsonify({'message': '令牌无效或已过期'}), 401
    
    # 查找用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    return jsonify({
        'message': '令牌有效',
        'user': user.to_dict()
    }), 200


@auth.route('/token/refresh', methods=['POST'])
def refresh_token():
    """刷新JWT令牌"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'message': '令牌是必填项'}), 400
    
    # 验证令牌
    user_id = validate_token(token)
    if not user_id:
        return jsonify({'message': '令牌无效或已过期'}), 401
    
    # 查找用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 生成新令牌
    new_token = generate_token(user.id)
    
    return jsonify({
        'message': '令牌刷新成功',
        'token': new_token
    }), 200
