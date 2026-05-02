'''music.py
音乐搜索和详情路由文件
包含歌曲搜索、获取歌曲详情、批量获取歌曲信息等音乐相关API端点。
'''
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Song
from services.netease_service import netease_service
import time

music_bp = Blueprint('music', __name__)         # 音乐相关路由蓝图，URL前缀在app.py中注册为'/music'

@music_bp.route('/search', methods=['GET'])
@jwt_required()
def search_songs():
    '''search_songs()
    搜索歌曲端点
    搜索网易云音乐中的歌曲，支持分页和缓存优化，需要JWT令牌认证。
    parameters:
        查询参数:
            q: string, 搜索关键词（必需）
            limit: integer, 返回数量，默认30，最大100
            offset: integer, 偏移量，默认0
    returns:
        JSON响应: {
            'keyword': '周杰伦',
            'total': 20,
            'offset': 0,
            'limit': 20,
            'songs': [
                {
                    'id': 'song_123',
                    'netease_song_id': 'song_123',
                    'title': '七里香',
                    'artist': '周杰伦',
                    'album': '七里香',
                    'album_cover_url': 'https://example.com/cover.jpg',
                    'duration': 240000
                }
            ],
            'source': 'combined'
        }, 状态码200
    '''
    keyword = request.args.get('q', '').strip()
    limit = request.args.get('limit', 30, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    if not keyword or len(keyword) < 1:
        return jsonify({'error': '搜索关键词不能为空'}), 400
    
    if len(keyword) > 100:
        return jsonify({'error': '搜索关键词过长'}), 400
    
    if limit > 100:
        limit = 100
    
    try:
        # 1. 从缓存检索
        cache_key = f"search:{keyword}:{limit}:{offset}"
        cached_results = netease_service._get_from_search_cache(cache_key)
        
        if cached_results:
            return jsonify({
                'keyword': keyword,
                'total': len(cached_results),
                'offset': offset,
                'limit': limit,
                'songs': cached_results,
                'source': 'cache'
            }), 200
        
        # 2. 从数据库检索（只检索用户已添加笔记的歌曲）
        db_songs = []
        if len(keyword) > 1:  # 避免太短的搜索词
            search_pattern = f"%{keyword}%"
            db_songs_query = Song.query.filter(
                (Song.title.ilike(search_pattern)) | 
                (Song.artist.ilike(search_pattern)) | 
                (Song.album.ilike(search_pattern))
            ).limit(limit).offset(offset).all()
            
            db_songs = [song.to_dict() for song in db_songs_query]
        
        # 如果数据库中有足够结果，直接返回
        if len(db_songs) >= limit:
            return jsonify({
                'keyword': keyword,
                'total': len(db_songs),
                'offset': offset,
                'limit': limit,
                'songs': db_songs,
                'source': 'database'
            }), 200
        
        # 3. 调用API搜索
        api_results = netease_service.search_songs(keyword, limit, offset)
        
        if not api_results:
            # 如果没有API结果，返回数据库结果
            return jsonify({
                'keyword': keyword,
                'total': len(db_songs),
                'offset': offset,
                'limit': limit,
                'songs': db_songs,
                'source': 'database_only'
            }), 200
        
        # 合并结果（去重）
        combined_results = []
        seen_ids = set()
        
        # 先添加数据库结果
        for song in db_songs:
            seen_ids.add(song['netease_song_id'])
            combined_results.append(song)
        
        # 添加API结果（去除重复的）
        for song in api_results:
            if song.get('netease_song_id') not in seen_ids and len(combined_results) < limit:
                combined_results.append(song)
                seen_ids.add(song.get('netease_song_id'))
        
        return jsonify({
            'keyword': keyword,
            'total': len(combined_results),
            'offset': offset,
            'limit': limit,
            'songs': combined_results,
            'source': 'combined'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500

@music_bp.route('/song/<song_id>', methods=['GET'])
@jwt_required()
def get_song_detail(song_id):
    '''get_song_detail(song_id)
    获取歌曲详情端点
    获取指定歌曲的详细信息，支持三级缓存策略，需要JWT令牌认证。
    parameters:
        路径参数:
            song_id: string, 网易云音乐歌曲ID
    returns:
        JSON响应: {
            'song': {
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
            'source': 'database'
        }, 状态码200
    '''
    if not song_id:
        return jsonify({'error': '歌曲ID不能为空'}), 400
    
    try:
        # 1. 从缓存获取
        cache_key = f"song:{song_id}"
        cached_song = netease_service._get_from_cache(cache_key)
        if cached_song:
            return jsonify({
                'song': cached_song,
                'source': 'cache'
            }), 200
        
        # 2. 从数据库获取
        db_song = Song.query.filter_by(netease_song_id=song_id).first()
        if db_song:
            song_data = db_song.to_dict()
            # 存入缓存
            netease_service._set_to_cache(cache_key, song_data)
            return jsonify({
                'song': song_data,
                'source': 'database'
            }), 200
        
        # 3. 从API获取
        api_song = netease_service.get_song_detail(song_id)
        
        if not api_song:
            return jsonify({'error': '未找到歌曲'}), 404
        
        # 存入缓存
        netease_service._set_to_cache(cache_key, api_song)
        
        return jsonify({
            'song': api_song,
            'source': 'api'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取歌曲详情失败: {str(e)}'}), 500

@music_bp.route('/batch-songs', methods=['POST'])
@jwt_required()
def get_batch_songs():
    '''get_batch_songs()
    批量获取歌曲信息端点
    批量获取多首歌曲的详细信息，优化API调用，需要JWT令牌认证。
    parameters:
        JSON请求体: {
            'song_ids': ['123', '456', '789']
        }
    returns:
        JSON响应: {
            'songs': [
                {
                    'netease_song_id': '123',
                    'title': '七里香',
                    'artist': '周杰伦',
                    'album': '七里香',
                    'album_cover_url': 'https://example.com/cover.jpg',
                    'duration': 240000
                }
            ],
            'source_counts': {
                'cache': 0,
                'database': 1,
                'api': 2
            },
            'found_count': 3,
            'requested_count': 3
        }, 状态码200
    '''
    data = request.get_json()
    
    if not data or not data.get('song_ids'):
        return jsonify({'error': '未提供歌曲ID列表'}), 400
    
    song_ids = data['song_ids']
    
    if not isinstance(song_ids, list):
        return jsonify({'error': 'song_ids必须是数组'}), 400
    
    if len(song_ids) > 100:
        return jsonify({'error': '每次最多查询100首歌曲'}), 400
    
    # 去重
    unique_song_ids = list(set(song_ids))
    
    songs = []
    missing_ids = []
    source_counts = {'cache': 0, 'database': 0, 'api': 0}
    
    for song_id in unique_song_ids:
        # 1. 检查缓存
        cache_key = f"song:{song_id}"
        cached_song = netease_service._get_from_cache(cache_key)
        if cached_song:
            songs.append(cached_song)
            source_counts['cache'] += 1
            continue
        
        # 2. 检查数据库
        db_song = Song.query.filter_by(netease_song_id=song_id).first()
        if db_song:
            song_data = db_song.to_dict()
            songs.append(song_data)
            netease_service._set_to_cache(cache_key, song_data)
            source_counts['database'] += 1
            continue
        
        missing_ids.append(song_id)
    
    # 3. 批量从API获取缺失的歌曲
    if missing_ids:
        for song_id in missing_ids:
            try:
                api_song = netease_service.get_song_detail(song_id)
                if api_song:
                    songs.append(api_song)
                    source_counts['api'] += 1
                else:
                    # 记录未找到的歌曲
                    songs.append({
                        'netease_song_id': song_id,
                        'title': '未知歌曲',
                        'artist': '未知',
                        'album': '未知',
                        'duration': 0,
                        'error': '未找到歌曲信息'
                    })
            except Exception as e:
                songs.append({
                    'netease_song_id': song_id,
                    'title': '未知歌曲',
                    'artist': '未知',
                    'album': '未知',
                    'duration': 0,
                    'error': str(e)
                })
    
    return jsonify({
        'songs': songs,
        'source_counts': source_counts,
        'found_count': len(songs),
        'requested_count': len(song_ids)
    }), 200