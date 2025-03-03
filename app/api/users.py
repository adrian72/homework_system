# app/api/users.py
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import User, Course
from app.utils.auth import token_required, admin_required
from app.utils.file_handler import save_file
import re

users = Blueprint('users', __name__)

@users.route('/', methods=['GET'])
@admin_required
def get_users(current_user):
    """获取用户列表（仅限管理员）"""
    # 获取查询参数
    role = request.args.get('role')
    search = request.args.get('search')
    
    # 构建查询
    query = User.query
    
    # 应用过滤条件
    if role:
        query = query.filter_by(role=role)
    
    if search:
        query = query.filter(
            (User.username.like(f'%{search}%')) |
            (User.email.like(f'%{search}%'))
        )
    
    # 分页
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page)
    
    users = pagination.items
    
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@users.route('/', methods=['POST'])
@admin_required
def create_user(current_user):
    """创建新用户（仅限管理员）"""
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
    
    return jsonify({
        'message': '用户创建成功',
        'user': user.to_dict()
    }), 201


@users.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    """获取特定用户信息"""
    # 普通用户只能查看自己的信息
    if not current_user.is_admin() and current_user.id != user_id:
        return jsonify({'message': '无权查看该用户信息'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 获取用户基本信息
    user_data = user.to_dict()
    
    # 如果是学生，添加已选课程
    if user.is_student():
        user_data['courses'] = [course.to_dict() for course in user.courses_as_student]
    
    # 如果是教师，添加教授的课程
    if user.is_teacher():
        user_data['teaching_courses'] = [course.to_dict() for course in Course.query.filter_by(teacher_id=user.id).all()]
    
    return jsonify({
        'user': user_data
    }), 200


@users.route('/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    """更新用户信息"""
    # 普通用户只能更新自己的信息
    if not current_user.is_admin() and current_user.id != user_id:
        return jsonify({'message': '无权更新该用户信息'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    data = request.get_json()
    
    # 更新字段
    if 'email' in data and current_user.is_admin():
        email = data['email']
        # 验证邮箱格式
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            return jsonify({'message': '邮箱格式不正确'}), 400
        
        # 确保邮箱未被其他用户使用
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({'message': '邮箱已被其他用户使用'}), 400
        
        user.email = email
    
    if 'password' in data:
        # 非管理员需要验证当前密码
        if not current_user.is_admin():
            current_password = data.get('current_password')
            if not current_password or not user.verify_password(current_password):
                return jsonify({'message': '当前密码不正确'}), 400
        
        user.password = data['password']
    
    # 只有管理员可以更改角色
    if 'role' in data and current_user.is_admin():
        role = data['role']
        if role not in ['student', 'teacher', 'admin']:
            return jsonify({'message': '角色不合法'}), 400
        
        user.role = role
    
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
    
    db.session.commit()
    
    return jsonify({
        'message': '用户信息更新成功',
        'user': user.to_dict()
    }), 200


@users.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_user, user_id):
    """删除用户（仅限管理员）"""
    # 不能删除自己
    if current_user.id == user_id:
        return jsonify({'message': '不能删除自己的账户'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 删除用户
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'message': '用户删除成功'
    }), 200


@users.route('/avatar', methods=['POST'])
@token_required
def upload_avatar(current_user):
    """上传头像"""
    if 'avatar' not in request.files:
        return jsonify({'message': '未上传头像'}), 400
    
    avatar = request.files['avatar']
    if not avatar.filename:
        return jsonify({'message': '未选择文件'}), 400
    
    # 保存头像
    file_info = save_file(avatar, 'image')
    if not file_info:
        return jsonify({'message': '头像上传失败'}), 500
    
    # 更新用户头像
    current_user.avatar_url = file_info['url']
    db.session.commit()
    
    return jsonify({
        'message': '头像上传成功',
        'avatar_url': current_user.avatar_url
    }), 200


@users.route('/teachers', methods=['GET'])
@token_required
def get_teachers(current_user):
    """获取所有教师"""
    teachers = User.query.filter_by(role='teacher').all()
    
    return jsonify({
        'teachers': [teacher.to_dict() for teacher in teachers]
    }), 200


@users.route('/students', methods=['GET'])
@token_required
def get_students(current_user):
    """获取所有学生"""
    # 非管理员教师只能查看自己课程的学生
    if current_user.is_teacher() and not current_user.is_admin():
        # 获取教师的所有课程
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
        
        # 收集所有学生
        student_ids = set()
        for course in courses:
            for student in course.students:
                student_ids.add(student.id)
        
        students = [User.query.get(student_id) for student_id in student_ids]
    else:
        # 管理员可以查看所有学生
        students = User.query.filter_by(role='student').all()
    
    return jsonify({
        'students': [student.to_dict() for student in students]
    }), 200


@users.route('/count', methods=['GET'])
@admin_required
def get_user_count(current_user):
    """获取用户数量统计（仅限管理员）"""
    total_users = User.query.count()
    student_count = User.query.filter_by(role='student').count()
    teacher_count = User.query.filter_by(role='teacher').count()
    admin_count = User.query.filter_by(role='admin').count()
    
    return jsonify({
        'total_users': total_users,
        'student_count': student_count,
        'teacher_count': teacher_count,
        'admin_count': admin_count
    }), 200
