# app/api/submissions.py
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Submission, Homework, User, Course
from app.utils.auth import token_required, student_required, teacher_required
from app.utils.file_handler import save_file
import json
from sqlalchemy import and_, or_

submissions = Blueprint('submissions', __name__)

@submissions.route('/', methods=['POST'])
@student_required
def create_submission(current_user):
    """创建新作业提交"""
    # 获取作业ID
    homework_id = request.form.get('homework_id')
    if not homework_id:
        return jsonify({'message': '作业ID为必填项'}), 400
    
    # 查找作业
    homework = Homework.query.get(homework_id)
    if not homework:
        return jsonify({'message': '作业不存在'}), 404
    
    # 确认学生是该课程的成员
    course = Course.query.get(homework.course_id)
    if current_user not in course.students and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的学生'}), 403
    
    # 检查之前的提交
    prev_submission = Submission.query.filter_by(
        homework_id=homework_id,
        student_id=current_user.id
    ).order_by(Submission.version.desc()).first()
    
    # 设置版本号
    version = 1
    if prev_submission:
        version = prev_submission.version + 1
    
    # 获取附加评论
    comment = request.form.get('comment', '')
    
    # 处理上传的文件
    content_data = {}
    
    # 根据作业类型处理不同的上传
    if homework.assignment_type == 'essay':
        # 处理图像上传
        if 'essay_images' in request.files:
            images = request.files.getlist('essay_images')
            image_data = []
            for img in images:
                if img.filename:
                    file_info = save_file(img, 'image')
                    if file_info:
                        image_data.append(file_info)
            
            if image_data:
                content_data['images'] = image_data
    
    elif homework.assignment_type == 'oral':
        # 处理音频上传
        if 'oral_audio' in request.files:
            audio = request.files['oral_audio']
            if audio.filename:
                file_info = save_file(audio, 'audio')
                if file_info:
                    content_data['audio'] = file_info
    
    # 处理文本内容
    text_content = request.form.get('text_content', '')
    if text_content:
        content_data['text'] = text_content
    
    # 创建提交记录
    submission = Submission(
        homework_id=homework_id,
        student_id=current_user.id,
        comment=comment,
        version=version,
        status='submitted'
    )
    
    # 设置内容
    submission.content_data = content_data
    
    db.session.add(submission)
    db.session.commit()
    
    return jsonify({
        'message': '作业提交成功',
        'submission': submission.to_dict()
    }), 201


@submissions.route('/', methods=['GET'])
@token_required
def get_submissions(current_user):
    """获取作业提交列表"""
    # 获取查询参数
    homework_id = request.args.get('homework_id')
    student_id = request.args.get('student_id')
    course_id = request.args.get('course_id')
    status = request.args.get('status')
    
    # 构建查询
    query = Submission.query
    
    # 根据角色限制查询范围
    if current_user.is_student():
        # 学生只能查看自己的提交
        query = query.filter_by(student_id=current_user.id)
    elif current_user.is_teacher():
        # 教师只能查看自己课程的提交
        if course_id:
            # 确认是该课程的教师
            course = Course.query.get(course_id)
            if not course or course.teacher_id != current_user.id:
                return jsonify({'message': '您不是该课程的教师'}), 403
            
            query = query.join(Homework).filter(Homework.course_id == course_id)
        else:
            # 获取教师所有课程的作业提交
            teacher_courses = Course.query.filter_by(teacher_id=current_user.id).all()
            course_ids = [c.id for c in teacher_courses]
            if not course_ids:
                return jsonify({'submissions': []}), 200
            
            query = query.join(Homework).filter(Homework.course_id.in_(course_ids))
    
    # 应用过滤条件
    if homework_id:
        query = query.filter_by(homework_id=homework_id)
    
    if student_id and (current_user.is_teacher() or current_user.is_admin()):
        query = query.filter_by(student_id=student_id)
    
    if status:
        query = query.filter_by(status=status)
    
    # 排序
    query = query.order_by(Submission.created_at.desc())
    
    # 执行查询
    submissions = query.all()
    
    return jsonify({
        'submissions': [sub.to_dict() for sub in submissions]
    }), 200


