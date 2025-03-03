from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
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

   return app
