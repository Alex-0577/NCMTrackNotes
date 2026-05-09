'''app.py
Flask应用工厂和配置主干
该文件定义了Flask应用的工厂函数，配置了数据库、认证、CORS等核心组件。
包含应用创建、蓝图注册、数据库初始化、错误处理、JWT配置和健康检查端点。
'''
from flask import Flask, jsonify, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config
import logging
import time
import uuid
from logging.handlers import RotatingFileHandler

# 初始化扩展
db = SQLAlchemy()           # SQLAlchemy数据库实例
bcrypt = Bcrypt()           # Bcrypt密码加密实例，用于处理JWT认证
jwt = JWTManager()          # JWT管理实例，用于处理JWT认证

def error_response(message: str, code: int = 400):
    """error_response(message, code=400)
    统一的错误响应函数
    创建标准化的JSON错误响应格式。
    parameters:
        message: str, 错误消息
        code: int, HTTP状态码，默认400
    returns:
        tuple: (jsonify响应, 状态码)
    """
    return jsonify({"error": message, "code": code}), code

def create_app(config_class=config):
    '''create_app(config_class=config)
    Flask应用工厂函数
    创建和配置Flask应用实例，初始化所有扩展，注册蓝图，设置错误处理和JWT回调。
    parameters:
        config_class: 配置类，默认为config.Config
    returns:
        app: 配置完成的Flask应用实例
    '''
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 初始化扩展
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    handler = RotatingFileHandler('app.log', maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')
    handler.setFormatter(formatter)
    app.logger.handlers = []
    app.logger.addHandler(handler)
    logging.getLogger('werkzeug').addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')
    
    @app.before_request
    def log_request_start():
        g.request_start_time = time.time()
        g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        app.logger.info(
            f'request.start method={request.method} path={request.path} remote={request.remote_addr} request_id={g.request_id}'
        )
    
    @app.after_request
    def log_request_end(response):
        elapsed_ms = int((time.time() - getattr(g, 'request_start_time', time.time())) * 1000)
        request_id = getattr(g, 'request_id', '')
        response.headers['X-Request-ID'] = request_id
        app.logger.info(
            f'request.end method={request.method} path={request.path} status={response.status_code} duration_ms={elapsed_ms} request_id={request_id}'
        )
        return response
    
    # 注册蓝图
    from routes.auth import auth_bp
    from routes.music import music_bp
    from routes.notes import notes_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(music_bp, url_prefix='/api/music')
    app.register_blueprint(notes_bp, url_prefix='/api/notes')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        '''not_found(error)
        404错误处理函数
        处理应用中不存在的路由请求，返回标准的404错误响应。
        parameters:
            error: 错误对象
        returns:
            JSON响应: {'error': 'Not found'}, 状态码404
        '''
        return error_response('Not found', 404)
    
    @app.errorhandler(500)
    def internal_error(error):
        '''internal_error(error)
        500错误处理函数
        处理服务器内部错误，返回标准的500错误响应。
        parameters:
            error: 错误对象
        returns:
            JSON响应: {'error': 'Internal server error'}, 状态码500
        '''
        return error_response('Internal server error', 500)
    
    # JWT错误处理
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        '''invalid_token_callback(error_string)
        JWT无效令牌回调函数
        当JWT令牌无效时调用，返回自定义的错误响应。
        parameters:
            error_string: 错误描述字符串
        returns:
            JSON响应: {'error': '无效的令牌: {error_string}'}, 状态码401
        '''
        return error_response(f'无效的令牌: {error_string}', 401)
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        '''unauthorized_callback(error_string)
        JWT未授权回调函数
        当请求未提供JWT令牌时调用，返回自定义的错误响应。
        parameters:
            error_string: 错误描述字符串
        returns:
            JSON响应: {'error': '未提供认证令牌: {error_string}'}, 状态码401
        '''
        return error_response(f'未提供认证令牌: {error_string}', 401)
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        '''expired_token_callback(jwt_header, jwt_payload)
        JWT过期令牌回调函数
        当JWT令牌已过期时调用，返回自定义的错误响应。
        parameters:
            jwt_header: JWT头部信息
            jwt_payload: JWT负载信息
        returns:
            JSON响应: {'error': '令牌已过期'}, 状态码401
        '''
        return error_response('令牌已过期', 401)
    
    @app.route('/api/health')
    def health_check():
        '''health_check()
        健康检查端点
        提供应用健康状态检查的API端点，用于监控和部署验证。
        returns:
            JSON响应: {'status': 'healthy', 'service': 'music-notepad-backend'}, 状态码200
        '''
        return jsonify({'status': 'healthy', 'service': 'music-notepad-backend'})
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        '''user_identity_lookup(user)
        JWT用户标识加载器
        将用户对象转换为JWT identity字符串，用于创建JWT令牌。
        parameters:
            user: 用户对象，通常为User模型实例
        returns:
            str: 用户ID的字符串表示
        '''
        # print(f"DEBUG: JWT user_identity_loader called with user: {user}, type: {type(user)}")
        return str(user)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        '''user_lookup_callback(_jwt_header, jwt_data)
        JWT用户查找回调函数
        从JWT数据中提取用户标识，查找并返回对应的用户对象。
        parameters:
            _jwt_header: JWT头部信息
            jwt_data: JWT负载数据，包含'sub'字段
        returns:
            User对象: 根据identity查找到的用户
        '''
        identity = jwt_data["sub"]
        # print(f"DEBUG: JWT user_lookup_callback called with identity: {identity}, type: {type(identity)}")
        return User.query.filter_by(id=int(identity)).first()

    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        '''add_claims_to_access_token(identity)
        JWT额外声明加载器
        向JWT令牌添加额外的声明信息，当前添加用户ID声明。
        parameters:
            identity: 用户标识（字符串形式的用户ID）
        returns:
            dict: 包含用户ID的声明字典，格式为{'user_id': identity}
        '''
        # print(f"DEBUG: JWT additional_claims_loader called with identity: {identity}, type: {type(identity)}")
        return {"user_id": identity}
    
    return app

# 导入模型
from models import User, NeteaseAccount, Song, Note

if __name__ == '__main__':
    '''if __name__ == '__main__'
    应用启动入口
    当直接运行app.py时，创建应用并启动开发服务器。
    returns:
        无返回值，启动Flask应用服务器
    '''
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)