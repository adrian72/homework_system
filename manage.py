#!/usr/bin/env python
import os
import click
from flask_migrate import Migrate
from app import create_app, db
from app.models import User, Course, Homework, Submission, Feedback

# 创建应用实例
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """为Flask shell命令添加上下文"""
    return dict(
        app=app, db=db, User=User, Course=Course,
        Homework=Homework, Submission=Submission, Feedback=Feedback
    )

@app.cli.command()
def test():
    """运行单元测试"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@app.cli.command()
@click.option('--username', prompt=True, help='管理员用户名')
@click.option('--email', prompt=True, help='管理员邮箱')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='管理员密码')
def create_admin(username, email, password):
    """创建管理员账户"""
    # 检查用户名和邮箱是否已存在
    if User.query.filter_by(username=username).first():
        click.echo('用户名已被使用')
        return
    
    if User.query.filter_by(email=email).first():
        click.echo('邮箱已被注册')
        return
    
    # 创建管理员
    admin = User(username=username, email=email, role='admin')
    admin.password = password
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo('管理员创建成功')

@app.cli.command()
def init_db():
    """初始化数据库并创建测试数据"""
    db.create_all()
    
    # 检查是否已有数据
    if User.query.first():
        click.echo('数据库已包含数据，跳过初始化')
        return
    
    # 创建管理员
    admin = User(username='admin', email='admin@example.com', role='admin')
    admin.password = 'password'
    db.session.add(admin)
    
    # 创建教师
    teacher = User(username='teacher', email='teacher@example.com', role='teacher')
    teacher.password = 'password'
    db.session.add(teacher)
    
    # 创建学生
    student = User(username='student', email='student@example.com', role='student')
    student.password = 'password'
    db.session.add(student)
    
    # 创建课程
    course = Course(
        name='Python编程基础',
        description='学习Python编程的基础知识',
        teacher=teacher
    )
    db.session.add(course)
    
    # 添加学生到课程
    course.students.append(student)
    
    # 创建作业
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
    
    click.echo('测试数据创建成功')

if __name__ == '__main__':
    app.run()
