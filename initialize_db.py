#!/usr/bin/env python
import os
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# 创建Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/oliver/Desktop/homework_system/instance/dev.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-key'

# 初始化SQLAlchemy
db = SQLAlchemy(app)

# 定义模型
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='student')
    wp_user_id = db.Column(db.Integer, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系将在创建其他表后设置

# 学生-课程多对多关系表
student_courses = db.Table('student_courses',
    db.Column('student_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    cover_image = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Homework(db.Model):
    __tablename__ = 'homeworks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    assignment_type = db.Column(db.String(20), nullable=False)  # 'essay', 'oral'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homeworks.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)  # JSON存储文件路径等信息
    comment = db.Column(db.Text, nullable=True)
    version = db.Column(db.Integer, default=1)  # 版本号，支持多次提交
    status = db.Column(db.String(20), default='submitted')  # submitted, graded, needs_revision, revised
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Float, nullable=True)
    comments = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)  # JSON存储反馈内容，包括图片、音频等
    requires_revision = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 设置关系
User.courses_as_student = db.relationship('Course', secondary=student_courses, backref=db.backref('students', lazy='dynamic'))
User.courses_as_teacher = db.relationship('Course', backref='teacher', foreign_keys=[Course.teacher_id])
User.submissions = db.relationship('Submission', backref='student', lazy='dynamic', foreign_keys=[Submission.student_id])
User.feedbacks = db.relationship('Feedback', backref='teacher', lazy='dynamic', foreign_keys=[Feedback.teacher_id])
Course.homeworks = db.relationship('Homework', backref='course', lazy='dynamic', cascade='all, delete-orphan')
Homework.submissions = db.relationship('Submission', backref='homework', lazy='dynamic', cascade='all, delete-orphan')
Submission.feedback = db.relationship('Feedback', backref='submission', lazy='dynamic', cascade='all, delete-orphan')

with app.app_context():
    # 创建所有表
    db.create_all()
    
    # 检查是否已有用户
    if User.query.count() == 0:
        # 创建管理员
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)
        
        # 创建教师
        teacher = User(
            username='teacher',
            email='teacher@example.com',
            role='teacher',
            password_hash=generate_password_hash('password')
        )
        db.session.add(teacher)
        
        # 创建学生
        student = User(
            username='student',
            email='student@example.com',
            role='student',
            password_hash=generate_password_hash('password')
        )
        db.session.add(student)
        
        # 提交创建用户
        db.session.commit()
        print("用户创建成功")
        
        # 创建课程
        course = Course(
            name='Python编程基础',
            description='学习Python编程的基础知识',
            teacher_id=teacher.id
        )
        db.session.add(course)
        
        # 添加学生到课程
        course.students.append(student)
        
        # 提交课程和关系
        db.session.commit()
        print("课程创建成功")
        
        # 创建作业
        homework1 = Homework(
            title='Python函数作业',
            description='请完成教材第5章的习题',
            course_id=course.id,
            assignment_type='essay'
        )
        db.session.add(homework1)
        
        homework2 = Homework(
            title='口语练习',
            description='请朗读教材第3章并录音',
            course_id=course.id,
            assignment_type='oral'
        )
        db.session.add(homework2)
        
        # 提交作业
        db.session.commit()
        print("作业创建成功")
        
        print("\n示例数据创建成功!")
    else:
        print("数据库已包含数据，跳过初始化")

print("数据库初始化完成!")
