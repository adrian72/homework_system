# app/api/homeworks.py
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Homework, Course, Submission
from app.utils.auth import token_required, teacher_required
from datetime import datetime

homeworks = Blueprint('homeworks', __name__)

@homeworks.route('/', methods=['GET'])
@token_required
def get_homeworks(current_user):
    """获取作业列表"""
    # 获取查询参数
    course_id = request.args.get('course_id')
    assignment_type = request.args.get('assignment_type')
    
    # 验证课程ID
    if not course_id:
        return jsonify({'message': '课程ID为必填项'}), 400
    
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
    
    # 构建查询
    query = Homework.query.filter_by(course_id=course_id)
    
    # 应用过滤条件
    if assignment_type:
        query = query.filter_by(assignment_type=assignment_type)
    
    # 排序
    query = query.order_by(Homework.created_at.desc())
    
    # 执行查询
    homeworks = query.all()
    
    return jsonify({
        'homeworks': [homework.to_dict() for homework in homeworks]
    }), 200


@homeworks.route('/', methods=['POST'])
@teacher_required
def create_homework(current_user):
    """创建新作业（教师）"""
    # 获取作业数据
    data = request.get_json()
    
    title = data.get('title')
    description = data.get('description', '')
    course_id = data.get('course_id')
    due_date = data.get('due_date')
    assignment_type = data.get('assignment_type')
    
    # 验证必填字段
    if not title or not course_id or not assignment_type:
        return jsonify({'message': '标题、课程ID和作业类型为必填项'}), 400
    
    # 验证作业类型
    if assignment_type not in ['essay', 'oral']:
        return jsonify({'message': '不支持的作业类型'}), 400
    
    # 查找课程
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404
    
    # 确认是该课程的教师
    if course.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 创建作业
    homework = Homework(
        title=title,
        description=description,
        course_id=course_id,
        assignment_type=assignment_type
    )
    
    # 处理可选字段
    if due_date:
        try:
            homework.due_date = datetime.fromisoformat(due_date)
        except ValueError:
            return jsonify({'message': '截止日期格式不正确'}), 400
    
    db.session.add(homework)
    db.session.commit()
    
    return jsonify({
        'message': '作业创建成功',
        'homework': homework.to_dict()
    }), 201


@homeworks.route('/<int:homework_id>', methods=['GET'])
@token_required
def get_homework(current_user, homework_id):
    """获取特定作业"""
    # 查找作业
    homework = Homework.query.get(homework_id)
    if not homework:
        return jsonify({'message': '作业不存在'}), 404
    
    # 查找课程
    course = Course.query.get(homework.course_id)
    
    # 权限检查
    if current_user.is_student():
        # 确认学生是该课程的成员
        if current_user not in course.students and not current_user.is_admin():
            return jsonify({'message': '您不是该课程的学生'}), 403
    
    elif current_user.is_teacher():
        # 确认是该课程的教师
        if course.teacher_id != current_user.id and not current_user.is_admin():
            return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 获取作业详情
    homework_data = homework.to_dict()
    
    # 如果是教师，添加提交统计
    if current_user.is_teacher() or current_user.is_admin():
        submitted_count = Submission.query.filter_by(homework_id=homework_id).distinct(Submission.student_id).count()
        total_students = course.students.count()
        
        homework_data['submission_stats'] = {
            'submitted_count': submitted_count,
            'total_students': total_students,
            'submission_rate': submitted_count / total_students if total_students > 0 else 0
        }
    
    # 如果是学生，添加提交状态
    if current_user.is_student():
        submission = Submission.query.filter_by(
            homework_id=homework_id,
            student_id=current_user.id
        ).order_by(Submission.version.desc()).first()
        
        if submission:
            homework_data['submission_status'] = {
                'status': submission.status,
                'version': submission.version,
                'created_at': submission.created_at.isoformat()
            }
        else:
            homework_data['submission_status'] = {
                'status': 'not_submitted'
            }
    
    return jsonify({
        'homework': homework_data
    }), 200


