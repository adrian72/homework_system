from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from config import config
import os

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth_views.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

def create_app(config_name='default'):
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 初始化扩展
    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)
    CORS(app)
    
    # 导入模型 - 放在这里避免循环导入
    from app.models import User, Course, Homework, Submission, Feedback
    
    # 注册蓝图
    from app.api.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/api/auth')
    
    from app.api.courses import courses as courses_blueprint
    app.register_blueprint(courses_blueprint, url_prefix='/api/courses')
    
    from app.api.homeworks import homeworks as homeworks_blueprint
    app.register_blueprint(homeworks_blueprint, url_prefix='/api/homeworks')
    
    from app.api.submissions import submissions as submissions_blueprint
    app.register_blueprint(submissions_blueprint, url_prefix='/api/submissions')
    
    from app.api.feedback import feedback as feedback_blueprint
    app.register_blueprint(feedback_blueprint, url_prefix='/api/feedback')
    
    from app.api.users import users as users_blueprint
    app.register_blueprint(users_blueprint, url_prefix='/api/users')
    
    from app.api.wordpress import wordpress as wordpress_blueprint
    app.register_blueprint(wordpress_blueprint, url_prefix='/api/wordpress')
    
    # 创建Web路由
    from app.views.auth import auth_views as auth_views_blueprint
    app.register_blueprint(auth_views_blueprint)
    
    from app.views.student import student_views as student_views_blueprint
    app.register_blueprint(student_views_blueprint, url_prefix='/student')
    
    from app.views.teacher import teacher_views as teacher_views_blueprint
    app.register_blueprint(teacher_views_blueprint, url_prefix='/teacher')
    
    from app.views.admin import admin_views as admin_views_blueprint
    app.register_blueprint(admin_views_blueprint, url_prefix='/admin')
    
    # 创建错误处理程序
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    
    # 添加上下文处理器
    @app.context_processor
    def inject_globals():
        """注入全局变量到模板中"""
        from datetime import datetime
        return {
            'now': datetime.now()
        }
    
    return app
