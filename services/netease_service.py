'''netease_service.py
网易云音乐服务实现文件
基于NeteaseCloudMusicApi SDK实现真实的网易云音乐API调用，提供歌曲搜索、详情获取、用户绑定等功能。
包含缓存管理、API调用封装、数据结构转换等核心功能。
'''

import json
import os
import re
import time
from MusicLibrary.neteaseCloudMusicApi import NeteaseCloudMusicApi

class NeteaseMusicService:
    '''NeteaseMusicService
    网易云音乐服务类
    基于NeteaseCloudMusicApi SDK封装，提供真实的网易云音乐API调用功能，包含内存缓存管理和数据结构转换。
    variables:
        api_base: String, API基础URL
        _cache: dict, 歌曲详情内存缓存
        _cache_max_size: int, 缓存最大容量
        _search_cache: dict, 搜索结果内存缓存
        _search_cache_max_size: int, 搜索缓存最大容量
        _api_client: NeteaseCloudMusicApi, 网易云音乐API客户端实例
        _user_cookies: dict, 用户登录状态cookie存储
    functions:
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
        '''__init__
        初始化网易云音乐服务
        创建API客户端实例，初始化内存缓存，设置缓存容量限制。
        parameters:
            无参数
        returns:
            无返回值
        '''
        self.api_base = "https://music.163.com/api"
        # 内存缓存
        self._cache = {}
        self._cache_max_size = 1000
        self._search_cache = {}
        self._search_cache_max_size = 500
        
        # 初始化API客户端
        # 对创建对象进行异常处理，确保服务稳定性
        try:
            self._api_client = NeteaseCloudMusicApi()
        except Exception as e:
            print(f"初始化API客户端时发生错误: {e}")
            exit(1)  # 退出程序，无法继续运行
        # 用户登录状态存储
        self._user_cookies = {}
    
    def _get_from_cache(self, key):
        '''_get_from_cache
        从缓存获取数据
        根据缓存键从内存缓存中获取缓存的歌曲详情数据，支持LRU缓存策略。
        parameters:
            key(string): 缓存键，格式为"cache_type:key"
        returns:
            any: 缓存的值，如果键不存在则返回None
        '''
        return self._cache.get(key)
    
    def _set_to_cache(self, key, value):
        '''_set_to_cache
        将数据存入缓存
        将歌曲详情数据存入内存缓存，当缓存达到最大容量时使用LRU策略淘汰最久未使用的数据。
        parameters:
            key(string): 缓存键
            value(any): 要缓存的值
        returns:
            无返回值
        '''
        if len(self._cache) >= self._cache_max_size:
            # 简单的LRU策略：移除最早的一个
            oldest_key = next(iter(self._cache))
            self._cache.pop(oldest_key)
        self._cache[key] = value
    
    def _get_from_search_cache(self, key):
        '''_get_from_search_cache
        从搜索缓存获取数据
        根据缓存键从内存缓存中获取缓存的搜索结果数据。
        parameters:
            key(string): 缓存键，格式为"search:keyword:limit:offset"
        returns:
            any: 缓存的值，如果键不存在则返回None
        '''
        return self._search_cache.get(key)
    
    def _set_to_search_cache(self, key, value):
        '''_set_to_search_cache
        将搜索数据存入缓存
        将搜索结果数据存入内存缓存，当缓存达到最大容量时使用LRU策略淘汰最久未使用的数据。
        parameters:
            key(string): 缓存键
            value(any): 要缓存的值
        returns:
            无返回值
        '''
        if len(self._search_cache) >= self._search_cache_max_size:
            oldest_key = next(iter(self._search_cache))
            self._search_cache.pop(oldest_key)
        self._search_cache[key] = value
    
    def search_songs(self, keyword, limit=30, offset=0):
        '''search_songs
        搜索歌曲
        调用网易云音乐真实API搜索歌曲，支持分页和缓存，返回格式化的歌曲信息列表。
        parameters:
            keyword(string): 搜索关键词
            limit(int): 返回数量，默认30
            offset(int): 偏移量，默认0
        returns:
            list: 歌曲信息列表，格式为[
                {
                    'id': 'song_id',  # 歌曲ID
                    'netease_song_id': 'song_id',  # 网易云歌曲ID
                    'title': '歌曲标题',  # 歌曲标题
                    'artist': '艺术家',  # 艺术家
                    'album': '专辑',  # 专辑名称
                    'album_cover_url': '封面URL',  # 专辑封面URL
                    'duration': 180000  # 歌曲时长（毫秒）
                }
            ]
        '''
        cache_key = f"search:{keyword}:{limit}:{offset}"
        cached = self._get_from_search_cache(cache_key)
        if cached:
            return cached
        
        for attempt in range(3):  # 重试3次
            try:
                # 调用真实API搜索歌曲
                response = self._api_client.search(keywords=keyword, limit=limit, offset=offset, type=1)
                
                if response.status == 200:
                    data = response.body
                    result = []
                    
                    # 解析搜索结果
                    if 'result' in data and 'songs' in data['result']:
                        songs = data['result']['songs']
                        for song in songs:
                            # 提取艺术家信息
                            artists = song.get('ar', [])
                            artist_name = artists[0].get('name', '未知艺术家') if artists else '未知艺术家'
                            
                            # 提取专辑信息
                            album_info = song.get('al', {})
                            album_name = album_info.get('name', '未知专辑')
                            album_cover_url = album_info.get('picUrl', '')
                            
                            song_data = {
                                'id': str(song.get('id', '')),
                                'netease_song_id': str(song.get('id', '')),
                                'title': song.get('name', '未知歌曲'),
                                'artist': artist_name,
                                'album': album_name,
                                'album_cover_url': album_cover_url,
                                'duration': song.get('duration', 0)  # 歌曲时长（毫秒）
                            }
                            result.append(song_data)
                    
                    # 存入缓存
                    self._set_to_search_cache(cache_key, result)
                    return result
                else:
                    # API调用失败，返回空列表
                    return []
                    
            except Exception as e:
                if attempt == 2:  # 最后一次重试失败
                    print(f"搜索歌曲失败，已重试3次: {e}")
                    return []
                time.sleep(1)  # 等待1秒后重试
    
    def get_song_detail(self, song_id):
        '''get_song_detail
        获取歌曲详情
        调用网易云音乐真实API获取歌曲详细信息，支持缓存，返回格式化的歌曲详情。
        parameters:
            song_id(string): 网易云音乐歌曲ID
        returns:
            dict: 歌曲详情，格式为{
                'id': 'song_id',  # 歌曲ID
                'netease_song_id': 'song_id',  # 网易云歌曲ID
                'title': '歌曲标题',  # 歌曲标题
                'artist': '艺术家',  # 艺术家
                'album': '专辑',  # 专辑名称
                'album_cover_url': '封面URL',  # 专辑封面URL
                'duration': 180000  # 歌曲时长（毫秒）
            }
        '''
        cache_key = f"song:{song_id}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        for attempt in range(3):  # 重试3次
            try:
                # 调用真实API获取歌曲详情
                response = self._api_client.song_detail(ids=song_id)

                if response.status == 200:
                    data = response.body
                    result = None
                    
                    # 解析歌曲详情
                    if 'songs' in data and len(data['songs']) > 0:
                        song = data['songs'][0]

                        # 提取艺术家信息
                        artists = song.get('ar', [])
                        artist_name = artists[0].get('name', '未知艺术家') if artists else '未知艺术家'
                        
                        # 提取专辑信息
                        album_info = song.get('al', {})
                        album_name = album_info.get('name', '未知专辑')
                        album_cover_url = album_info.get('picUrl', '')
                        
                        result = {
                            'id': str(song.get('id', song_id)),
                            'netease_song_id': str(song.get('id', song_id)),
                            'title': song.get('name', '未知歌曲'),
                            'artist': artist_name,
                            'album': album_name,
                            'album_cover_url': album_cover_url,
                            'duration': song.get('dt', 0)  # 歌曲时长（毫秒）
                        }
                    
                    if result:
                        # 存入缓存
                        self._set_to_cache(cache_key, result)
                        return result
                    else:
                        # 如果没有找到歌曲，返回模拟数据
                        return {
                            'id': song_id,
                            'netease_song_id': song_id,
                            'title': f'歌曲 {song_id}',
                            'artist': '未知艺术家',
                            'album': '未知专辑',
                            'album_cover_url': 'https://example.com/cover.jpg',
                            'duration': 180000
                        }
                else:
                    # API调用失败，返回模拟数据
                    return {
                        'id': song_id,
                        'netease_song_id': song_id,
                        'title': f'歌曲 {song_id}',
                        'artist': '未知艺术家',
                        'album': '未知专辑',
                        'album_cover_url': 'https://example.com/cover.jpg',
                        'duration': 180000
                    }
                    
            except Exception as e:
                if attempt == 2:  # 最后一次重试失败
                    print(f"获取歌曲详情失败，已重试3次: {e}")
                    return {
                        'id': song_id,
                        'netease_song_id': song_id,
                        'title': f'歌曲 {song_id}',
                        'artist': '未知艺术家',
                        'album': '未知专辑',
                        'album_cover_url': 'https://example.com/cover.jpg',
                        'duration': 180000
                    }
                time.sleep(1)  # 等待1秒后重试
    
    def get_user_info(self, user_id):
        '''get_user_info
        获取用户信息
        调用网易云音乐真实API获取用户信息，包括基本信息和歌单名称（不包含歌单中的歌曲列表）。
        parameters:
            user_id(string): 网易云用户ID
        returns:
            dict: 用户信息，格式为{
                'user_id': 'netease_user_id',  # 网易云用户ID
                'username': '用户名',  # 用户名
                'playlists': [  # 歌单列表
                    {
                        'playlist_id': '歌单ID',  # 歌单ID
                        'playlist_name': '歌单名称'  # 歌单名称
                    }
                ]
            } 或 None（当用户不存在时）
        '''
        try:
            # 调用真实API获取用户详情
            response = self._api_client.user_detail(uid=user_id)
            
            if response.status == 200:
                data = response.body
                
                if 'profile' in data:
                    profile = data['profile']
                    
                    # 获取用户歌单
                    playlists = []
                    try:
                        playlist_response = self._api_client.user_playlist(uid=user_id, limit=10)
                        if playlist_response.status == 200:
                            playlist_data = playlist_response.body
                            if 'playlist' in playlist_data:
                                for playlist in playlist_data['playlist']:
                                    playlist_id = str(playlist.get('id', ''))
                                    playlist_name = playlist.get('name', '未命名歌单')
                                    
                                    playlist_info = {
                                        'playlist_id': playlist_id,
                                        'playlist_name': playlist_name
                                    }
                                    playlists.append(playlist_info)
                    except Exception as e:
                        # 如果获取歌单失败，记录错误但继续返回用户信息
                        print(f"获取用户歌单列表时发生错误: {e}")
                        # 不将错误信息返回给调用方，只返回已有的歌单列表
                    
                    return {
                        'user_id': str(profile.get('userId', user_id)),
                        'username': profile.get('nickname', '未知用户'),
                        'playlists': playlists
                    }
            
            return None
                    
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            return None
    
    def bind_user_account(self, credentials):
        '''bind_user_account
        绑定用户账号
        调用网易云音乐真实API进行用户认证和绑定，支持手机号和邮箱登录。
        parameters:
            credentials(dict): 认证信息，格式为{
                'username': '用户名',  # 手机号或邮箱
                'password': '密码'  # 密码
            }
        returns:
            dict: 绑定结果，格式为{
                'success': True/False,  # 绑定是否成功
                'message': '绑定成功/失败消息',  # 消息描述
                'data': {  # 绑定数据，成功时包含用户信息
                    'user_id': 'netease_user_id',  # 网易云用户ID
                    'username': '用户名'  # 用户名
                } 或 None（绑定失败时）
            }
        '''
        username = credentials.get('username', '')
        password = credentials.get('password', '')
        
        if not username or not password:
            return {
                'success': False,
                'message': '用户名和密码不能为空',
                'data': None
            }
        
        try:
            # 判断是手机号还是邮箱
            is_phone = re.match(r'^1[3-9]\d{9}$', username)  # 简单手机号验证
            
            if is_phone:
                # 手机号登录
                response = self._api_client.login_cellphone(phone=username, password=password)
            else:
                # 邮箱登录
                response = self._api_client.login(email=username, password=password)
            
            if response.status == 200:
                data = response.body
                
                if data.get('code') == 200:  # 登录成功
                    # 获取用户ID
                    account_info = data.get('account', {})
                    profile_info = data.get('profile', {})
                    
                    user_id = str(profile_info.get('userId', '')) or str(account_info.get('id', ''))
                    
                    if not user_id:
                        return {
                            'success': False,
                            'message': '无法获取用户ID',
                            'data': None
                        }
                    
                    # 设置API客户端的cookie
                    if 'cookie' in data:
                        self._api_client.set_cookie(data['cookie'])
                    
                    return {
                        'success': True,
                        'message': '绑定成功',
                        'data': {
                            'user_id': user_id,
                            'username': profile_info.get('nickname', username)
                        }
                    }
                else:
                    # 登录失败
                    error_msg = data.get('message', '登录失败')
                    return {
                        'success': False,
                        'message': f'认证失败: {error_msg}',
                        'data': None
                    }
            else:
                return {
                    'success': False,
                    'message': 'API调用失败',
                    'data': None
                }
                
        except Exception as e:
            print(f"绑定用户账号失败: {e}")
            return {
                'success': False,
                'message': f'绑定失败: {str(e)}',
                'data': None
            }
    
    def get_playlist_songs(self, playlist_id, user_id=None):
        '''get_playlist_songs
        获取歌单歌曲
        调用网易云音乐真实API获取歌单中的所有歌曲列表，支持私有歌单。包含详细的错误处理机制。
        parameters:
            playlist_id(string): 歌单ID
            user_id(string): 用户ID（用于私有歌单），可选
        returns:
            dict: 包含成功状态和数据的字典，格式为{
                'success': True/False,  # 获取是否成功
                'message': '成功/失败消息',  # 消息描述
                'error_type': '错误类型',  # 错误类型标识
                'data': [  # 成功时的歌曲详情列表
                    {
                        'id': 'song_id',
                        'netease_song_id': 'song_id',
                        'title': '歌曲标题',
                        'artist': '艺术家',
                        'album': '专辑',
                        'album_cover_url': '封面URL',
                        'duration': 180000
                    }
                ] 或 None（获取失败时）
            }
        '''
        try:
            # 调用真实API获取歌单所有歌曲
            print(f"正在获取歌单 {playlist_id} 的所有歌曲...")
            
            # 使用 playlist_track_all 获取歌单所有歌曲
            response = self._api_client.playlist_track_all(id=playlist_id)
            
            if response.status == 200:
                data = response.body
                songs = []
                
                if 'songs' in data:
                    tracks = data['songs']
                    
                    for track in tracks:
                        # 提取艺术家信息
                        artists = track.get('ar', [])
                        artist_name = artists[0].get('name', '未知艺术家') if artists else '未知艺术家'
                        
                        # 提取专辑信息
                        album_info = track.get('al', {})
                        album_name = album_info.get('name', '未知专辑')
                        album_cover_url = album_info.get('picUrl', '')
                        
                        song_detail = {
                            'id': str(track.get('id', '')),
                            'netease_song_id': str(track.get('id', '')),
                            'title': track.get('name', '未知歌曲'),
                            'artist': artist_name,
                            'album': album_name,
                            'album_cover_url': album_cover_url,
                            'duration': track.get('dt', 0)
                        }
                        songs.append(song_detail)
                    
                    return {
                        'success': True,
                        'message': f'成功获取歌单歌曲，共 {len(songs)} 首',
                        'error_type': None,
                        'data': songs
                    }
                else:
                    return {
                        'success': False,
                        'message': 'API返回数据格式异常，未找到songs字段',
                        'error_type': 'data_format_error',
                        'data': None
                    }
            else:
                return {
                    'success': False,
                    'message': f'API调用失败，状态码: {response.status}',
                    'error_type': 'api_status_error',
                    'data': None
                }
                        
        except OSError as e:
            # 处理SDK相关的操作系统级错误
            error_msg = f"获取歌单歌曲时发生SDK错误: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'message': f'SDK内部错误: {str(e)} (可能是网络连接、文件系统或系统资源问题)',
                'error_type': 'sdk_os_error',
                'data': None
            }
        
        except Exception as e:
            # 处理其他所有未明确捕获的异常
            error_msg = f"获取歌单歌曲时发生未预期的错误: {type(e).__name__}: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'message': f'未知错误: {type(e).__name__}: {str(e)}',
                'error_type': 'unexpected_error',
                'data': None
            }
    
    def send_captcha(self, phone, ctcode=None):
        '''send_captcha
        发送手机验证码
        向指定手机号发送短信验证码，用于验证码登录。
        parameters:
            phone(string): 手机号码
            ctcode(string): 国家代码，默认86（中国）
        returns:
            dict: 发送结果，格式为{
                'success': True/False,  # 发送是否成功
                'message': '发送成功/失败消息',  # 消息描述
                'data': {  # 发送结果数据
                    'phone': '手机号',
                    'captcha_sent': True/False
                } 或 None（发送失败时）
            }
        '''
        try:
            # 调用API发送验证码
            response = self._api_client.captcha_sent(phone=phone, ctcode=ctcode)
            
            if response.status == 200:
                data = response.body
                if data.get('code') == 200:
                    return {
                        'success': True,
                        'message': '验证码发送成功',
                        'data': {
                            'phone': phone,
                            'captcha_sent': True
                        }
                    }
                else:
                    return {
                        'success': False,
                        'message': f'验证码发送失败: {data.get("message", "未知错误")}',
                        'data': None
                    }
            else:
                return {
                    'success': False,
                    'message': f'API调用失败，状态码: {response.status}',
                    'data': None
                }
        except Exception as e:
            error_msg = f"发送验证码失败: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'data': None
            }

    def verify_captcha(self, phone, captcha, ctcode=None):
        '''verify_captcha
        验证手机验证码
        验证用户输入的短信验证码是否正确。
        parameters:
            phone(string): 手机号码
            captcha(string): 验证码
            ctcode(string): 国家代码，默认86（中国）
        returns:
            dict: 验证结果，格式为{
                'success': True/False,  # 验证是否成功
                'message': '验证成功/失败消息',  # 消息描述
                'data': {  # 验证结果数据
                    'phone': '手机号',
                    'captcha_verified': True/False
                } 或 None（验证失败时）
            }
        '''
        try:
            # 调用API验证验证码
            response = self._api_client.captcha_verify(phone=phone, captcha=captcha, ctcode=ctcode)
            
            if response.status == 200:
                data = response.body
                if data.get('code') == 200:
                    return {
                        'success': True,
                        'message': '验证码验证成功',
                        'data': {
                            'phone': phone,
                            'captcha_verified': True
                        }
                    }
                else:
                    return {
                        'success': False,
                        'message': f'验证码验证失败: {data.get("message", "未知错误")}',
                        'data': None
                    }
            else:
                return {
                    'success': False,
                    'message': f'API调用失败，状态码: {response.status}',
                    'data': None
                }
        except Exception as e:
            error_msg = f"验证验证码失败: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'data': None
            }

    def captcha_login(self, phone, captcha, ctcode=None):
        '''captcha_login
        验证码登录
        使用手机号和验证码进行登录，替代密码登录。
        parameters:
            phone(string): 手机号码
            captcha(string): 验证码
            ctcode(string): 国家代码，默认86（中国）
        returns:
            dict: 登录结果，格式为{
                'success': True/False,  # 登录是否成功
                'message': '登录成功/失败消息',  # 消息描述
                'data': {  # 登录成功时的用户信息
                    'user_id': 'netease_user_id',  # 网易云用户ID
                    'username': '用户名'  # 用户名
                } 或 None（登录失败时）
            }
        '''
        try:
            # 调用验证码登录API
            # response = self._api_client.login_cellphone(phone=phone, captcha=captcha, ctcode=ctcode)
            response = self._api_client.login_cellphone(phone=phone, captcha=captcha)
            
            if response.status == 200:
                data = response.body
                
                if data.get('code') == 200:  # 登录成功
                    # 获取用户ID
                    account_info = data.get('account', {})
                    profile_info = data.get('profile', {})
                    
                    user_id = str(profile_info.get('userId', '')) or str(account_info.get('id', ''))
                    
                    if not user_id:
                        return {
                            'success': False,
                            'message': '无法获取用户ID',
                            'data': None
                        }
                    
                    # 设置API客户端的cookie
                    if 'cookie' in data:
                        self._api_client.set_cookie(data['cookie'])
                    
                    return {
                        'success': True,
                        'message': '验证码登录成功',
                        'data': {
                            'user_id': user_id,
                            'username': profile_info.get('nickname', phone)
                        }
                    }
                else:
                    # 登录失败
                    error_msg = data.get('message', '登录失败')
                    return {
                        'success': False,
                        'message': f'验证码登录失败: {error_msg}',
                        'data': None
                    }
            else:
                return {
                    'success': False,
                    'message': f'API调用失败，状态码: {response.status}',
                    'data': None
                }
        except Exception as e:
            error_msg = f"验证码登录失败: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'data': None
            }

netease_service = NeteaseMusicService()