'''auth.py
用户认证路由
包含用户注册、登录、资料管理、网易云账号绑定等认证相关API端点。
'''
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db, bcrypt, error_response
from models import User, NeteaseAccount
from services.netease_service import netease_service
import re
import datetime

auth_bp = Blueprint('auth', __name__)       # 认证相关路由，URL前缀在app.py中定义为/api/auth

# User service will be initialized in app context
user_service = None

def get_user_service():
    """Get or create user service instance."""
    from services.user_service import UserService
    global user_service
    if user_service is None:
        user_service = UserService(db, bcrypt)
    return user_service

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
    try:
        data = request.get_json()
        username = data.get('username') if data else None
        email = data.get('email') if data else None
        current_app.logger.info(
            f'register.start username={username} email={email}'
        )

        # 验证输入
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return error_response('Missing required fields', 400)

        # 验证邮箱格式
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, data['email']):
            return error_response('Invalid email format', 400)

        # 使用服务层注册用户
        result = get_user_service().register_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )

        current_app.logger.info(f'register.success user_id={result["user"]["id"]} username={result["user"]["username"]}')

        return jsonify(result), 201
    except ValueError as e:
        current_app.logger.warning(f'register.validation_failed username={username} email={email} error={str(e)}')
        return error_response(str(e), 400)
    except Exception as e:
        current_app.logger.exception('register.failed')
        db.session.rollback()
        return error_response('Registration failed, please try again later', 500)

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
    try:
        data = request.get_json()
        identifier = data.get('identifier') if data else None
        current_app.logger.info(f'login.start identifier={identifier}')

        if not data or not data.get('identifier') or not data.get('password'):
            return error_response('Missing username/email or password', 400)

        # 使用服务层认证用户
        result = get_user_service().authenticate_user(
            identifier=data['identifier'],
            password=data['password']
        )

        current_app.logger.info(f'login.success user_id={result["user"]["id"]} identifier={identifier}')

        return jsonify(result), 200
    except ValueError as e:
        current_app.logger.warning(f'login.failed identifier={identifier} error={str(e)}')
        return error_response(str(e), 401)
    except Exception as e:
        current_app.logger.exception('login.failed')
        return error_response('Login failed, please try again later', 500)

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
    try:
        user_id = get_jwt_identity()
        current_app.logger.info(f'profile.start user_id={user_id}')

        # 使用服务层获取用户资料
        result = get_user_service().get_user_profile(int(user_id))

        current_app.logger.info(f'profile.success user_id={user_id}')
        return jsonify(result), 200
    except ValueError as e:
        current_app.logger.warning(f'profile.not_found user_id={user_id} error={str(e)}')
        return error_response(str(e), 404)
    except Exception as e:
        current_app.logger.exception('profile.failed')
        return error_response('Failed to retrieve profile', 500)

@auth_bp.route('/bind-netease', methods=['POST'])
@jwt_required()
def bind_netease_account():
    '''bind_netease_account
    绑定网易云账号端点
    支持密码登录和验证码登录两种方式绑定网易云音乐账号，需要JWT令牌认证。
    parameters:
        JSON请求体（密码登录）: {
            'netease_username': 'string, 手机号或邮箱',
            'netease_password': 'string, 密码',
            'login_type': 'password'  # 可选，默认为password
        }
        或（验证码登录）: {
            'phone': 'string, 手机号',
            'captcha': 'string, 验证码',
            'login_type': 'captcha'  # 必须为captcha
        }
    returns:
        JSON响应（成功）: {
            'message': 'Netease account bound successfully',
            'netease_account': {
                'netease_user_id': 'netease_user_id',
                'is_bound': true
            }
        }, 状态码200

        JSON响应（失败）: {
            'error': '绑定失败原因',
            'details': '详细错误信息'
        }, 状态码400
    '''
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        login_type = data.get('login_type', 'password') if data else 'password'
        current_app.logger.info(f'bind_netease.start user_id={user_id} login_type={login_type}')

        # 根据登录类型处理不同的认证方式
        login_type = data.get('login_type', 'password')

        bind_result = None

        if login_type == 'captcha':
            # 验证码登录
            phone = data.get('phone')
            captcha = data.get('captcha')

            if not phone or not captcha:
                return error_response('Missing phone or captcha for captcha login', 400)

            # 调用验证码登录
            bind_result = netease_service.captcha_login(phone=phone, captcha=captcha)

        else:
            # 密码登录（默认）
            username = data.get('netease_username')
            password = data.get('netease_password')

            if not username or not password:
                return error_response('Missing Netease credentials', 400)

            # 调用密码登录
            bind_result = netease_service.bind_user_account({
                'username': username,
                'password': password
            })

        if not bind_result.get('success'):
            return error_response('Failed to bind Netease account', 400)

        # 获取绑定的用户名
        bind_username = None
        if login_type == 'captcha':
            bind_username = bind_result.get('data', {}).get('username', data.get('phone'))
        else:
            bind_username = data.get('netease_username')

        # 使用服务层绑定网易云账号
        result = get_user_service().bind_netease_account(
            user_id=int(user_id),
            netease_data={
                'user_id': bind_result.get('data', {}).get('user_id', 'unknown'),
                'username': bind_username
            }
        )

        current_app.logger.info(
            f'bind_netease.success user_id={user_id} netease_user_id={bind_result.get("data", {}).get("user_id", "unknown")} login_type={login_type}'
        )

        return jsonify(result), 200
    except ValueError as e:
        current_app.logger.warning(f'bind_netease.validation_failed user_id={user_id} error={str(e)}')
        return error_response(str(e), 400)
    except Exception as e:
        current_app.logger.exception('bind_netease.failed')
        db.session.rollback()
        return error_response('Binding failed, please try again later', 500)

