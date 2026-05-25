"""
Netease Music Service Module
Handles Netease Cloud Music API interactions with caching and error handling.
"""

import json
import os
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from MusicLibrary.neteaseCloudMusicApi import NeteaseCloudMusicApi
from .interfaces import INeteaseService


class CacheManager:
    """Simple LRU cache manager for API responses."""

    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Any] = {}
        self._max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with LRU eviction."""
        if len(self._cache) >= self._max_size:
            # Simple LRU: remove oldest item
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[key] = value

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()


class NeteaseMusicService(INeteaseService):
    """
    Netease Cloud Music service class.
    Provides API interactions with caching, retry logic, and error handling.
    """

    def __init__(self):
        self.api_base = "https://music.163.com/api"

        # Initialize caches
        self._song_cache = CacheManager(max_size=1000)
        self._search_cache = CacheManager(max_size=500)

        # Initialize API client
        try:
            self._api_client = NeteaseCloudMusicApi()
        except Exception as e:
            print(f"Failed to initialize API client: {e}")
            raise RuntimeError("Cannot initialize Netease API client")

        # User session storage
        self._user_cookies: Dict[str, str] = {}

    def _make_api_call_with_retry(self, api_call_func, max_retries: int = 3,
                                  retry_delay: float = 1.0) -> Tuple[bool, Any]:
        """
        Execute API call with retry logic.

        Args:
            api_call_func: Function that makes the API call
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            Tuple of (success: bool, response_data: Any)
        """
        for attempt in range(max_retries):
            try:
                response = api_call_func()

                if response.status == 200:
                    return True, response.body
                else:
                    if attempt == max_retries - 1:
                        return False, f"API returned status {response.status}"

            except Exception as e:
                if attempt == max_retries - 1:
                    return False, str(e)
                time.sleep(retry_delay)

        return False, "Max retries exceeded"

    def _parse_song_data(self, song: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw song data into standardized format."""
        # Extract artist info
        artists = song.get('ar', [])
        artist_name = artists[0].get('name', 'Unknown Artist') if artists else 'Unknown Artist'

        # Extract album info
        album_info = song.get('al', {})
        album_name = album_info.get('name', 'Unknown Album')
        album_cover_url = album_info.get('picUrl', '')

        return {
            'id': str(song.get('id', '')),
            'netease_song_id': str(song.get('id', '')),
            'title': song.get('name', 'Unknown Song'),
            'artist': artist_name,
            'album': album_name,
            'album_cover_url': album_cover_url,
            'duration': song.get('dt', song.get('duration', 0))
        }

    def search_songs(self, keyword: str, limit: int = 30, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search songs by keyword.

        Args:
            keyword: Search keyword
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of song dictionaries
        """
        cache_key = f"search:{keyword}:{limit}:{offset}"
        cached_result = self._search_cache.get(cache_key)
        if cached_result:
            return cached_result

        def api_call():
            return self._api_client.search(keywords=keyword, limit=limit, offset=offset, type=1)

        success, data = self._make_api_call_with_retry(api_call)

        if not success:
            print(f"Search failed after retries: {data}")
            return []

        result = []
        if 'result' in data and 'songs' in data['result']:
            songs = data['result']['songs']
            for song in songs:
                song_data = self._parse_song_data(song)
                result.append(song_data)

        self._search_cache.set(cache_key, result)
        return result

    def get_song_detail(self, song_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a song.

        Args:
            song_id: Netease song ID

        Returns:
            Song detail dictionary
        """
        cache_key = f"song:{song_id}"
        cached_result = self._song_cache.get(cache_key)
        if cached_result:
            return cached_result

        def api_call():
            return self._api_client.song_detail(ids=song_id)

        success, data = self._make_api_call_with_retry(api_call)

        if success and 'songs' in data and len(data['songs']) > 0:
            song = data['songs'][0]
            result = self._parse_song_data(song)
            self._song_cache.set(cache_key, result)
            return result

        # Return fallback data if API fails
        print(f"Failed to get song detail for {song_id}: {data}")
        return {
            'id': song_id,
            'netease_song_id': song_id,
            'title': f'Song {song_id}',
            'artist': 'Unknown Artist',
            'album': 'Unknown Album',
            'album_cover_url': 'https://example.com/cover.jpg',
            'duration': 180000
        }

    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information including playlists.

        Args:
            user_id: Netease user ID

        Returns:
            User info dictionary or None if not found
        """
        def api_call():
            return self._api_client.user_detail(uid=user_id)

        success, data = self._make_api_call_with_retry(api_call)

        if not success or 'profile' not in data:
            print(f"Failed to get user info for {user_id}: {data}")
            return None

        profile = data['profile']

        # Get user playlists
        playlists = []
        try:
            def playlist_call():
                return self._api_client.user_playlist(uid=user_id, limit=10)

            playlist_success, playlist_data = self._make_api_call_with_retry(playlist_call)

            if playlist_success and 'playlist' in playlist_data:
                for playlist in playlist_data['playlist']:
                    playlist_info = {
                        'playlist_id': str(playlist.get('id', '')),
                        'playlist_name': playlist.get('name', 'Unnamed Playlist')
                    }
                    playlists.append(playlist_info)
        except Exception as e:
            print(f"Error getting user playlists: {e}")

        return {
            'user_id': str(profile.get('userId', user_id)),
            'username': profile.get('nickname', 'Unknown User'),
            'playlists': playlists
        }

    def bind_user_account(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Bind user account with credentials.

        Args:
            credentials: Dict with 'username' and 'password'

        Returns:
            Binding result dictionary
        """
        username = credentials.get('username', '')
        password = credentials.get('password', '')

        if not username or not password:
            return {
                'success': False,
                'message': 'Username and password are required',
                'data': None
            }

        # Determine login method
        is_phone = bool(re.match(r'^1[3-9]\d{9}$', username))

        def login_call():
            if is_phone:
                return self._api_client.login_cellphone(phone=username, password=password)
            else:
                return self._api_client.login(email=username, password=password)

        success, data = self._make_api_call_with_retry(login_call)

        if not success or data.get('code') != 200:
            error_msg = data if isinstance(data, str) else data.get('message', 'Login failed')
            return {
                'success': False,
                'message': f'Authentication failed: {error_msg}',
                'data': None
            }

        # Extract user info
        account_info = data.get('account', {})
        profile_info = data.get('profile', {})

        user_id = str(profile_info.get('userId', '')) or str(account_info.get('id', ''))

        if not user_id:
            return {
                'success': False,
                'message': 'Unable to get user ID',
                'data': None
            }

        # Set API client cookie
        if 'cookie' in data:
            self._api_client.set_cookie(data['cookie'])

        return {
            'success': True,
            'message': 'Account bound successfully',
            'data': {
                'user_id': user_id,
                'username': profile_info.get('nickname', username)
            }
        }

    def get_playlist_songs(self, playlist_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all songs from a playlist.

        Args:
            playlist_id: Playlist ID
            user_id: User ID (for private playlists)

        Returns:
            Result dictionary with success status and song list
        """
        def api_call():
            return self._api_client.playlist_track_all(id=playlist_id)

        success, data = self._make_api_call_with_retry(api_call)

        if not success:
            return {
                'success': False,
                'message': f'API call failed: {data}',
                'error_type': 'api_error',
                'data': None
            }

        if 'songs' not in data:
            return {
                'success': False,
                'message': 'Invalid response format: missing songs field',
                'error_type': 'data_format_error',
                'data': None
            }

        songs = []
        for track in data['songs']:
            song_detail = self._parse_song_data(track)
            songs.append(song_detail)

        return {
            'success': True,
            'message': f'Successfully retrieved {len(songs)} songs',
            'error_type': None,
            'data': songs
        }

    def send_captcha(self, phone: str, ctcode: Optional[str] = None) -> Dict[str, Any]:
        """
        Send SMS captcha to phone number.

        Args:
            phone: Phone number
            ctcode: Country code (default: 86)

        Returns:
            Send result dictionary
        """
        def api_call():
            return self._api_client.captcha_sent(phone=phone, ctcode=ctcode)

        success, data = self._make_api_call_with_retry(api_call)

        if success and data.get('code') == 200:
            return {
                'success': True,
                'message': 'Captcha sent successfully',
                'data': {
                    'phone': phone,
                    'captcha_sent': True
                }
            }

        error_msg = data if isinstance(data, str) else data.get('message', 'Unknown error')
        return {
            'success': False,
            'message': f'Failed to send captcha: {error_msg}',
            'data': None
        }

    def verify_captcha(self, phone: str, captcha: str, ctcode: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify SMS captcha.

        Args:
            phone: Phone number
            captcha: Captcha code
            ctcode: Country code (default: 86)

        Returns:
            Verification result dictionary
        """
        def api_call():
            return self._api_client.captcha_verify(phone=phone, captcha=captcha, ctcode=ctcode)

        success, data = self._make_api_call_with_retry(api_call)

        if success and data.get('code') == 200:
            return {
                'success': True,
                'message': 'Captcha verified successfully',
                'data': {
                    'phone': phone,
                    'captcha_verified': True
                }
            }

        error_msg = data if isinstance(data, str) else data.get('message', 'Unknown error')
        return {
            'success': False,
            'message': f'Captcha verification failed: {error_msg}',
            'data': None
        }

    def captcha_login(self, phone: str, captcha: str, ctcode: Optional[str] = None) -> Dict[str, Any]:
        """
        Login using phone number and captcha.

        Args:
            phone: Phone number
            captcha: Captcha code
            ctcode: Country code (default: 86)

        Returns:
            Login result dictionary
        """
        def api_call():
            return self._api_client.login_cellphone(phone=phone, captcha=captcha)

        success, data = self._make_api_call_with_retry(api_call)

        if not success or data.get('code') != 200:
            error_msg = data if isinstance(data, str) else data.get('message', 'Login failed')
            return {
                'success': False,
                'message': f'Captcha login failed: {error_msg}',
                'data': None
            }

        # Extract user info
        account_info = data.get('account', {})
        profile_info = data.get('profile', {})

        user_id = str(profile_info.get('userId', '')) or str(account_info.get('id', ''))

        if not user_id:
            return {
                'success': False,
                'message': 'Unable to get user ID',
                'data': None
            }

        # Set API client cookie
        if 'cookie' in data:
            self._api_client.set_cookie(data['cookie'])

        return {
            'success': True,
            'message': 'Captcha login successful',
            'data': {
                'user_id': user_id,
                'username': profile_info.get('nickname', phone)
            }
        }


# Global service instance
netease_service = NeteaseMusicService()