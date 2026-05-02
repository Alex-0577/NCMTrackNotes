import os
from datetime import timedelta

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///NCMTrackNotes.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 应用配置
    DEBUG = True
    
    # 安全配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-me'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_IDENTITY_CLAIM = 'sub'  # 指定identity字段名
    JWT_HEADER_NAME = 'Authorization'  # 指定请求头中的字段名
    JWT_HEADER_TYPE = 'Bearer'  # 指定令牌类型
    
    # 网易云音乐API配置（占位）
    NETEASE_API_BASE_URL = 'https://music.163.com/api'
    NETEASE_API_TIMEOUT = 10

config = Config()