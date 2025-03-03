# app/api/courses.py
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Course, User, student_courses
from app.utils.auth import token_required, teacher_required, admin_required
from app.utils.file_handler import save_file, delete_file

courses = Blueprint('courses', __name__)

@courses.route('/', methods=['GET'])
@token_required
def get_courses(current_user):
    """获取课程列表"""
    # 获取查询参数
    teacher_id = request.args.get('teacher_id')
    student_id = request.args.get('student_id')
    
    # 构建查询
    query = Course.query
    
    # 根据角色限制查询范围
    if current_user.is_student():
        # 学生只能查看自己参与的课程
        return jsonify({
            'courses': [course.to_dict() for course in current_user.courses_as_student]
        }), 200
    
    elif current_user.is_teacher():
        # 教师只能查看自己的课程
        if teacher_id and int(teacher_id) != current_user.id:
            return jsonify({'message': '无权查看其他教师的课程'}), 403
        
        query = query.filter_by(teacher_id=current_user.id)
    
    # 应用过滤条件
    if teacher_id and (current_user.is_admin() or current_user.is_teacher()):
        query = query.filter_by(teacher_id=teacher_id)
    
    if student_id and current_user.is_admin():
        student = User.query.get(student_id)
        if not student:
            return jsonify({'message': '学生不存在'}), 404
        
        query = query.join(student_courses).filter(student_courses.c.student_id == student_id)
    
    # 排序
    query = query.order_by(Course.created_at.desc())
    
    # 执行查询
    courses = query.all()
    
    return jsonify({
        'courses': [course.to_dict() for course in courses]
    }), 200


