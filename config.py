'''config.py
应用配置
包含Flask应用的所有配置项，包括数据库连接、安全密钥、JWT设置和应用参数。
'''
import os
from datetime import timedelta

class Config:
    '''Config
    配置类
    包含Flask应用的所有配置设置，支持从环境变量读取配置。
    variables:
        SECRET_KEY: String, Flask应用密钥
        SQLALCHEMY_DATABASE_URI: String, 数据库连接URI
        SQLALCHEMY_TRACK_MODIFICATIONS: Boolean, SQLAlchemy跟踪修改开关
        DEBUG: Boolean, 调试模式开关
        JWT_SECRET_KEY: String, JWT密钥
        JWT_ACCESS_TOKEN_EXPIRES: timedelta, JWT访问令牌过期时间
        JWT_REFRESH_TOKEN_EXPIRES: timedelta, JWT刷新令牌过期时间
        JWT_IDENTITY_CLAIM: String, JWT身份声明字段名
        JWT_HEADER_NAME: String, JWT请求头字段名
        JWT_HEADER_TYPE: String, JWT令牌类型
        NETEASE_API_BASE_URL: String, 网易云音乐API基础URL
        NETEASE_API_TIMEOUT: Integer, 网易云音乐API超时时间
    '''
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