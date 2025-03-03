#!/bin/bash
# 脚本：fix_path_issues.sh
# 用途：修复代码中的硬编码路径和数据库配置问题

# 确保当前目录是项目根目录
if [ ! -f "manage.py" ] || [ ! -d "app" ]; then
    echo "错误：请在项目根目录中运行此脚本"
    exit 1
fi

echo "开始修复路径问题..."

# 修复config.py中的数据库路径
echo "修复config.py中的数据库配置..."
sed -i.bak 's|sqlite:////Users/oliver/Desktop/homework_system/instance/dev.sqlite|sqlite:///instance/dev.sqlite|g' config.py
if [ $? -eq 0 ]; then echo "✓ 成功修复config.py"; else echo "× 修复config.py失败"; fi

# 修复create_db.py中的数据库路径
echo "修复create_db.py中的数据库配置..."
sed -i.bak 's|app.config\['"'"'SQLALCHEMY_DATABASE_URI'"'"'\] = '"'"'sqlite:///instance/dev.sqlite'"'"'|app.config\['"'"'SQLALCHEMY_DATABASE_URI'"'"'\] = '"'"'sqlite:///'"'"' + os.path.join(os.path.dirname(os.path.abspath(__file__)), '"'"'instance/dev.sqlite'"'"')|g' create_db.py
if [ $? -eq 0 ]; then echo "✓ 成功修复create_db.py"; else echo "× 修复create_db.py失败"; fi

# 修复initialize_db.py中的数据库路径
echo "修复initialize_db.py中的数据库配置..."
sed -i.bak 's|app.config\['"'"'SQLALCHEMY_DATABASE_URI'"'"'\] = '"'"'sqlite:////Users/oliver/Desktop/homework_system/instance/dev.sqlite'"'"'|app.config\['"'"'SQLALCHEMY_DATABASE_URI'"'"'\] = '"'"'sqlite:///'"'"' + os.path.join(os.path.dirname(os.path.abspath(__file__)), '"'"'instance/dev.sqlite'"'"')|g' initialize_db.py
if [ $? -eq 0 ]; then echo "✓ 成功修复initialize_db.py"; else echo "× 修复initialize_db.py失败"; fi

# 修复fix_imports.sh和fix_view_imports.sh中的绝对路径
echo "修复导入脚本中的绝对路径..."
sed -i.bak 's|cd /Users/oliver/Desktop/homework_system|cd $(dirname "$0")|g' fix_imports.sh fix_view_imports.sh
if [ $? -eq 0 ]; then echo "✓ 成功修复导入脚本"; else echo "× 修复导入脚本失败"; fi

# 修复app/__init__.py中的动态路径处理
echo "确保app/__init__.py中使用动态路径..."
cat > app/__init__.py.new << 'EOF'
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
EOF
mv app/__init__.py.new app/__init__.py
echo "✓ 成功更新app/__init__.py"

# 确保使用相对路径
echo "创建instance目录（如果不存在）..."
mkdir -p instance

echo "修复完成！"
echo "请检查修改并测试系统功能。"