@homeworks.route('/<int:homework_id>', methods=['PUT'])
@teacher_required
def update_homework(current_user, homework_id):
    """更新作业（教师）"""
    # 查找作业
    homework = Homework.query.get(homework_id)
    if not homework:
        return jsonify({'message': '作业不存在'}), 404
    
    # 确认是该课程的教师
    course = Course.query.get(homework.course_id)
    if course.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 获取更新数据
    data = request.get_json()
    
    # 更新字段
    if 'title' in data:
        homework.title = data['title']
    
    if 'description' in data:
        homework.description = data['description']
    
    if 'due_date' in data:
        if data['due_date']:
            try:
                homework.due_date = datetime.fromisoformat(data['due_date'])
            except ValueError:
                return jsonify({'message': '截止日期格式不正确'}), 400
        else:
            homework.due_date = None
    
    # 不允许修改作业类型，以防影响已有提交
    
    db.session.commit()
    
    return jsonify({
        'message': '作业更新成功',
        'homework': homework.to_dict()
    }), 200


@homeworks.route('/<int:homework_id>', methods=['DELETE'])
@teacher_required
def delete_homework(current_user, homework_id):
    """删除作业（教师）"""
    # 查找作业
    homework = Homework.query.get(homework_id)
    if not homework:
        return jsonify({'message': '作业不存在'}), 404
    
    # 确认是该课程的教师
    course = Course.query.get(homework.course_id)
    if course.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 检查是否有提交
    submissions = Submission.query.filter_by(homework_id=homework_id).count()
    if submissions > 0:
        return jsonify({
            'message': '该作业已有学生提交，无法删除',
            'submission_count': submissions
        }), 400
    
    # 删除作业
    db.session.delete(homework)
    db.session.commit()
    
    return jsonify({
        'message': '作业删除成功'
    }), 200


@homeworks.route('/<int:homework_id>/submissions', methods=['GET'])
@teacher_required
def get_homework_submissions(current_user, homework_id):
    """获取作业的所有提交（教师）"""
    # 查找作业
    homework = Homework.query.get(homework_id)
    if not homework:
        return jsonify({'message': '作业不存在'}), 404
    
    # 确认是该课程的教师
    course = Course.query.get(homework.course_id)
    if course.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 查询提交
    submissions = Submission.query.filter_by(homework_id=homework_id).all()
    
    # 按学生分组
    submissions_by_student = {}
    for submission in submissions:
        student_id = submission.student_id
        if student_id not in submissions_by_student:
            submissions_by_student[student_id] = []
        
        submissions_by_student[student_id].append(submission.to_dict())
    
    # 对每个学生的提交按版本排序
    for student_id, student_submissions in submissions_by_student.items():
        submissions_by_student[student_id] = sorted(
            student_submissions,
            key=lambda x: x['version'],
            reverse=True
        )
    
    return jsonify({
        'submissions_by_student': submissions_by_student
    }), 200


@homeworks.route('/<int:homework_id>/statistics', methods=['GET'])
@teacher_required
def get_homework_statistics(current_user, homework_id):
    """获取作业统计信息（教师）"""
    # 查找作业
    homework = Homework.query.get(homework_id)
    if not homework:
        return jsonify({'message': '作业不存在'}), 404
    
    # 确认是该课程的教师
    course = Course.query.get(homework.course_id)
    if course.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 统计信息
    total_students = course.students.count()
    submissions = Submission.query.filter_by(homework_id=homework_id).all()
    
    # 按提交状态分组
    status_counts = {
        'submitted': 0,
        'graded': 0,
        'needs_revision': 0,
        'revised': 0,
        'not_submitted': 0
    }
    
    # 提交学生ID集合
    submitted_student_ids = set()
    
    for submission in submissions:
        submitted_student_ids.add(submission.student_id)
        status_counts[submission.status] += 1
    
    status_counts['not_submitted'] = total_students - len(submitted_student_ids)
    
    # 计算提交率
    submission_rate = len(submitted_student_ids) / total_students if total_students > 0 else 0
    
    return jsonify({
        'homework': homework.to_dict(),
        'statistics': {
            'total_students': total_students,
            'submitted_students': len(submitted_student_ids),
            'submission_rate': submission_rate,
            'status_counts': status_counts
        }
    }), 200
