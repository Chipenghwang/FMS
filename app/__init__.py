from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
# from flask_babel import Babel
from config import Config

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
# babel = Babel()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    # babel.init_app(app)
    
    # 配置登录管理器
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面。'
    login_manager.login_message_category = 'info'
    
    # 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # # Babel语言选择器
    # @babel.locale_selector
    # def get_locale():
    #     # 1. 如果URL参数中有lang，使用它
    #     if request.args.get('lang'):
    #         session['language'] = request.args.get('lang')
        
    #     # 2. 如果session中有语言设置，使用它
    #     if 'language' in session:
    #         return session['language']
        
    #     # 3. 使用浏览器偏好语言
    #     return request.accept_languages.best_match(app.config['LANGUAGES']) or app.config['BABEL_DEFAULT_LOCALE']
    
    # 注册蓝图
    from app.blueprints.auth import auth_bp
    from app.blueprints.files import files_bp
    from app.blueprints.main import main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(files_bp, url_prefix='/files')
    app.register_blueprint(main_bp)
    
    # 初始化应用
    Config.init_app(app)
    
    return app 