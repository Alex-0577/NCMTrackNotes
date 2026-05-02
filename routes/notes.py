'''notes.py
笔记管理路由文件
包含笔记的创建、读取、更新、删除以及公开笔记查询等API端点。
'''
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Note, Song, User
from services.netease_service import netease_service
from datetime import datetime

notes_bp = Blueprint('notes', __name__)         # 笔记相关路由蓝图，URL前缀在app.py中注册为'/notes'

def _get_or_create_song(netease_song_id):
    '''_get_or_create_song(netease_song_id)
    内部函数：获取或创建歌曲记录
    根据网易云歌曲ID获取歌曲记录，如果不存在则从API获取并创建。
    parameters:
        netease_song_id: string, 网易云音乐歌曲ID
    returns:
        Song对象: 歌曲记录，如果API调用失败则返回最小化的歌曲记录
    '''
    # 1. 先从数据库查找
    song = Song.query.filter_by(netease_song_id=netease_song_id).first()
    if song:
        return song
    
    # 2. 从API获取歌曲信息
    try:
        song_info = netease_service.get_song_detail(netease_song_id)
        if not song_info:
            return None
        
        # 3. 创建歌曲记录
        song = Song(
            netease_song_id=netease_song_id,
            title=song_info.get('title', '未知歌曲'),
            artist=song_info.get('artist', '未知艺术家'),
            album=song_info.get('album', '未知专辑'),
            album_cover_url=song_info.get('album_cover_url', ''),
            duration=song_info.get('duration', 0)
        )
        db.session.add(song)
        db.session.flush()  # 获取ID但不提交
        return song
    except Exception as e:
        # 如果API调用失败，创建最小化的歌曲记录
        song = Song(
            netease_song_id=netease_song_id,
            title='未知歌曲',
            artist='未知艺术家',
            album='未知专辑',
            duration=0
        )
        db.session.add(song)
        db.session.flush()
        return song