@auth_bp.route('/bind-netease-uid', methods=['POST'])
@jwt_required()
def bind_netease_account_by_uid():
    '''bind_netease_account_by_uid
    通过UID绑定网易云账号端点
    将传入的网易云UID与当前登录的记事本账号直接绑定，无需登录验证，需要JWT令牌认证。
    适用于已有网易云UID的场景，跳过登录验证流程。
    parameters:
        JSON请求体: {
            'netease_user_id': 'string, 网易云用户ID（必需）',
        }
    returns:
        JSON响应（成功）: {
            'success': true,
            'message': 'Netease account bound successfully by UID',
            'netease_account': {
                'netease_user_id': 'netease_user_id',
                'is_bound': true
            }
        }, 状态码200
        
        JSON响应（失败）: {
            'success': false,
            'message': '绑定失败原因',
            'error': '详细错误信息'
        }, 状态码400
    '''
    # 获取当前登录用户ID
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # 验证输入参数
    if not data:
        return jsonify({
            'success': False,
            'message': '请求体不能为空',
            'error': 'Missing request body'
        }), 400
    
    netease_user_id = data.get('netease_user_id')
    
    if not netease_user_id:
        return jsonify({
            'success': False,
            'message': '缺少必要参数',
            'error': 'Missing netease_user_id or netease_username'
        }), 400
    
    # 验证参数格式
    if not isinstance(netease_user_id, str):
        return jsonify({
            'success': False,
            'message': '参数格式错误',
            'error': 'netease_user_id and netease_username must be strings'
        }), 400
    
    # 检查网易云UID是否已被其他用户绑定
    existing_binding = NeteaseAccount.query.filter_by(netease_user_id=netease_user_id).first()
    if existing_binding and existing_binding.user_id != int(user_id):
        return jsonify({
            'success': False,
            'message': '该网易云账号已被其他用户绑定',
            'error': f'Netease UID {netease_user_id} already bound to user {existing_binding.user_id}'
        }), 409
    
    try:
        # 检查当前用户是否已有绑定
        existing_account = NeteaseAccount.query.filter_by(user_id=user_id).first()
        
        if existing_account:
            # 更新现有绑定
            existing_account.netease_user_id = netease_user_id
            existing_account.is_bound = True
            existing_account.bound_at = datetime.utcnow()  # 需要导入datetime
            action = 'updated'
        else:
            # 创建新绑定
            new_account = NeteaseAccount(
                user_id=user_id,
                netease_user_id=netease_user_id,
                is_bound=True,
                bound_at=datetime.utcnow()  # 需要导入datetime
            )
            db.session.add(new_account)
            action = 'created'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Netease account bound successfully by UID ({action})',
            'netease_account': {
                'netease_user_id': netease_user_id,
                'is_bound': True,
                'bound_at': datetime.utcnow().isoformat() if action == 'created' else 'updated'
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '绑定过程中发生错误',
            'error': str(e)
        }), 500

@auth_bp.route('/send-captcha', methods=['POST'])
@jwt_required()
def send_captcha():
    '''send_captcha
    发送验证码端点
    向指定手机号发送短信验证码，用于验证码登录绑定网易云账号。
    parameters:
        JSON请求体: {
            'phone': 'string, 手机号',
            'ctcode': 'string, 国家代码，默认86'
        }
    returns:
        JSON响应（成功）: {
            'success': True,
            'message': '验证码发送成功',
            'data': {
                'phone': '手机号',
                'captcha_sent': True
            }
        }, 状态码200
        
        JSON响应（失败）: {
            'success': False,
            'message': '验证码发送失败消息',
            'data': None
        }, 状态码400
    '''
    data = request.get_json()
    phone = data.get('phone')
    ctcode = data.get('ctcode', '86')
    
    if not phone:
        return jsonify({
            'success': False,
            'message': '手机号不能为空',
            'data': None
        }), 400
    
    # 调用netease_service发送验证码
    send_result = netease_service.send_captcha(phone=phone, ctcode=ctcode)
    
    if send_result.get('success'):
        return jsonify(send_result), 200
    else:
        return jsonify(send_result), 400

@auth_bp.route('/verify-captcha', methods=['POST'])
@jwt_required()
def verify_captcha():
    '''verify_captcha
    验证验证码端点
    验证用户输入的短信验证码是否正确，用于验证码登录前的验证。
    parameters:
        JSON请求体: {
            'phone': 'string, 手机号',
            'captcha': 'string, 验证码',
            'ctcode': 'string, 国家代码，默认86'
        }
    returns:
        JSON响应（成功）: {
            'success': True,
            'message': '验证码验证成功',
            'data': {
                'phone': '手机号',
                'captcha_verified': True
            }
        }, 状态码200
        
        JSON响应（失败）: {
            'success': False,
            'message': '验证码验证失败消息',
            'data': None
        }, 状态码400
    '''
    data = request.get_json()
    phone = data.get('phone')
    captcha = data.get('captcha')
    ctcode = data.get('ctcode', '86')
    
    if not phone or not captcha:
        return jsonify({
            'success': False,
            'message': '手机号和验证码不能为空',
            'data': None
        }), 400
    
    # 调用netease_service验证验证码
    verify_result = netease_service.verify_captcha(phone=phone, captcha=captcha, ctcode=ctcode)
    
    if verify_result.get('success'):
        return jsonify(verify_result), 200
    else:
        return jsonify(verify_result), 400

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