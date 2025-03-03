# app/views/teacher.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Course, Homework, Submission, Feedback, User
from datetime import datetime, timedelta

teacher_views = Blueprint('teacher_views', __name__)

# 教师访问权限装饰器
def teacher_required(f):
    """确保只有教师可以访问"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_teacher() and not current_user.is_admin():
            flash('无权访问教师页面', 'danger')
            return redirect(url_for('auth_views.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@teacher_views.route('/dashboard')
@teacher_required
def dashboard():
    """教师仪表盘页面"""
    # 获取教师课程
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    
    # 统计信息
    total_students = 0
    total_homeworks = 0
    total_submissions = 0
    recent_submissions = []
    
    for course in courses:
        # 学生数量
        total_students += course.students.count()
        
        # 作业数量
        homeworks = Homework.query.filter_by(course_id=course.id).all()
        total_homeworks += len(homeworks)
        
        # 作业提交
        for homework in homeworks:
            submissions = Submission.query.filter_by(homework_id=homework.id).all()
            total_submissions += len(submissions)
            
            # 最近未批改的提交
            ungraded_submissions = Submission.query.filter_by(
                homework_id=homework.id,
                status='submitted'
            ).order_by(Submission.created_at.desc()).all()
            
            for submission in ungraded_submissions:
                student = User.query.get(submission.student_id)
                recent_submissions.append({
                    'homework': homework,
                    'submission': submission,
                    'student': student,
                    'course': course
                })
    
    # 按提交时间排序
    recent_submissions.sort(key=lambda x: x['submission'].created_at, reverse=True)
    
    # 只显示前10个
    recent_submissions = recent_submissions[:10]
    
    # 最近7天内的提交统计
    today = datetime.now().date()
    submission_stats = []
    
    for i in range(7):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        day_submissions = 0
        for course in courses:
            homeworks = Homework.query.filter_by(course_id=course.id).all()
            for homework in homeworks:
                day_submissions += Submission.query.filter(
                    Submission.homework_id == homework.id,
                    Submission.created_at >= day_start,
                    Submission.created_at <= day_end
                ).count()
        
        submission_stats.append({
            'date': day.strftime('%m-%d'),
            'count': day_submissions
        })
    
    # 反转列表使日期按升序排列
    submission_stats.reverse()
    
    return render_template('teacher/dashboard.html', 
                          courses=courses,
                          total_students=total_students,
                          total_homeworks=total_homeworks,
                          total_submissions=total_submissions,
                          recent_submissions=recent_submissions,
                          submission_stats=submission_stats)

@teacher_views.route('/courses')
@teacher_required
def courses():
    """教师课程列表页面"""
    # 获取教师课程
    teacher_courses = Course.query.filter_by(teacher_id=current_user.id).all()
    
    return render_template('teacher/courses.html', courses=teacher_courses)

@teacher_views.route('/courses/create', methods=['GET', 'POST'])
@teacher_required
def create_course():
    """创建课程页面"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not name:
            flash('课程名称为必填项', 'danger')
            return redirect(url_for('teacher_views.create_course'))
        
        # 创建课程
        course = Course(
            name=name,
            description=description,
            teacher_id=current_user.id
        )
        
        # 处理日期
        if start_date:
            try:
                course.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                flash('开始日期格式不正确', 'danger')
                return redirect(url_for('teacher_views.create_course'))
        
        if end_date:
            try:
                course.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                flash('结束日期格式不正确', 'danger')
                return redirect(url_for('teacher_views.create_course'))
        
        # 处理封面图片
        if 'cover_image' in request.files:
            from app.utils.file_handler import save_file
            
            cover_image = request.files['cover_image']
            if cover_image.filename:
                file_info = save_file(cover_image, 'image')
                if file_info:
                    course.cover_image = file_info['url']
        
        db.session.add(course)
        db.session.commit()
        
        flash('课程创建成功', 'success')
        return redirect(url_for('teacher_views.courses'))
    
    return render_template('teacher/create_course.html')

