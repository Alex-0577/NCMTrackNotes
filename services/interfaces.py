"""
Service Layer Interfaces
Defines abstract interfaces for service layer classes to ensure consistency and enable dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class IUserService(ABC):
    """Abstract interface for user service operations."""

    @abstractmethod
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user."""
        pass

    @abstractmethod
    def authenticate_user(self, identifier: str, password: str) -> Dict[str, Any]:
        """Authenticate a user with username/email and password."""
        pass

    @abstractmethod
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user profile information."""
        pass

    @abstractmethod
    def bind_netease_account(self, user_id: int, netease_data: Dict[str, Any]) -> Dict[str, Any]:
        """Bind Netease account to user."""
        pass


class INeteaseService(ABC):
    """Abstract interface for Netease music service operations."""

    @abstractmethod
    def search_songs(self, keyword: str, limit: int = 30, offset: int = 0) -> List[Dict[str, Any]]:
        """Search songs by keyword."""
        pass

    @abstractmethod
    def get_song_detail(self, song_id: str) -> Dict[str, Any]:
        """Get detailed information for a song."""
        pass

    @abstractmethod
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information including playlists."""
        pass

    @abstractmethod
    def bind_user_account(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Bind user account with credentials."""
        pass

    @abstractmethod
    def get_playlist_songs(self, playlist_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all songs from a playlist."""
        pass

    @abstractmethod
    def send_captcha(self, phone: str, ctcode: Optional[str] = None) -> Dict[str, Any]:
        """Send SMS captcha to phone number."""
        pass

    @abstractmethod
    def verify_captcha(self, phone: str, captcha: str, ctcode: Optional[str] = None) -> Dict[str, Any]:
        """Verify SMS captcha."""
        pass

    @abstractmethod
    def captcha_login(self, phone: str, captcha: str, ctcode: Optional[str] = None) -> Dict[str, Any]:
        """Login using phone number and captcha."""
        pass