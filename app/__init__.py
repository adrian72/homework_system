from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from .utils.filters import nl2br
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name='default'):
    # 创建 Flask 应用实例
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # 注册蓝图
    from .views import student_bp, teacher_bp, admin_bp, main_bp
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)

    # 注册自定义过滤器
    app.jinja_env.filters['nl2br'] = nl2br

    # 设置登录视图
    login_manager.login_view = 'auth.login'

    return app