@teacher_views.route('/courses/<int:course_id>')
@teacher_required
def course_detail(course_id):
    """教师课程详情页面"""
    # 获取课程
    course = Course.query.get_or_404(course_id)
    
    # 确认是否为课程教师
    if course.teacher_id != current_user.id and not current_user.is_admin():
        flash('您不是该课程的教师', 'danger')
        return redirect(url_for('teacher_views.courses'))
    
    # 获取课程作业
    homeworks = Homework.query.filter_by(course_id=course_id).order_by(Homework.created_at.desc()).all()
    
    # 获取课程学生
    students = course.students.all()
    
    # 统计信息
    homework_stats = []
    for homework in homeworks:
        submissions = Submission.query.filter_by(homework_id=homework.id).all()
        submitted_students = set()
        
        for submission in submissions:
            submitted_students.add(submission.student_id)
        
        homework_stats.append({
            'homework': homework,
            'submission_count': len(submissions),
            'submitted_students': len(submitted_students),
            'submission_rate': len(submitted_students) / len(students) if students else 0
        })
    
    return render_template('teacher/course_detail.html', 
                          course=course, 
                          homeworks=homeworks,
                          students=students,
                          homework_stats=homework_stats)

@teacher_views.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_course(course_id):
    """编辑课程页面"""
    # 获取课程
    course = Course.query.get_or_404(course_id)
    
    # 确认是否为课程教师
    if course.teacher_id != current_user.id and not current_user.is_admin():
        flash('您不是该课程的教师', 'danger')
        return redirect(url_for('teacher_views.courses'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not name:
            flash('课程名称为必填项', 'danger')
            return redirect(url_for('teacher_views.edit_course', course_id=course_id))
        
        # 更新课程信息
        course.name = name
        course.description = description
        
        # 处理日期
        if start_date:
            try:
                course.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                flash('开始日期格式不正确', 'danger')
                return redirect(url_for('teacher_views.edit_course', course_id=course_id))
        else:
            course.start_date = None
        
        if end_date:
            try:
                course.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                flash('结束日期格式不正确', 'danger')
                return redirect(url_for('teacher_views.edit_course', course_id=course_id))
        else:
            course.end_date = None
        
        # 处理封面图片
        if 'cover_image' in request.files:
            from app.utils.file_handler import save_file, delete_file
            
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
        
        flash('课程更新成功', 'success')
        return redirect(url_for('teacher_views.course_detail', course_id=course_id))
    
    # 格式化日期以符合HTML日期输入
    start_date_str = course.start_date.strftime('%Y-%m-%d') if course.start_date else ''
    end_date_str = course.end_date.strftime('%Y-%m-%d') if course.end_date else ''
    
    return render_template('teacher/edit_course.html', 
                          course=course,
                          start_date=start_date_str,
                          end_date=end_date_str)

@teacher_views.route('/courses/<int:course_id>/students')
@teacher_required
def course_students(course_id):
    """课程学生管理页面"""
    # 获取课程
    course = Course.query.get_or_404(course_id)
    
    # 确认是否为课程教师
    if course.teacher_id != current_user.id and not current_user.is_admin():
        flash('您不是该课程的教师', 'danger')
        return redirect(url_for('teacher_views.courses'))
    
    # 获取课程学生
    students = course.students.all()
    
    # 获取可添加的学生
    all_students = User.query.filter_by(role='student').all()
    available_students = [s for s in all_students if s not in students]
    
    return render_template('teacher/course_students.html',
                          course=course,
                          students=students,
                          available_students=available_students)

@teacher_views.route('/courses/<int:course_id>/add_student', methods=['POST'])
@teacher_required
def add_student(course_id):
    """添加学生到课程"""
    # 获取课程
    course = Course.query.get_or_404(course_id)
    
    # 确认是否为课程教师
    if course.teacher_id != current_user.id and not current_user.is_admin():
        flash('您不是该课程的教师', 'danger')
        return redirect(url_for('teacher_views.courses'))
    
    # 获取要添加的学生ID
    student_id = request.form.get('student_id')
    
    if not student_id:
        flash('请选择要添加的学生', 'danger')
        return redirect(url_for('teacher_views.course_students', course_id=course_id))
    
    # 获取学生
    student = User.query.get_or_404(student_id)
    
    # 确认学生角色
    if student.role != 'student':
        flash('只能添加学生角色用户', 'danger')
        return redirect(url_for('teacher_views.course_students', course_id=course_id))
    
    # 检查学生是否已在课程中
    if student in course.students:
        flash('该学生已在课程中', 'warning')
        return redirect(url_for('teacher_views.course_students', course_id=course_id))
    
    # 添加学生到课程
    course.students.append(student)
    db.session.commit()
    
    flash(f'学生 {student.real_name or student.username} 已成功添加到课程', 'success')
    return redirect(url_for('teacher_views.course_students', course_id=course_id))

@teacher_views.route('/courses/<int:course_id>/remove_student', methods=['POST'])
@teacher_required
def remove_student(course_id):
    """从课程中移除学生"""
    # 获取课程
    course = Course.query.get_or_404(course_id)
    
    # 确认是否为课程教师
    if course.teacher_id != current_user.id and not current_user.is_admin():
        flash('您不是该课程的教师', 'danger')
        return redirect(url_for('teacher_views.courses'))
    
    # 获取要移除的学生ID
    student_id = request.form.get('student_id')
    
    if not student_id:
        flash('请选择要移除的学生', 'danger')
        return redirect(url_for('teacher_views.course_students', course_id=course_id))
    
    # 获取学生
    student = User.query.get_or_404(student_id)
    
    # 检查学生是否在课程中
    if student not in course.students:
        flash('该学生不在课程中', 'warning')
        return redirect(url_for('teacher_views.course_students', course_id=course_id))
    
    # 移除学生
    course.students.remove(student)
    db.session.commit()
    
    flash(f'学生 {student.real_name or student.username} 已成功从课程中移除', 'success')
    return redirect(url_for('teacher_views.course_students', course_id=course_id))

@teacher_views.route('/homeworks/create', methods=['GET', 'POST'])
@teacher_required
def create_homework():
    """创建作业页面"""
    # 获取教师的所有课程
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        title = request.form.get('title')
        description = request.form.get('description', '')
        deadline = request.form.get('deadline')
        
        # 验证必填项
        if not course_id or not title:
            flash('课程和作业标题为必填项', 'danger')
            return redirect(url_for('teacher_views.create_homework'))
        
        # 获取课程
        course = Course.query.get_or_404(course_id)
        
        # 验证课程归属
        if course.teacher_id != current_user.id and not current_user.is_admin():
            flash('您没有权限为此课程创建作业', 'danger')
            return redirect(url_for('teacher_views.courses'))
        
        # 创建作业
        homework = Homework(
            course_id=course_id,
            title=title,
            description=description
        )
        
        # 处理截止日期
        if deadline:
            try:
                homework.deadline = datetime.strptime(deadline, '%Y-%m-%d %H:%M')
            except ValueError:
                flash('截止日期格式不正确', 'danger')
                return redirect(url_for('teacher_views.create_homework'))
        
        # 处理附件
        if 'attachment' in request.files:
            from app.utils.file_handler import save_file
            
            attachment = request.files['attachment']
            if attachment.filename:
                file_info = save_file(attachment, 'homework')
                if file_info:
                    homework.attachment = file_info['url']
        
        db.session.add(homework)
        db.session.commit()
        
        flash('作业创建成功', 'success')
        return redirect(url_for('teacher_views.course_detail', course_id=course_id))
    
    return render_template('teacher/create_homework.html', courses=courses)

@teacher_views.route('/homeworks/<int:homework_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_homework(homework_id):
    """编辑作业页面"""
    # 获取作业
    homework = Homework.query.get_or_404(homework_id)
    
    # 获取教师的所有课程
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    
    # 验证课程归属
    if homework.course.teacher_id != current_user.id and not current_user.is_admin():
        flash('您没有权限编辑此作业', 'danger')
        return redirect(url_for('teacher_views.courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        deadline = request.form.get('deadline')
        course_id = request.form.get('course_id')
        
        # 验证必填项
        if not title:
            flash('作业标题为必填项', 'danger')
            return redirect(url_for('teacher_views.edit_homework', homework_id=homework_id))
        
        # 更新基本信息
        homework.title = title
        homework.description = description
        homework.course_id = course_id
        
        # 处理截止日期
        if deadline:
            try:
                homework.deadline = datetime.strptime(deadline, '%Y-%m-%d %H:%M')
            except ValueError:
                flash('截止日期格式不正确', 'danger')
                return redirect(url_for('teacher_views.edit_homework', homework_id=homework_id))
        else:
            homework.deadline = None
        
        # 处理新附件
        if 'attachment' in request.files:
            from app.utils.file_handler import save_file, delete_file
            
            attachment = request.files['attachment']
            if attachment.filename:
                # 删除旧附件
                if homework.attachment:
                    old_path = homework.attachment.replace('/static/uploads/', '')
                    delete_file(old_path)
                
                # 保存新附件
                file_info = save_file(attachment, 'homework')
                if file_info:
                    homework.attachment = file_info['url']
        
        db.session.commit()
        
        flash('作业更新成功', 'success')
        return redirect(url_for('teacher_views.course_detail', course_id=course_id))
    
    # 格式化截止日期
    deadline_str = homework.deadline.strftime('%Y-%m-%d %H:%M') if homework.deadline else ''
    
    return render_template('teacher/edit_homework.html', 
                          homework=homework, 
                          courses=courses,
                          deadline=deadline_str)

@teacher_views.route('/homeworks/<int:homework_id>/submissions')
@teacher_required
def homework_submissions(homework_id):
    """查看作业提交情况"""
    # 获取作业
    homework = Homework.query.get_or_404(homework_id)
    
    # 验证课程归属
    if homework.course.teacher_id != current_user.id and not current_user.is_admin():
        flash('您没有权限查看此作业的提交情况', 'danger')
        return redirect(url_for('teacher_views.courses'))
    
    # 获取所有提交
    submissions = Submission.query.filter_by(homework_id=homework_id).all()
    
    # 准备提交数据
    submission_data = []
    for submission in submissions:
        student = User.query.get(submission.student_id)
        submission_data.append({
            'submission': submission,
            'student': student
        })
    
    return render_template('teacher/homework_submissions.html', 
                          homework=homework, 
                          submissions=submission_data)

@teacher_views.route('/submissions/<int:submission_id>/grade', methods=['GET', 'POST'])
@teacher_required
def grade_submission(submission_id):
    """给作业提交评分"""
    # 获取提交
    submission = Submission.query.get_or_404(submission_id)
    
    # 验证课程归属
    if submission.homework.course.teacher_id != current_user.id and not current_user.is_admin():
        flash('您没有权限评分此提交', 'danger')
        return redirect(url_for('teacher_views.courses'))
    
    if request.method == 'POST':
        score = request.form.get('score')
        comments = request.form.get('comments', '')
        
        # 验证分数
        try:
            score = float(score)
        except (ValueError, TypeError):
            flash('分数必须是数字', 'danger')
            return redirect(url_for('teacher_views.grade_submission', submission_id=submission_id))
        
        # 创建或更新反馈
        feedback = Feedback.query.filter_by(submission_id=submission_id).first()
        if not feedback:
            feedback = Feedback(submission_id=submission_id)
            db.session.add(feedback)
        
        feedback.score = score
        feedback.comments = comments
        feedback.graded_at = datetime.now()
        
        # 更新提交状态
        submission.status = 'graded'
        
        db.session.commit()
        
        flash('作业评分成功', 'success')
        return redirect(url_for('teacher_views.homework_submissions', homework_id=submission.homework_id))
    
    return render_template('teacher/grade_submission.html', submission=submission)
