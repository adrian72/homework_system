# config.py
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置"""
    # 项目根目录
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app/static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg'}
    
    # 安全配置
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() in ['true', 'on', '1']
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = 3600 * 24 * 7  # 7天
    
    # WordPress API配置
    WP_API_URL = os.environ.get('WP_API_URL')
    WP_API_USER = os.environ.get('WP_API_USER')
    WP_API_PASSWORD = os.environ.get('WP_API_PASSWORD')
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    
    @staticmethod
    def init_app(app):
        """初始化应用"""
        # 创建上传目录
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # 创建日志目录
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        
        # 配置日志
        import logging
        from logging.handlers import RotatingFileHandler
        
        handler = RotatingFileHandler(
            os.path.join(Config.LOG_DIR, 'app.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d - %(message)s'
        )
        
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        
        log_level = getattr(logging, Config.LOG_LEVEL)
        app.logger.setLevel(log_level)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(Config.BASE_DIR, 'instance/dev.sqlite')
    
    # 开发环境可以关闭某些安全限制
    SESSION_COOKIE_SECURE = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 开发环境特定日志配置
        import logging
        app.logger.setLevel(logging.DEBUG)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d - %(message)s'
        ))
        app.logger.addHandler(console_handler)


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite://'
    WTF_CSRF_ENABLED = False
    
    # 测试环境禁用WordPress集成
    WP_API_URL = None
    WP_API_USER = None
    WP_API_PASSWORD = None


class ProductionConfig(Config):
    """生产环境配置"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:postgres@db:5432/homework_system'
    
    # 生产环境额外安全配置
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 生产环境特定日志配置
        import logging
        from logging.handlers import SMTPHandler
        
        # 如果配置了邮件，添加邮件错误处理器
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_DEFAULT_SENDER,
            toaddrs=[os.environ.get('ADMIN_EMAIL', 'admin@example.com')],
            subject='应用错误',
            credentials=(cls.MAIL_USERNAME, cls.MAIL_PASSWORD),
            secure=() if cls.MAIL_USE_TLS else None
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


# 配置映射
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}