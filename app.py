from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config
import logging

# 初始化扩展
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app(config_class=config):
    """
    应用工厂函数
    """
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
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # JWT错误处理
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return jsonify({'error': f'无效的令牌: {error_string}'}), 401
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        return jsonify({'error': f'未提供认证令牌: {error_string}'}), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': '令牌已过期'}), 401
    
    # 健康检查端点
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'music-notepad-backend'})
    
    # 在app.py的create_app函数中添加
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """将用户ID转换为字符串作为JWT identity"""
        # print(f"DEBUG: JWT user_identity_loader called with user: {user}, type: {type(user)}")
        return str(user)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """从JWT数据中查找用户"""
        identity = jwt_data["sub"]
        # print(f"DEBUG: JWT user_lookup_callback called with identity: {identity}, type: {type(identity)}")
        return User.query.filter_by(id=int(identity)).first()

    # 添加额外的JWT回调用于调试
    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        # print(f"DEBUG: JWT additional_claims_loader called with identity: {identity}, type: {type(identity)}")
        return {"user_id": identity}
    
    return app

# 导入模型
from models import User, NeteaseAccount, Song, Note

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)