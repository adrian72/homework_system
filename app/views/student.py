# app/views/student.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Course, Homework, Submission, Feedback, User
from datetime import datetime

student_views = Blueprint('student_views', __name__)

# 学生访问权限装饰器
def student_required(f):
    """确保只有学生可以访问"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_student() and not current_user.is_admin():
            flash('无权访问学生页面', 'danger')
            return redirect(url_for('auth_views.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@student_views.route('/dashboard')
@student_required
def dashboard():
    """学生仪表盘页面"""
    # 获取学生课程
    courses = current_user.courses_as_student
    
    # 获取最近作业
    recent_homework_submissions = []
    for course in courses:
        homeworks = Homework.query.filter_by(course_id=course.id).order_by(Homework.due_date.desc()).limit(5).all()
        for homework in homeworks:
            submission = Submission.query.filter_by(
                homework_id=homework.id,
                student_id=current_user.id
            ).order_by(Submission.version.desc()).first()
            
            recent_homework_submissions.append({
                'homework': homework,
                'submission': submission
            })
    
    # 按截止日期排序
    recent_homework_submissions.sort(
        key=lambda x: x['homework'].due_date if x['homework'].due_date else datetime.max,
        reverse=False
    )
    
    # 只保留最近10个
    recent_homework_submissions = recent_homework_submissions[:10]
    
    return render_template('student/dashboard.html', 
                          courses=courses, 
                          recent_homework_submissions=recent_homework_submissions)

@student_views.route('/courses')
@student_required
def courses():
    """学生课程列表页面"""
    # 获取学生课程
    student_courses = current_user.courses_as_student
    
    # 获取可选课程
    available_courses = Course.query.filter(~Course.id.in_([c.id for c in student_courses])).all()
    
    return render_template('student/courses.html', 
                          courses=student_courses,
                          available_courses=available_courses)

@student_views.route('/courses/<int:course_id>')
@student_required
def course_detail(course_id):
    """学生课程详情页面"""
    # 获取课程
    course = Course.query.get_or_404(course_id)
    
    # 确认学生是该课程的成员
    if current_user not in course.students and not current_user.is_admin():
        flash('您不是该课程的学生', 'danger')
        return redirect(url_for('student_views.courses'))
    
    # 获取课程作业
    homeworks = Homework.query.filter_by(course_id=course_id).order_by(Homework.created_at.desc()).all()
    
    # 获取学生提交情况
    homework_submissions = []
    for homework in homeworks:
        submission = Submission.query.filter_by(
            homework_id=homework.id,
            student_id=current_user.id
        ).order_by(Submission.version.desc()).first()
        
        homework_submissions.append({
            'homework': homework,
            'submission': submission
        })
    
    return render_template('student/course_detail.html', 
                          course=course, 
                          homework_submissions=homework_submissions)

@student_views.route('/homeworks/<int:homework_id>')
@student_required
def homework_detail(homework_id):
    """学生作业详情页面"""
    # 获取作业
    homework = Homework.query.get_or_404(homework_id)
    
    # 获取课程
    course = Course.query.get(homework.course_id)
    
    # 确认学生是该课程的成员
    if current_user not in course.students and not current_user.is_admin():
        flash('您不是该课程的学生', 'danger')
        return redirect(url_for('student_views.courses'))
    
    # 获取学生的所有提交
    submissions = Submission.query.filter_by(
        homework_id=homework_id,
        student_id=current_user.id
    ).order_by(Submission.version.desc()).all()
    
    # 获取最新提交
    latest_submission = submissions[0] if submissions else None
    
    # 获取反馈
    feedbacks = []
    if latest_submission:
        feedbacks = Feedback.query.filter_by(
            submission_id=latest_submission.id
        ).order_by(Feedback.created_at.desc()).all()
    
    return render_template('student/homework_detail.html',
                          homework=homework,
                          course=course,
                          submissions=submissions,
                          latest_submission=latest_submission,
                          feedbacks=feedbacks)

@student_views.route('/homeworks/<int:homework_id>/submit', methods=['GET', 'POST'])
@student_required
def submit_homework(homework_id):
    """提交作业页面"""
    # 获取作业
    homework = Homework.query.get_or_404(homework_id)
    
    # 获取课程
    course = Course.query.get(homework.course_id)
    
    # 确认学生是该课程的成员
    if current_user not in course.students and not current_user.is_admin():
        flash('您不是该课程的学生', 'danger')
        return redirect(url_for('student_views.courses'))
    
    # 检查截止日期
    if homework.due_date and homework.due_date < datetime.now():
        flash('作业已过截止日期，无法提交', 'warning')
        return redirect(url_for('student_views.homework_detail', homework_id=homework_id))
    
    # 获取之前的提交
    prev_submission = Submission.query.filter_by(
        homework_id=homework_id,
        student_id=current_user.id
    ).order_by(Submission.version.desc()).first()
    
    # 设置版本号
    version = 1
    if prev_submission:
        version = prev_submission.version + 1
    
    if request.method == 'POST':
        # 处理提交
        comment = request.form.get('comment', '')
        
        # 创建提交记录
        submission = Submission(
            homework_id=homework_id,
            student_id=current_user.id,
            comment=comment,
            version=version,
            status='submitted'
        )
        
        # 处理上传的文件和内容
        content_data = {}
        
        # 根据作业类型处理不同的上传
        if homework.assignment_type == 'essay':
            # 处理文本内容
            text_content = request.form.get('text_content', '')
            if text_content:
                content_data['text'] = text_content
            
            # 处理图像上传
            if 'essay_images' in request.files:
                from app.utils.file_handler import save_file
                
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
                from app.utils.file_handler import save_file
                
                audio = request.files['oral_audio']
                if audio.filename:
                    file_info = save_file(audio, 'audio')
                    if file_info:
                        content_data['audio'] = file_info
        
        # 设置内容
        submission.content_data = content_data
        
        db.session.add(submission)
        db.session.commit()
        
        flash('作业提交成功', 'success')
        return redirect(url_for('student_views.homework_detail', homework_id=homework_id))
    
    return render_template('student/submit_homework.html',
                          homework=homework,
                          course=course,
                          prev_submission=prev_submission)

@student_views.route('/submissions/<int:submission_id>')
@student_required
def view_submission(submission_id):
    """查看提交详情页面"""
    # 获取提交
    submission = Submission.query.get_or_404(submission_id)
    
    # 确认学生是提交的所有者
    if submission.student_id != current_user.id and not current_user.is_admin():
        flash('无权查看该提交', 'danger')
        return redirect(url_for('student_views.dashboard'))
    
    # 获取作业和课程
    homework = Homework.query.get(submission.homework_id)
    course = Course.query.get(homework.course_id)
    
    # 获取反馈
    feedbacks = Feedback.query.filter_by(
        submission_id=submission_id
    ).order_by(Feedback.created_at.desc()).all()
    
    return render_template('student/view_submission.html',
                          submission=submission,
                          homework=homework,
                          course=course,
                          feedbacks=feedbacks)

@student_views.route('/courses/enroll/<int:course_id>', methods=['POST'])
@student_required
def enroll_course(course_id):
    """选课"""
    # 获取课程
    course = Course.query.get_or_404(course_id)
    
    # 检查是否已选课
    if current_user in course.students:
        flash('您已经选修了该课程', 'warning')
        return redirect(url_for('student_views.courses'))
    
    # 添加学生到课程
    course.students.append(current_user)
    db.session.commit()
    
    flash(f'成功选修课程: {course.name}', 'success')
    return redirect(url_for('student_views.courses'))

@student_views.route('/courses/unenroll/<int:course_id>', methods=['POST'])
@student_required
def unenroll_course(course_id):
    """退选课程"""
    # 获取课程
    course = Course.query.get_or_404(course_id)
    
    # 检查是否已选课
    if current_user not in course.students:
        flash('您未选修该课程', 'warning')
        return redirect(url_for('student_views.courses'))
    
    # 从课程中移除学生
    course.students.remove(current_user)
    db.session.commit()
    
    flash(f'成功退选课程: {course.name}', 'success')
    return redirect(url_for('student_views.courses'))
