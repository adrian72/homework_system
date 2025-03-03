#!/usr/bin/env python
from app import create_app, db
from app.models import User, Course, Homework, Submission, Feedback

# 创建应用实例
app = create_app('development')

# 在应用上下文中创建表
with app.app_context():
    # 创建所有表
    db.create_all()
    
    # 检查是否已有管理员用户
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        # 创建管理员
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.password = 'admin123'  # 设置一个初始密码
        db.session.add(admin)
        
        # 创建测试教师
        teacher = User(username='teacher', email='teacher@example.com', role='teacher')
        teacher.password = 'password'
        db.session.add(teacher)
        
        # 创建测试学生
        student = User(username='student', email='student@example.com', role='student')
        student.password = 'password'
        db.session.add(student)
        
        # 创建示例课程
        course = Course(
            name='Python编程基础',
            description='学习Python编程的基础知识',
            teacher=teacher
        )
        db.session.add(course)
        
        # 添加学生到课程
        course.students.append(student)
        
        # 创建示例作业
        homework1 = Homework(
            title='Python函数作业',
            description='请完成教材第5章的习题',
            course=course,
            assignment_type='essay'
        )
        db.session.add(homework1)
        
        homework2 = Homework(
            title='口语练习',
            description='请朗读教材第3章并录音',
            course=course,
            assignment_type='oral'
        )
        db.session.add(homework2)
        
        db.session.commit()
        print("示例数据创建成功!")
    else:
        print("数据库已包含数据，跳过初始化")

print("数据库初始化完成!")