@notes_bp.route('', methods=['POST'])
@jwt_required()
def create_note():
    '''create_note()
    创建笔记端点
    为指定歌曲创建笔记，如果歌曲不存在于数据库则自动创建歌曲记录，需要JWT令牌认证。
    parameters:
        JSON请求体: {
            'netease_song_id': 'string, 网易云歌曲ID',
            'content': 'string, 笔记内容',
            'timestamp': 0,
            'is_public': false
        }
    returns:
        JSON响应: {
            'message': '笔记创建成功',
            'note': {
                'id': 1,
                'user_id': 1,
                'song_id': 1,
                'content': '这是一条笔记',
                'timestamp': 123456,
                'is_public': false,
                'created_at': '2023-10-01T12:00:00Z',
                'updated_at': '2023-10-01T12:00:00Z',
                'song': {
                    'netease_song_id': '123456',
                    'title': '七里香',
                    'artist': '周杰伦',
                    'album': '七里香',
                    'album_cover_url': 'https://example.com/cover.jpg'
                }
            }
        }, 状态码201
    '''
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # 验证输入
    required_fields = ['netease_song_id', 'content']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    netease_song_id = data['netease_song_id'].strip()
    content = data['content'].strip()
    
    if not netease_song_id or not content:
        return jsonify({'error': '歌曲ID和内容不能为空'}), 400
    
    if len(content) > 10000:
        return jsonify({'error': '笔记内容过长'}), 400
    
    try:
        # 获取或创建歌曲
        song = _get_or_create_song(netease_song_id)
        if not song:
            return jsonify({'error': '无法获取歌曲信息'}), 400
        
        # 创建笔记
        note = Note(
            user_id=user_id,
            song_id=song.id,
            content=content,
            timestamp=data.get('timestamp', 0),
            is_public=data.get('is_public', False)
        )
        
        # 更新歌曲的笔记计数
        song.note_count = Note.query.filter_by(song_id=song.id).count() + 1
        song.updated_at = datetime.utcnow()
        
        db.session.add(note)
        db.session.commit()
        
        return jsonify({
            'message': '笔记创建成功',
            'note': note.to_dict(include_song=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建笔记失败: {str(e)}'}), 500

@notes_bp.route('', methods=['GET'])
@jwt_required()
def get_user_notes():
    '''get_user_notes()
    获取用户笔记端点
    获取当前用户的所有笔记，支持分页和按歌曲筛选，需要JWT令牌认证。
    parameters:
        查询参数:
            page: integer, 页码，默认1
            per_page: integer, 每页数量，默认20
            song_id: string, 按歌曲ID筛选（可选）
    returns:
        JSON响应: {
            'notes': [
                {
                    'id': 1,
                    'user_id': 1,
                    'song_id': 1,
                    'content': '这是一条笔记',
                    'timestamp': 123456,
                    'is_public': false,
                    'created_at': '2023-10-01T12:00:00Z',
                    'updated_at': '2023-10-01T12:00:00Z',
                    'song': {
                        'netease_song_id': '123456',
                        'title': '七里香',
                        'artist': '周杰伦',
                        'album': '七里香',
                        'album_cover_url': 'https://example.com/cover.jpg'
                    }
                }
            ],
            'total': 100,
            'page': 1,
            'per_page': 20,
            'pages': 5
        }, 状态码200
    '''
    user_id = get_jwt_identity()
    
    # 查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    song_id = request.args.get('song_id')
    
    # 构建查询
    query = Note.query.filter_by(user_id=user_id)
    
    if song_id:
        # 如果是网易云歌曲ID，先找到对应的数据库歌曲ID
        song = Song.query.filter_by(netease_song_id=song_id).first()
        if song:
            query = query.filter_by(song_id=song.id)
        else:
            # 如果没有对应的歌曲，返回空结果
            return jsonify({
                'notes': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'pages': 0
            }), 200
    
    # 分页
    notes = query.order_by(Note.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'notes': [note.to_dict(include_song=True) for note in notes.items],
        'total': notes.total,
        'page': notes.page,
        'per_page': notes.per_page,
        'pages': notes.pages
    }), 200

@notes_bp.route('/<int:note_id>', methods=['GET'])
@jwt_required()
def get_note(note_id):
    '''get_note(note_id)
    获取单个笔记端点
    获取指定ID的笔记详情，需要JWT令牌认证，私有笔记只能由所有者查看。
    parameters:
        路径参数:
            note_id: integer, 笔记ID
    returns:
        JSON响应: {
            'note': {
                'id': 1,
                'user_id': 1,
                'song_id': 1,
                'content': '这是一条笔记',
                'timestamp': 123456,
                'is_public': false,
                'created_at': '2023-10-01T12:00:00Z',
                'updated_at': '2023-10-01T12:00:00Z',
                'song': {
                    'netease_song_id': '123456',
                    'title': '七里香',
                    'artist': '周杰伦',
                    'album': '七里香',
                    'album_cover_url': 'https://example.com/cover.jpg'
                }
            }
        }, 状态码200
    '''
    user_id = get_jwt_identity()
    
    note = Note.query.get_or_404(note_id)
    
    # 检查权限
    if int(note.user_id) != int(user_id) and not note.is_public:
        return jsonify({'error': '该笔记是私有的'}), 403
    
    return jsonify({
        'note': note.to_dict(include_song=True)
    }), 200

@notes_bp.route('/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_note(note_id):
    '''update_note(note_id)
    更新笔记端点
    更新指定ID的笔记内容、时间戳或公开状态，需要JWT令牌认证，只能由所有者操作。
    parameters:
        路径参数:
            note_id: integer, 笔记ID
        JSON请求体（可选字段）: {
            'content': 'string, 更新后的内容',
            'timestamp': 123456,
            'is_public': true
        }
    returns:
        JSON响应: {
            'message': '笔记更新成功',
            'note': {
                'id': 1,
                'user_id': 1,
                'song_id': 1,
                'content': '更新后的内容',
                'timestamp': 123456,
                'is_public': true,
                'created_at': '2023-10-01T12:00:00Z',
                'updated_at': '2023-10-01T12:30:00Z',
                'song': {
                    'netease_song_id': '123456',
                    'title': '七里香',
                    'artist': '周杰伦',
                    'album': '七里香',
                    'album_cover_url': 'https://example.com/cover.jpg'
                }
            }
        }, 状态码200
    '''
    user_id = get_jwt_identity()

    # 调试：打印JWT解析结果
    # print(f"DEBUG [update_note]: JWT解析的用户ID: {user_id}, 类型: {type(user_id)}")

    data = request.get_json()
    
    note = Note.query.get_or_404(note_id)

    # 调试：打印数据库中的用户ID
    # print(f"DEBUG [update_note]: 数据库中的笔记用户ID: {note.user_id}, 类型: {type(note.user_id)}")
    
    # 检查权限
    if int(note.user_id) != int(user_id):
        # print(f"DEBUG [update_note]: 权限检查失败! 数据库用户ID: {note.user_id}, JWT用户ID: {user_id}")
        return jsonify({'error': '无权限操作此笔记'}), 403
    
    # 更新字段
    if 'content' in data:
        content = data['content'].strip()
        if not content:
            return jsonify({'error': '笔记内容不能为空'}), 400
        if len(content) > 10000:
            return jsonify({'error': '笔记内容过长'}), 400
        note.content = content
    
    if 'timestamp' in data:
        timestamp = data['timestamp']
        if not isinstance(timestamp, int) or timestamp < 0:
            return jsonify({'error': '时间戳必须是正整数'}), 400
        note.timestamp = timestamp
    
    if 'is_public' in data:
        note.is_public = bool(data['is_public'])
    
    note.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'message': '笔记更新成功',
            'note': note.to_dict(include_song=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新笔记失败: {str(e)}'}), 500

@notes_bp.route('/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note(note_id):
    '''delete_note(note_id)
    删除笔记端点
    删除指定ID的笔记，需要JWT令牌认证，只能由所有者操作。
    parameters:
        路径参数:
            note_id: integer, 笔记ID
    returns:
        JSON响应: {'message': '笔记删除成功'}, 状态码200
    '''
    user_id = get_jwt_identity()
    
    note = Note.query.get_or_404(note_id)
    
    # 检查权限
    if int(note.user_id) != int(user_id):
        return jsonify({'error': '无权限删除此笔记'}), 403
    
    try:
        # 获取歌曲以更新计数
        song = note.song
        
        db.session.delete(note)
        
        # 更新歌曲的笔记计数
        if song:
            song.note_count = Note.query.filter_by(song_id=song.id).count() - 1
            if song.note_count < 0:
                song.note_count = 0
            song.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'message': '笔记删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除笔记失败: {str(e)}'}), 500

@notes_bp.route('/public', methods=['GET'])
def get_public_notes():
    '''get_public_notes()
    获取公开笔记端点
    获取所有公开的笔记，支持分页、按歌曲和用户筛选，无需认证。
    parameters:
        查询参数:
            page: integer, 页码，默认1
            per_page: integer, 每页数量，默认20
            song_id: string, 按歌曲ID筛选（可选）
            user_id: integer, 按用户ID筛选（可选）
    returns:
        JSON响应: {
            'notes': [
                {
                    'id': 1,
                    'user_id': 1,
                    'song_id': 1,
                    'content': '这是一条公开笔记',
                    'timestamp': 123456,
                    'is_public': true,
                    'created_at': '2023-10-01T12:00:00Z',
                    'updated_at': '2023-10-01T12:00:00Z',
                    'song': {
                        'netease_song_id': '123456',
                        'title': '七里香',
                        'artist': '周杰伦',
                        'album': '七里香',
                        'album_cover_url': 'https://example.com/cover.jpg'
                    },
                    'user': {
                        'id': 1,
                        'username': 'testuser'
                    }
                }
            ],
            'total': 50,
            'page': 1,
            'per_page': 20,
            'pages': 3
        }, 状态码200
    '''
    # 查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    song_id = request.args.get('song_id')
    user_id = request.args.get('user_id', type=int)
    
    # 构建查询
    query = Note.query.filter_by(is_public=True)
    
    if song_id:
        # 通过网易云歌曲ID筛选
        song = Song.query.filter_by(netease_song_id=song_id).first()
        if song:
            query = query.filter_by(song_id=song.id)
        else:
            # 如果没有对应的歌曲，返回空结果
            return jsonify({
                'notes': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'pages': 0
            }), 200
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    # 分页
    notes = query.order_by(Note.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取用户信息
    notes_data = []
    for note in notes.items:
        note_dict = note.to_dict(include_song=True)
        user = User.query.get(note.user_id)
        if user:
            note_dict['user'] = {
                'id': user.id,
                'username': user.username
            }
        notes_data.append(note_dict)
    
    return jsonify({
        'notes': notes_data,
        'total': notes.total,
        'page': notes.page,
        'per_page': per_page,
        'pages': notes.pages
    }), 200

@notes_bp.route('/by-song/<song_id>', methods=['GET'])
def get_notes_by_song(song_id):
    '''get_notes_by_song(song_id)
    通过歌曲获取笔记端点
    获取指定歌曲的所有笔记，支持分页和私有笔记查询，无需认证。
    parameters:
        路径参数:
            song_id: string, 网易云音乐歌曲ID
        查询参数:
            page: integer, 页码，默认1
            per_page: integer, 每页数量，默认20
            include_private: boolean, 是否包含私有笔记，默认false
            user_id: integer, 当include_private=true时，必须指定用户ID
    returns:
        JSON响应: {
            'song_id': '123456',
            'song_info': {
                'id': 1,
                'netease_song_id': '123456',
                'title': '七里香',
                'artist': '周杰伦',
                'album': '七里香',
                'album_cover_url': 'https://example.com/cover.jpg',
                'duration': 240000,
                'note_count': 5,
                'created_at': '2023-10-01T12:00:00Z',
                'updated_at': '2023-10-01T12:00:00Z'
            },
            'notes': [
                {
                    'id': 1,
                    'user_id': 1,
                    'song_id': 1,
                    'content': '这是一条笔记',
                    'timestamp': 123456,
                    'is_public': true,
                    'created_at': '2023-10-01T12:00:00Z',
                    'updated_at': '2023-10-01T12:00:00Z',
                    'user': {
                        'id': 1,
                        'username': 'testuser'
                    }
                }
            ],
            'total': 5,
            'page': 1,
            'per_page': 20,
            'pages': 1
        }, 状态码200
    '''
    if not song_id:
        return jsonify({'error': '歌曲ID不能为空'}), 400
    
    # 查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    include_private = request.args.get('include_private', 'false').lower() == 'true'
    user_id = request.args.get('user_id', type=int)
    
    # 查找歌曲
    song = Song.query.filter_by(netease_song_id=song_id).first()
    if not song:
        return jsonify({
            'song_id': song_id,
            'song_info': None,
            'notes': [],
            'total': 0,
            'message': '该歌曲暂无笔记'
        }), 200
    
    # 构建查询
    if include_private and user_id:
        # 如果包含私有笔记，必须指定用户ID
        query = Note.query.filter_by(song_id=song.id, user_id=user_id)
    else:
        # 只查询公开笔记
        query = Note.query.filter_by(song_id=song.id, is_public=True)
    
    # 分页
    notes = query.order_by(Note.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取歌曲信息和用户信息
    song_info = song.to_dict()
    notes_data = []
    
    for note in notes.items:
        note_dict = note.to_dict(include_song=False)  # 不包含歌曲信息，因为上面已提供
        user = User.query.get(note.user_id)
        if user:
            note_dict['user'] = {
                'id': user.id,
                'username': user.username
            }
        notes_data.append(note_dict)
    
    return jsonify({
        'song_id': song_id,
        'song_info': song_info,
        'notes': notes_data,
        'total': notes.total,
        'page': notes.page,
        'per_page': per_page,
        'pages': notes.pages
    }), 200

@notes_bp.route('/user/<int:target_user_id>/by-song/<song_id>', methods=['GET'])
@jwt_required()
def get_user_notes_for_song(target_user_id, song_id):
    '''get_user_notes_for_song(target_user_id, song_id)
    获取指定用户对指定歌曲的笔记端点
    获取指定用户对指定歌曲的笔记，需要JWT令牌认证，只能查看自己的私有笔记或其他用户的公开笔记。
    parameters:
        路径参数:
            target_user_id: integer, 目标用户ID
            song_id: string, 网易云音乐歌曲ID
        查询参数:
            page: integer, 页码，默认1
            per_page: integer, 每页数量，默认20
    returns:
        JSON响应: {
            'song_id': '123456',
            'song_info': {
                'id': 1,
                'netease_song_id': '123456',
                'title': '七里香',
                'artist': '周杰伦',
                'album': '七里香',
                'album_cover_url': 'https://example.com/cover.jpg',
                'duration': 240000,
                'note_count': 2,
                'created_at': '2023-10-01T12:00:00Z',
                'updated_at': '2023-10-01T12:00:00Z'
            },
            'notes': [
                {
                    'id': 1,
                    'user_id': 1,
                    'song_id': 1,
                    'content': '这是一条笔记',
                    'timestamp': 123456,
                    'is_public': true,
                    'created_at': '2023-10-01T12:00:00Z',
                    'updated_at': '2023-10-01T12:00:00Z'
                }
            ],
            'total': 2,
            'page': 1,
            'per_page': 20,
            'pages': 1
        }, 状态码200
    '''
    current_user_id = get_jwt_identity()
    
    if not song_id:
        return jsonify({'error': '歌曲ID不能为空'}), 400
    
    # 查找歌曲
    song = Song.query.filter_by(netease_song_id=song_id).first()
    if not song:
        return jsonify({
            'song_id': song_id,
            'song_info': None,
            'notes': [],
            'total': 0,
            'message': '该歌曲暂无笔记'
        }), 200
    
    # 构建查询
    if int(current_user_id) == int(target_user_id):
        # 查看自己的笔记（包括私有）
        query = Note.query.filter_by(user_id=target_user_id, song_id=song.id)
    else:
        # 查看其他用户的笔记（只包括公开）
        query = Note.query.filter_by(user_id=target_user_id, song_id=song.id, is_public=True)
    
    # 查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 分页
    notes = query.order_by(Note.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取歌曲信息和用户信息
    song_info = song.to_dict()
    notes_data = []
    
    for note in notes.items:
        note_dict = note.to_dict(include_song=False)
        user = User.query.get(note.user_id)
        if user:
            note_dict['user'] = {
                'id': user.id,
                'username': user.username
            }
        notes_data.append(note_dict)
    
    return jsonify({
        'song_id': song_id,
        'song_info': song_info,
        'notes': notes_data,
        'total': notes.total,
        'page': notes.page,
        'per_page': per_page,
        'pages': notes.pages
    }), 200