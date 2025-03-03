# 保存到 app/utils/validators.py

import re
from flask import request, jsonify
from functools import wraps
from datetime import datetime

def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """验证用户名格式：字母、数字、下划线，3-64位"""
    pattern = r'^[a-zA-Z0-9_]{3,64}$'
    return re.match(pattern, username) is not None

def validate_password(password):
    """验证密码强度：至少8位，包含字母和数字"""
    if len(password) < 8:
        return False
    # 检查是否同时包含字母和数字
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_letter and has_digit

def sanitize_text(text):
    """清理文本内容，去除危险HTML标签"""
    if text is None:
        return ""
    # 移除可能的HTML/JavaScript注入
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.DOTALL)
    text = re.sub(r'on\w+="[^"]*"', '', text)
    return text

def validate_date(date_str, format='%Y-%m-%d'):
    """验证日期格式"""
    try:
        datetime.strptime(date_str, format)
        return True
    except (ValueError, TypeError):
        return False

def validate_integer(value, min_value=None, max_value=None):
    """验证整数值是否在指定范围内"""
    try:
        int_value = int(value)
        if min_value is not None and int_value < min_value:
            return False
        if max_value is not None and int_value > max_value:
            return False
        return True
    except (ValueError, TypeError):
        return False

def validate_float(value, min_value=None, max_value=None):
    """验证浮点数值是否在指定范围内"""
    try:
        float_value = float(value)
        if min_value is not None and float_value < min_value:
            return False
        if max_value is not None and float_value > max_value:
            return False
        return True
    except (ValueError, TypeError):
        return False

def validate_required_fields(data, required_fields):
    """验证必填字段是否存在"""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None or data[field] == '']
    return missing_fields

# 表单验证装饰器
def validate_form(*required_fields, **validators):
    """
    表单验证装饰器，验证请求中的表单字段
    
    使用示例:
    @validate_form('username', 'email', email=validate_email)
    def register():
        # 函数代码
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 验证必填字段
            missing = []
            for field in required_fields:
                if field not in request.form or not request.form[field].strip():
                    missing.append(field)
            
            if missing:
                return jsonify({
                    'status': 'error', 
                    'message': f'缺少必填字段: {", ".join(missing)}'
                }), 400
            
            # 应用字段特定的验证器
            errors = {}
            for field, validator in validators.items():
                if field in request.form and request.form[field].strip():
                    if not validator(request.form[field]):
                        errors[field] = '验证失败'
            
            if errors:
                return jsonify({
                    'status': 'error', 
                    'message': '表单验证失败',
                    'errors': errors
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# JSON验证装饰器
def validate_json(*required_fields, **validators):
    """
    JSON验证装饰器，验证请求中的JSON字段
    
    使用示例:
    @validate_json('username', 'email', email=validate_email)
    def register_api():
        # 函数代码
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 确保请求包含JSON数据
            if not request.is_json:
                return jsonify({
                    'status': 'error', 
                    'message': '需要JSON格式的请求'
                }), 400
            
            data = request.get_json()
            
            # 验证必填字段
            missing = []
            for field in required_fields:
                if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                    missing.append(field)
            
            if missing:
                return jsonify({
                    'status': 'error', 
                    'message': f'缺少必填字段: {", ".join(missing)}'
                }), 400
            
            # 应用字段特定的验证器
            errors = {}
            for field, validator in validators.items():
                if field in data and data[field] is not None:
                    if isinstance(data[field], str) and not data[field].strip():
                        continue
                    if not validator(data[field]):
                        errors[field] = '验证失败'
            
            if errors:
                return jsonify({
                    'status': 'error', 
                    'message': 'JSON验证失败',
                    'errors': errors
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator