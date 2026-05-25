"""
User Service Module
Handles user-related business logic including registration, authentication, and profile management.
"""

from typing import Optional, Dict, Any
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from sqlalchemy.orm import Session
from models import User, NeteaseAccount
from .interfaces import IUserService


class UserService(IUserService):
    """User service class for handling user operations."""

    def __init__(self, db_session: Session, bcrypt: Bcrypt):
        self.db = db_session
        self.bcrypt = bcrypt

    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            username: Username for the new user
            email: Email address for the new user
            password: Plain text password

        Returns:
            Dict containing user data and access token, or error message

        Raises:
            ValueError: If validation fails
        """
        # Validate input
        if not username or not email or not password:
            raise ValueError("Missing required fields")

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already exists")

        if User.query.filter_by(email=email).first():
            raise ValueError("Email already exists")

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)

        self.db.session.add(user)
        self.db.session.commit()

        # Generate access token
        access_token = user.generate_auth_token()

        return {
            "message": "User registered successfully",
            "user": user.to_dict(),
            "access_token": access_token
        }

    def authenticate_user(self, identifier: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user with username/email and password.

        Args:
            identifier: Username or email
            password: Plain text password

        Returns:
            Dict containing user data and access token

        Raises:
            ValueError: If authentication fails
        """
        # Find user by username or email
        if '@' in identifier:
            user = User.query.filter_by(email=identifier).first()
        else:
            user = User.query.filter_by(username=identifier).first()

        if not user or not user.check_password(password):
            raise ValueError("Invalid credentials")

        # Generate access token
        access_token = user.generate_auth_token()

        return {
            "message": "Login successful",
            "user": user.to_dict(),
            "access_token": access_token
        }

    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Get user profile information.

        Args:
            user_id: User ID

        Returns:
            Dict containing user profile data

        Raises:
            ValueError: If user not found
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        response = user.to_dict()

        # Add Netease account info if exists
        if user.netease_account:
            response['netease_account'] = user.netease_account.to_dict()

        return response

    def bind_netease_account(self, user_id: int, netease_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bind Netease account to user.

        Args:
            user_id: User ID
            netease_data: Netease account data

        Returns:
            Dict containing binding result

        Raises:
            ValueError: If binding fails
        """
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        netease_user_id = netease_data.get('user_id')
        netease_username = netease_data.get('username', '')

        if not netease_user_id:
            raise ValueError("Missing Netease user ID")

        # Check if Netease account is already bound to another user
        existing_binding = NeteaseAccount.query.filter_by(netease_user_id=netease_user_id).first()
        if existing_binding and existing_binding.user_id != user_id:
            raise ValueError("Netease account already bound to another user")

        # Check if user already has a binding
        existing_account = NeteaseAccount.query.filter_by(user_id=user_id).first()

        if existing_account:
            # Update existing binding
            existing_account.netease_user_id = netease_user_id
            existing_account.netease_username = netease_username
            existing_account.is_bound = True
        else:
            # Create new binding
            new_account = NeteaseAccount(
                user_id=user_id,
                netease_user_id=netease_user_id,
                netease_username=netease_username,
                is_bound=True
            )
            self.db.session.add(new_account)

        self.db.session.commit()

        return {
            "message": "Netease account bound successfully",
            "netease_account": {
                "netease_user_id": netease_user_id,
                "netease_username": netease_username,
                "is_bound": True
            }
        }