@courses.route('/', methods=['POST'])
@teacher_required
def create_course(current_user):
    """创建新课程（教师或管理员）"""
    # 获取课程数据
    name = request.form.get('name')
    description = request.form.get('description', '')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    if not name:
        return jsonify({'message': '课程名称为必填项'}), 400
    
    # 创建课程
    course = Course(
        name=name,
        description=description,
        teacher_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # 处理封面图片
    if 'cover_image' in request.files:
        cover_image = request.files['cover_image']
        if cover_image.filename:
            file_info = save_file(cover_image, 'image')
            if file_info:
                course.cover_image = file_info['url']
    
    db.session.add(course)
    db.session.commit()
    
    return jsonify({
        'message': '课程创建成功',
        'course': course.to_dict()
    }), 201


@courses.route('/<int:course_id>', methods=['GET'])
@token_required
def get_course(current_user, course_id):
    """获取特定课程"""
    # 查找课程
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404
    
    # 权限检查
    if current_user.is_student():
        # 确认学生是该课程的成员
        if current_user not in course.students and not current_user.is_admin():
            return jsonify({'message': '您不是该课程的学生'}), 403
    
    elif current_user.is_teacher():
        # 确认是该课程的教师
        if course.teacher_id != current_user.id and not current_user.is_admin():
            return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 获取课程详情
    course_data = course.to_dict()
    
    # 添加学生和教师信息
    course_data['teacher'] = User.query.get(course.teacher_id).to_dict()
    course_data['students'] = [student.to_dict() for student in course.students]
    
    return jsonify({
        'course': course_data
    }), 200


@courses.route('/<int:course_id>', methods=['PUT'])
@token_required
def update_course(current_user, course_id):
    """更新课程信息（仅限课程教师或管理员）"""
    # 查找课程
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404
    
    # 权限检查
    if current_user.is_teacher() and course.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 获取更新数据
    data = request.form
    
    # 更新字段
    if 'name' in data:
        course.name = data['name']
    
    if 'description' in data:
        course.description = data['description']
    
    if 'start_date' in data:
        course.start_date = data['start_date'] or None
    
    if 'end_date' in data:
        course.end_date = data['end_date'] or None
    
    # 处理封面图片
    if 'cover_image' in request.files:
        cover_image = request.files['cover_image']
        if cover_image.filename:
            # 删除旧图片
            if course.cover_image:
                old_path = course.cover_image.replace('/static/uploads/', '')
                delete_file(old_path)
            
            # 保存新图片
            file_info = save_file(cover_image, 'image')
            if file_info:
                course.cover_image = file_info['url']
    
    db.session.commit()
    
    return jsonify({
        'message': '课程更新成功',
        'course': course.to_dict()
    }), 200


@courses.route('/<int:course_id>', methods=['DELETE'])
@admin_required
def delete_course(current_user, course_id):
    """删除课程（仅限管理员）"""
    # 查找课程
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404
    
    # 删除课程
    db.session.delete(course)
    db.session.commit()
    
    return jsonify({
        'message': '课程删除成功'
    }), 200


@courses.route('/<int:course_id>/students', methods=['GET'])
@token_required
def get_course_students(current_user, course_id):
    """获取课程学生"""
    # 查找课程
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404
    
    # 权限检查
    if current_user.is_teacher() and course.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的教师'}), 403
    
    if current_user.is_student() and current_user not in course.students and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的学生'}), 403
    
    # 获取学生列表
    students = [student.to_dict() for student in course.students]
    
    return jsonify({
        'students': students
    }), 200


@courses.route('/<int:course_id>/students', methods=['POST'])
@teacher_required
def add_course_student(current_user, course_id):
    """添加学生到课程（教师或管理员）"""
    # 查找课程
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404
    
    # 权限检查
    if course.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 获取学生ID
    data = request.get_json()
    student_id = data.get('student_id')
    
    if not student_id:
        return jsonify({'message': '学生ID为必填项'}), 400
    
    # 查找学生
    student = User.query.get(student_id)
    if not student:
        return jsonify({'message': '学生不存在'}), 404
    
    if not student.is_student():
        return jsonify({'message': '用户不是学生'}), 400
    
    # 检查学生是否已在课程中
    if student in course.students:
        return jsonify({'message': '学生已在课程中'}), 400
    
    # 添加学生到课程
    course.students.append(student)
    db.session.commit()
    
    return jsonify({
        'message': '学生添加成功',
        'student': student.to_dict()
    }), 201


@courses.route('/<int:course_id>/students/<int:student_id>', methods=['DELETE'])
@teacher_required
def remove_course_student(current_user, course_id, student_id):
    """从课程中移除学生（教师或管理员）"""
    # 查找课程
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404
    
    # 权限检查
    if course.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 查找学生
    student = User.query.get(student_id)
    if not student:
        return jsonify({'message': '学生不存在'}), 404
    
    # 检查学生是否在课程中
    if student not in course.students:
        return jsonify({'message': '学生不在课程中'}), 400
    
    # 从课程中移除学生
    course.students.remove(student)
    db.session.commit()
    
    return jsonify({
        'message': '学生移除成功'
    }), 200


@courses.route('/enroll/<int:course_id>', methods=['POST'])
@token_required
def enroll_course(current_user, course_id):
    """学生自主选课"""
    # 权限检查
    if not current_user.is_student():
        return jsonify({'message': '只有学生才能选课'}), 403
    
    # 查找课程
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404
    
    # 检查学生是否已在课程中
    if current_user in course.students:
        return jsonify({'message': '您已经选修了该课程'}), 400
    
    # 添加学生到课程
    course.students.append(current_user)
    db.session.commit()
    
    return jsonify({
        'message': '选课成功',
        'course': course.to_dict()
    }), 201


@courses.route('/unenroll/<int:course_id>', methods=['POST'])
@token_required
def unenroll_course(current_user, course_id):
    """学生退选课程"""
    # 权限检查
    if not current_user.is_student():
        return jsonify({'message': '只有学生才能退选课程'}), 403
    
    # 查找课程
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404
    
    # 检查学生是否在课程中
    if current_user not in course.students:
        return jsonify({'message': '您未选修该课程'}), 400
    
    # 从课程中移除学生
    course.students.remove(current_user)
    db.session.commit()
    
    return jsonify({
        'message': '退选成功'
    }), 200
