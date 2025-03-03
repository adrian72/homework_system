# app/api/feedback.py
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Submission, Feedback, Homework, Course
from app.utils.auth import token_required, teacher_required
from app.utils.file_handler import save_file
import json

feedback = Blueprint('feedback', __name__)

@feedback.route('/', methods=['POST'])
@teacher_required
def create_feedback(current_user):
    """创建新的作业反馈（教师）"""
    # 获取提交ID
    submission_id = request.form.get('submission_id')
    if not submission_id:
        return jsonify({'message': '提交ID为必填项'}), 400
    
    # 查找提交
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({'message': '提交不存在'}), 404
    
    # 确认是否为该作业所属课程的教师
    homework = Homework.query.get(submission.homework_id)
    course = Course.query.get(homework.course_id)
    if course.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 获取反馈内容
    score = request.form.get('score')
    comments = request.form.get('comments', '')
    requires_revision = request.form.get('requires_revision', 'false').lower() == 'true'
    
    # 验证分数
    if score is not None:
        try:
            score = float(score)
            if score < 0 or score > 100:
                return jsonify({'message': '分数必须在0-100之间'}), 400
        except ValueError:
            return jsonify({'message': '分数格式不正确'}), 400
    
    # 处理上传的文件
    content_data = {}
    
    # 处理图像上传
    if 'feedback_images' in request.files:
        images = request.files.getlist('feedback_images')
        image_data = []
        for img in images:
            if img.filename:
                file_info = save_file(img, 'image')
                if file_info:
                    image_data.append(file_info)
        
        if image_data:
            content_data['images'] = image_data
    
    # 处理音频上传
    if 'feedback_audio' in request.files:
        audio = request.files['feedback_audio']
        if audio.filename:
            file_info = save_file(audio, 'audio')
            if file_info:
                content_data['audio'] = file_info
    
    # 处理文本内容
    text_content = request.form.get('text_content', '')
    if text_content:
        content_data['text'] = text_content
    
    # 创建反馈记录
    feedback = Feedback(
        submission_id=submission_id,
        teacher_id=current_user.id,
        score=score,
        comments=comments,
        requires_revision=requires_revision
    )
    
    # 设置内容
    feedback.content_data = content_data
    
    # 更新提交状态
    if requires_revision:
        submission.status = 'needs_revision'
    else:
        submission.status = 'graded'
    
    db.session.add(feedback)
    db.session.commit()
    
    return jsonify({
        'message': '反馈创建成功',
        'feedback': feedback.to_dict()
    }), 201


@feedback.route('/<int:feedback_id>', methods=['GET'])
@token_required
def get_feedback(current_user, feedback_id):
    """获取特定反馈"""
    # 查找反馈
    feedback = Feedback.query.get(feedback_id)
    if not feedback:
        return jsonify({'message': '反馈不存在'}), 404
    
    # 获取相关提交
    submission = Submission.query.get(feedback.submission_id)
    
    # 权限检查
    if current_user.is_student():
        # 学生只能查看自己的作业反馈
        if submission.student_id != current_user.id:
            return jsonify({'message': '无权查看该反馈'}), 403
    
    elif current_user.is_teacher():
        # 确认是否为该作业所属课程的教师
        homework = Homework.query.get(submission.homework_id)
        course = Course.query.get(homework.course_id)
        if course.teacher_id != current_user.id:
            return jsonify({'message': '您不是该课程的教师'}), 403
    
    return jsonify({
        'feedback': feedback.to_dict()
    }), 200


@feedback.route('/submission/<int:submission_id>', methods=['GET'])
@token_required
def get_submission_feedback(current_user, submission_id):
    """获取提交的所有反馈"""
    # 查找提交
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({'message': '提交不存在'}), 404
    
    # 权限检查
    if current_user.is_student():
        # 学生只能查看自己的作业反馈
        if submission.student_id != current_user.id:
            return jsonify({'message': '无权查看该反馈'}), 403
    
    elif current_user.is_teacher():
        # 确认是否为该作业所属课程的教师
        homework = Homework.query.get(submission.homework_id)
        course = Course.query.get(homework.course_id)
        if course.teacher_id != current_user.id:
            return jsonify({'message': '您不是该课程的教师'}), 403
    
    # 获取反馈列表
    feedbacks = Feedback.query.filter_by(submission_id=submission_id).order_by(Feedback.created_at.desc()).all()
    
    return jsonify({
        'feedbacks': [f.to_dict() for f in feedbacks]
    }), 200


@feedback.route('/<int:feedback_id>', methods=['PUT'])
@teacher_required
def update_feedback(current_user, feedback_id):
    """更新反馈（教师）"""
    # 查找反馈
    feedback = Feedback.query.get(feedback_id)
    if not feedback:
        return jsonify({'message': '反馈不存在'}), 404
    
    # 权限检查
    if feedback.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '无权修改该反馈'}), 403
    
    # 获取反馈内容
    data = request.get_json()
    
    # 更新字段
    if 'score' in data:
        try:
            score = float(data['score'])
            if score < 0 or score > 100:
                return jsonify({'message': '分数必须在0-100之间'}), 400
            feedback.score = score
        except ValueError:
            return jsonify({'message': '分数格式不正确'}), 400
    
    if 'comments' in data:
        feedback.comments = data['comments']
    
    if 'requires_revision' in data:
        feedback.requires_revision = bool(data['requires_revision'])
        
        # 更新提交状态
        submission = Submission.query.get(feedback.submission_id)
        if feedback.requires_revision:
            submission.status = 'needs_revision'
        else:
            submission.status = 'graded'
    
    if 'content' in data:
        feedback.content_data = data['content']
    
    db.session.commit()
    
    return jsonify({
        'message': '反馈更新成功',
        'feedback': feedback.to_dict()
    }), 200


@feedback.route('/<int:feedback_id>', methods=['DELETE'])
@teacher_required
def delete_feedback(current_user, feedback_id):
    """删除反馈（教师）"""
    # 查找反馈
    feedback = Feedback.query.get(feedback_id)
    if not feedback:
        return jsonify({'message': '反馈不存在'}), 404
    
    # 权限检查
    if feedback.teacher_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': '无权删除该反馈'}), 403
    
    # 删除反馈
    db.session.delete(feedback)
    db.session.commit()
    
    return jsonify({
        'message': '反馈删除成功'
    }), 200
