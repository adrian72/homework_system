#!/usr/bin/env python
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 创建一个最小化的Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/dev.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-key'

# 初始化数据库
db = SQLAlchemy(app)

# 定义基本模型
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='student')
    wp_user_id = db.Column(db.Integer, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)

# 使用上下文创建表
with app.app_context():
    # 创建数据库表
    db.create_all()
    
    # 添加管理员用户
    from werkzeug.security import generate_password_hash
    admin = User(
        username='admin',
        email='admin@example.com',
        role='admin',
        password_hash=generate_password_hash('admin123')
    )
    
    # 检查是否已存在
    existing_admin = User.query.filter_by(username='admin').first()
    if not existing_admin:
        db.session.add(admin)
        db.session.commit()
        print("管理员用户创建成功!")
    else:
        print("管理员用户已存在")

print("数据库初始化完成!")
print(f"数据库文件位置: {os.path.abspath('instance/dev.sqlite')}")
