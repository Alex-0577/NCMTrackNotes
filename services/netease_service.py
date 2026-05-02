'''netease_service.py
网易云音乐服务模拟文件
模拟网易云音乐API调用，提供歌曲搜索、详情获取、用户绑定等功能，用于测试和开发。
'''
import json
import os
import re

class NeteaseMusicService:
    '''NeteaseMusicService
    网易云音乐服务类提供缓存、测试数据加载和API调用模拟功能。
    variables:
        api_base: String, API基础URL
        _cache: dict, 歌曲详情内存缓存
        _cache_max_size: int, 缓存最大容量
        _search_cache: dict, 搜索结果内存缓存
        _search_cache_max_size: int, 搜索缓存最大容量
        _songs: dict, 测试歌曲数据
        _accounts: dict, 测试账户数据
    functions:
        _load_test_data: 加载测试数据
        _get_from_cache: 从缓存获取数据
        _set_to_cache: 将数据存入缓存
        _get_from_search_cache: 从搜索缓存获取数据
        _set_to_search_cache: 将搜索数据存入缓存
        search_songs: 搜索歌曲
        get_song_detail: 获取歌曲详情
        get_user_info: 获取用户信息
        bind_user_account: 绑定用户账号
        get_playlist_songs: 获取歌单歌曲
    '''
    
    def __init__(self):
        self.api_base = "https://music.163.com/api"
        # 内存缓存
        self._cache = {}
        self._cache_max_size = 1000
        self._search_cache = {}
        self._search_cache_max_size = 500
        
        # 加载测试数据
        self._load_test_data()
    
    def _load_test_data(self):
        '''_load_test_data()
        加载测试数据方法
        从JSON文件加载测试用的歌曲数据和账户数据，用于模拟API调用。
        returns:
            无返回值，但会初始化_songs和_accounts实例变量
        '''
        try:
            # 加载歌曲数据
            songs_file = os.path.join(os.path.dirname(__file__), 'music_data_test.json')
            with open(songs_file, 'r', encoding='utf-8') as f:
                songs_data = json.load(f)
                self._songs = {song['song_id']: song for song in songs_data.get('songs', [])}
            
            # 加载账户数据
            accounts_file = os.path.join(os.path.dirname(__file__), 'music_accounts.json')
            if os.path.exists(accounts_file):
                with open(accounts_file, 'r', encoding='utf-8') as f:
                    accounts_data = json.load(f)
                    self._accounts = {account['user_id']: account for account in accounts_data.get('music_accounts', [])}
            else:
                # 如果没有账户文件，使用默认账户
                self._accounts = {
                    'netease_001': {
                        'username': 'music_lover_2024',
                        'user_id': 'netease_001',
                        'playlists': [
                            {
                                'playlist_id': 'pl_001',
                                'playlist_name': '每日推荐',
                                'song_ids': ['1', '2', '3']
                            }
                        ]
                    }
                }
        except Exception as e:
            print(f"加载测试数据失败: {e}")
            self._songs = {}
            self._accounts = {}
    
    def _get_from_cache(self, key):
        '''_get_from_cache(key)
        从缓存获取数据方法
        根据键从内存缓存中获取缓存的歌曲详情数据。
        parameters:
            key: string, 缓存键
        returns:
            缓存的值，如果不存在则返回None
        '''
        return self._cache.get(key)
    
    def _set_to_cache(self, key, value):
        '''_set_to_cache(key, value)
        将数据存入缓存方法
        将歌曲详情数据存入内存缓存，如果缓存已满则使用LRU策略淘汰旧数据。
        parameters:
            key: string, 缓存键
            value: any, 要缓存的值
        returns:
            无返回值
        '''
        if len(self._cache) >= self._cache_max_size:
            # 简单的LRU策略
            oldest_key = next(iter(self._cache))
            self._cache.pop(oldest_key)
        self._cache[key] = value
    
    def _get_from_search_cache(self, key):
        '''_get_from_search_cache(key)
        从搜索缓存获取数据方法
        根据键从内存缓存中获取缓存的搜索结果数据。
        parameters:
            key: string, 缓存键
        returns:
            缓存的值，如果不存在则返回None
        '''
        return self._search_cache.get(key)
    
    def _set_to_search_cache(self, key, value):
        '''_set_to_search_cache(key, value)
        将搜索数据存入缓存方法
        将搜索结果数据存入内存缓存，如果缓存已满则使用LRU策略淘汰旧数据。
        parameters:
            key: string, 缓存键
            value: any, 要缓存的值
        returns:
            无返回值
        '''
        if len(self._search_cache) >= self._search_cache_max_size:
            oldest_key = next(iter(self._search_cache))
            self._search_cache.pop(oldest_key)
        self._search_cache[key] = value
    
    def search_songs(self, keyword, limit=30, offset=0):
        '''search_songs(keyword, limit=30, offset=0)
        搜索歌曲方法
        模拟网易云音乐搜索API，根据关键词搜索歌曲，支持分页和缓存。
        parameters:
            keyword: string, 搜索关键词
            limit: int, 返回数量，默认30
            offset: int, 偏移量，默认0
        returns:
            list: 歌曲信息列表，格式为[
                {
                    'id': 'song_id',
                    'netease_song_id': 'song_id',
                    'title': '歌曲标题',
                    'artist': '艺术家',
                    'album': '专辑',
                    'album_cover_url': '封面URL',
                    'duration': 180000
                }
            ]
        '''
        cache_key = f"search:{keyword}:{limit}:{offset}"
        cached = self._get_from_search_cache(cache_key)
        if cached:
            return cached
        
        # TODO: 实现网易云音乐搜索API调用
        # 使用测试数据进行搜索
        result = []
        keyword_lower = keyword.lower()
        
        # 在测试数据中搜索
        for song in self._songs.values():
            # 检查标题、艺术家、专辑是否包含关键词
            if (keyword_lower in song.get('title', '').lower() or
                keyword_lower in song.get('artist', '').lower() or
                keyword_lower in song.get('album', '').lower()):
                
                result.append({
                    'id': song['song_id'],
                    'netease_song_id': song['song_id'],
                    'title': song.get('title', '未知歌曲'),
                    'artist': song.get('artist', '未知艺术家'),
                    'album': song.get('album', '未知专辑'),
                    'album_cover_url': song.get('album_cover_url', ''),
                    'duration': song.get('duration', 0)
                })
                
                if len(result) >= limit + offset:
                    break
        
        # 应用分页
        if offset < len(result):
            result = result[offset:offset+limit]
        
        # 存入缓存
        self._set_to_search_cache(cache_key, result)
        return result
    
    def get_song_detail(self, song_id):
        '''get_song_detail(song_id)
        获取歌曲详情方法
        模拟网易云音乐歌曲详情API，根据歌曲ID获取歌曲详细信息，支持缓存。
        parameters:
            song_id: string, 网易云音乐歌曲ID
        returns:
            dict: 歌曲详情，格式为{
                'id': 'song_id',
                'netease_song_id': 'song_id',
                'title': '歌曲标题',
                'artist': '艺术家',
                'album': '专辑',
                'album_cover_url': '封面URL',
                'duration': 180000
            }
        '''
        cache_key = f"song:{song_id}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # TODO: 实现获取歌曲详情API调用
        # 从测试数据中获取歌曲详情
        song = self._songs.get(song_id)
        if song:
            result = {
                'id': song_id,
                'netease_song_id': song_id,
                'title': song.get('title', '未知歌曲'),
                'artist': song.get('artist', '未知艺术家'),
                'album': song.get('album', '未知专辑'),
                'album_cover_url': song.get('album_cover_url', ''),
                'duration': song.get('duration', 0)
            }
        else:
            # 如果没有找到，返回模拟数据
            result = {
                'id': song_id,
                'netease_song_id': song_id,
                'title': f'歌曲 {song_id}',
                'artist': '模拟艺术家',
                'album': '模拟专辑',
                'album_cover_url': 'https://example.com/cover.jpg',
                'duration': 180000
            }
        
        # 存入缓存
        self._set_to_cache(cache_key, result)
        return result
    
    def get_user_info(self, user_id):
        '''get_user_info(user_id)
        获取用户信息方法
        模拟网易云音乐用户信息API，根据用户ID获取用户信息。
        parameters:
            user_id: string, 网易云用户ID
        returns:
            dict: 用户信息，格式为{
                'user_id': 'netease_user_id',
                'username': '用户名',
                'playlists': [
                    {
                        'playlist_id': '歌单ID',
                        'playlist_name': '歌单名称',
                        'song_ids': ['歌曲ID1', '歌曲ID2']
                    }
                ]
            } 或 None
        '''
        # TODO: 实现获取用户信息API调用
        # 从测试数据中获取用户信息
        account = self._accounts.get(user_id)
        if account:
            return {
                'user_id': account['user_id'],
                'username': account['username'],
                'playlists': account.get('playlists', [])
            }
        return None
    
    def bind_user_account(self, credentials):
        '''bind_user_account(credentials)
        绑定用户账号方法
        模拟网易云音乐用户认证和绑定逻辑，验证用户名密码并返回绑定结果。
        parameters:
            credentials: dict, 认证信息，格式为{
                'username': '用户名',
                'password': '密码'
            }
        returns:
            dict: 绑定结果，格式为{
                'success': True/False,
                'message': '绑定成功/失败消息',
                'data': {
                    'user_id': 'netease_user_id',
                    'username': '用户名'
                } 或 None
            }
        '''
        # TODO: 实现用户认证和绑定逻辑
        username = credentials.get('username', '')
        password = credentials.get('password', '')
        
        # 模拟认证逻辑
        if username and password:
            # 在测试账户中查找
            for account in self._accounts.values():
                if account['username'] == username:
                    return {
                        'success': True,
                        'message': '绑定成功',
                        'data': {
                            'user_id': account['user_id'],
                            'username': account['username']
                        }
                    }
            
            # 如果没有找到，创建一个新的测试账户
            new_user_id = f'netease_{len(self._accounts) + 1:03d}'
            new_account = {
                'username': username,
                'user_id': new_user_id,
                'playlists': []
            }
            self._accounts[new_user_id] = new_account
            
            return {
                'success': True,
                'message': '绑定成功（新用户）',
                'data': {
                    'user_id': new_user_id,
                    'username': username
                }
            }
        
        return {
            'success': False,
            'message': '认证失败，请检查用户名和密码',
            'data': None
        }
    
    def get_playlist_songs(self, playlist_id, user_id=None):
        '''get_playlist_songs(playlist_id, user_id=None)
        获取歌单歌曲方法
        模拟网易云音乐歌单歌曲API，根据歌单ID获取歌单中的歌曲列表。
        parameters:
            playlist_id: string, 歌单ID
            user_id: string, 用户ID（用于私有歌单），可选
        returns:
            list: 歌曲详情列表，格式为[歌曲详情字典, ...]
        '''
        # TODO: 实现获取歌单歌曲API调用
        songs = []
        
        # 查找指定用户的歌单
        if user_id:
            account = self._accounts.get(user_id)
            if account:
                for playlist in account.get('playlists', []):
                    if playlist['playlist_id'] == playlist_id:
                        # 获取歌单中的所有歌曲
                        for song_id in playlist.get('song_ids', []):
                            song_detail = self.get_song_detail(song_id)
                            if song_detail:
                                songs.append(song_detail)
                        break
        else:
            # 如果没有指定用户，在所有用户中查找公开歌单
            for account in self._accounts.values():
                for playlist in account.get('playlists', []):
                    if playlist['playlist_id'] == playlist_id:
                        # 获取歌单中的所有歌曲
                        for song_id in playlist.get('song_ids', []):
                            song_detail = self.get_song_detail(song_id)
                            if song_detail:
                                songs.append(song_detail)
                        break
                if songs:  # 找到第一个匹配的歌单就返回
                    break
        
        return songs

netease_service = NeteaseMusicService()         # 创建网易云音乐服务实例，供其他模块调用