@submissions.route('/<int:submission_id>', methods=['GET'])
@token_required
def get_submission(current_user, submission_id):
    """获取特定作业提交"""
    # 查找提交
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({'message': '提交不存在'}), 404
    
    # 权限检查
    if current_user.is_student() and submission.student_id != current_user.id:
        return jsonify({'message': '无权查看该提交'}), 403
    
    if current_user.is_teacher():
        # 确认是否为该作业所属课程的教师
        homework = Homework.query.get(submission.homework_id)
        course = Course.query.get(homework.course_id)
        if course.teacher_id != current_user.id:
            return jsonify({'message': '您不是该课程的教师'}), 403
    
    return jsonify({
        'submission': submission.to_dict()
    }), 200


@submissions.route('/<int:submission_id>', methods=['PUT'])
@student_required
def update_submission(current_user, submission_id):
    """更新作业提交（仅限学生本人）"""
    # 查找提交
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({'message': '提交不存在'}), 404
    
    # 权限检查
    if submission.student_id != current_user.id:
        return jsonify({'message': '无权修改该提交'}), 403
    
    # 确保提交状态允许修改
    if submission.status not in ['submitted', 'revised']:
        return jsonify({'message': '当前状态不允许修改提交'}), 400
    
    # 获取提交数据
    comment = request.form.get('comment')
    if comment is not None:
        submission.comment = comment
    
    # 获取作业信息
    homework = Homework.query.get(submission.homework_id)
    content_data = submission.content_data
    
    # 根据作业类型处理不同的上传
    if homework.assignment_type == 'essay':
        # 处理图像上传
        if 'essay_images' in request.files:
            images = request.files.getlist('essay_images')
            image_data = content_data.get('images', [])
            for img in images:
                if img.filename:
                    file_info = save_file(img, 'image')
                    if file_info:
                        image_data.append(file_info)
            
            content_data['images'] = image_data
    
    elif homework.assignment_type == 'oral':
        # 处理音频上传
        if 'oral_audio' in request.files:
            audio = request.files['oral_audio']
            if audio.filename:
                file_info = save_file(audio, 'audio')
                if file_info:
                    content_data['audio'] = file_info
    
    # 处理文本内容
    text_content = request.form.get('text_content')
    if text_content is not None:
        content_data['text'] = text_content
    
    # 更新提交内容
    submission.content_data = content_data
    submission.status = 'revised'
    
    db.session.commit()
    
    return jsonify({
        'message': '提交更新成功',
        'submission': submission.to_dict()
    }), 200


@submissions.route('/<int:submission_id>', methods=['DELETE'])
@token_required
def delete_submission(current_user, submission_id):
    """删除作业提交（学生本人或管理员）"""
    # 查找提交
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({'message': '提交不存在'}), 404
    
    # 权限检查
    if not current_user.is_admin() and submission.student_id != current_user.id:
        return jsonify({'message': '无权删除该提交'}), 403
    
    # 删除提交
    db.session.delete(submission)
    db.session.commit()
    
    return jsonify({
        'message': '提交删除成功'
    }), 200


@submissions.route('/history/<int:homework_id>', methods=['GET'])
@token_required
def get_submission_history(current_user, homework_id):
    """获取学生的作业提交历史"""
    # 获取查询参数
    student_id = request.args.get('student_id')
    
    # 设置默认值
    if not student_id and current_user.is_student():
        student_id = current_user.id
    
    if not student_id:
        return jsonify({'message': '学生ID为必填项'}), 400
    
    # 权限检查
    if current_user.is_student() and int(student_id) != current_user.id:
        return jsonify({'message': '无权查看其他学生的提交历史'}), 403
    
    if current_user.is_teacher():
        # 确认是否为该作业所属课程的教师
        homework = Homework.query.get(homework_id)
        if not homework:
            return jsonify({'message': '作业不存在'}), 404
        
        course = Course.query.get(homework.course_id)
        if course.teacher_id != current_user.id:
            return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 查询提交历史
    submissions = Submission.query.filter_by(
        homework_id=homework_id,
        student_id=student_id
    ).order_by(Submission.version.desc()).all()
    
    return jsonify({
        'submissions': [sub.to_dict() for sub in submissions]
    }), 200
