'''auth.py
用户认证路由
包含用户注册、登录、资料管理、网易云账号绑定等认证相关API端点。
'''
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db, bcrypt
from models import User, NeteaseAccount
from services.netease_service import netease_service
import re

auth_bp = Blueprint('auth', __name__)       # 认证相关路由，URL前缀在app.py中定义为/api/auth

@auth_bp.route('/register', methods=['POST'])
def register():
    '''register()
    用户注册端点
    处理新用户注册请求，创建用户账户并返回JWT令牌。
    parameters:
        JSON请求体: {
            'username': 'string, 用户名',
            'email': 'string, 邮箱地址',
            'password': 'string, 密码'
        }
    returns:
        JSON响应: {
            'message': 'User registered successfully',
            'user': {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com',
                'created_at': '2023-10-01T12:00:00Z'
            },
            'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
        }, 状态码201
    '''
    data = request.get_json()
    
    # 验证输入
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # 验证邮箱格式
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # 检查用户名和邮箱是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # 创建新用户
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()

    # 调试：打印用户ID
    # print(f"DEBUG [register]: 创建用户成功，用户ID: {user.id}, 类型: {type(user.id)}")
    
    # 生成访问令牌 - 将identity转换为字符串
    access_token = create_access_token(identity=str(user.id))

    # 调试：打印生成的令牌
    # print(f"DEBUG [register]: 生成的JWT令牌: {access_token[:50]}...")
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(),
        'access_token': access_token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    '''login()
    用户登录端点
    处理用户登录请求，验证凭证并返回JWT令牌。
    parameters:
        JSON请求体: {
            'identifier': 'string, 用户名或邮箱',
            'password': 'string, 密码'
        }
    returns:
        JSON响应: {
            'message': 'Login successful',
            'user': {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com',
                'created_at': '2023-10-01T12:00:00Z'
            },
            'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
        }, 状态码200
    '''
    data = request.get_json()
    
    if not data or not data.get('identifier') or not data.get('password'):
        return jsonify({'error': 'Missing username/email or password'}), 400
    
    identifier = data['identifier']
    password = data['password']
    
    # 通过用户名或邮箱查找用户
    if '@' in identifier:
        user = User.query.filter_by(email=identifier).first()
    else:
        user = User.query.filter_by(username=identifier).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # 生成访问令牌 - 将identity转换为字符串
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    '''get_profile()
    获取用户资料端点
    获取当前认证用户的详细资料信息，需要JWT令牌认证。
    returns:
        JSON响应: {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'created_at': '2023-10-01T12:00:00Z',
            'netease_account': {
                'netease_user_id': 'netease_123456',
                'netease_username': 'netease_user',
                'is_bound': true,
                'bound_at': '2023-10-01T12:00:00Z'
            }
        }, 状态码200
    '''
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    response = user.to_dict()
    
    # 添加网易云账号绑定信息
    if user.netease_account:
        response['netease_account'] = user.netease_account.to_dict()
    
    return jsonify(response), 200

@auth_bp.route('/bind-netease', methods=['POST'])
@jwt_required()
def bind_netease_account():
    '''bind_netease_account()
    绑定网易云账号端点
    将网易云音乐账号绑定到当前用户账户，需要JWT令牌认证。
    parameters:
        JSON请求体: {
            'netease_username': 'string, 网易云用户名',
            'netease_password': 'string, 网易云密码'
        }
    returns:
        JSON响应: {
            'message': 'Netease account bound successfully',
            'netease_account': {
                'netease_username': 'netease_user',
                'is_bound': true
            }
        }, 状态码200
    '''
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('netease_username') or not data.get('netease_password'):
        return jsonify({'error': 'Missing Netease credentials'}), 400
    
    # 调用网易云音乐服务进行绑定（占位实现）
    bind_result = netease_service.bind_user_account({
        'username': data['netease_username'],
        'password': data['netease_password']
    })
    
    if not bind_result.get('success'):
        return jsonify({
            'error': 'Failed to bind Netease account',
            'details': bind_result.get('message', 'Unknown error')
        }), 400
    
    # 检查是否已绑定
    existing_account = NeteaseAccount.query.filter_by(user_id=user_id).first()
    
    if existing_account:
        # 更新现有绑定
        existing_account.netease_user_id = bind_result.get('data', {}).get('user_id', 'unknown')
        existing_account.netease_username = data['netease_username']
        existing_account.is_bound = True
    else:
        # 创建新绑定
        new_account = NeteaseAccount(
            user_id=user_id,
            netease_user_id=bind_result.get('data', {}).get('user_id', 'unknown'),
            netease_username=data['netease_username'],
            is_bound=True
        )
        db.session.add(new_account)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Netease account bound successfully',
        'netease_account': {
            'netease_username': data['netease_username'],
            'is_bound': True
        }
    }), 200

@auth_bp.route('/unbind-netease', methods=['POST'])
@jwt_required()
def unbind_netease_account():
    '''unbind_netease_account()
    解绑网易云账号端点
    解绑当前用户已绑定的网易云音乐账号，需要JWT令牌认证。
    returns:
        JSON响应: {'message': 'Netease account unbound successfully'}, 状态码200
    '''
    user_id = get_jwt_identity()
    
    account = NeteaseAccount.query.filter_by(user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'No Netease account bound'}), 404
    
    db.session.delete(account)
    db.session.commit()
    
    return jsonify({'message': 'Netease account unbound successfully'}), 200