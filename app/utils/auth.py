# app/utils/auth.py
from flask import current_app
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from app.models import User

def generate_token(user_id):
    """生成JWT令牌"""
    payload = {
        'exp': datetime.utcnow() + timedelta(days=1),  # 过期时间：1天
        'iat': datetime.utcnow(),  # 签发时间
        'sub': user_id  # 主题：用户ID
    }
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def validate_token(token):
    """验证JWT令牌并返回用户ID"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload['sub']
    except jwt.ExpiredSignatureError:
        # 令牌已过期
        return None
    except jwt.InvalidTokenError:
        # 令牌无效
        return None

def token_required(f):
    """JWT令牌验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头中获取令牌
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split('Bearer ')[1]
        
        if not token:
            return jsonify({'message': '令牌缺失'}), 401
        
        # 验证令牌
        user_id = validate_token(token)
        if not user_id:
            return jsonify({'message': '令牌无效或已过期'}), 401
        
        # 查找用户
        current_user = User.query.get(user_id)
        if not current_user:
            return jsonify({'message': '用户不存在'}), 404
        
        # 将用户传递给被装饰的函数
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin():
            return jsonify({'message': '需要管理员权限'}), 403
        return f(current_user, *args, **kwargs)
    
    return token_required(decorated)

def teacher_required(f):
    """教师权限验证装饰器"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_teacher() and not current_user.is_admin():
            return jsonify({'message': '需要教师权限'}), 403
        return f(current_user, *args, **kwargs)
    
    return token_required(decorated)

def student_required(f):
    """学生权限验证装饰器"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_student() and not current_user.is_admin():
            return jsonify({'message': '需要学生权限'}), 403
        return f(current_user, *args, **kwargs)
    
    return token_required(decorated)
