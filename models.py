from datetime import datetime
from app import db, bcrypt
from flask_jwt_extended import create_access_token
import json

class User(db.Model):
    '''User
    用户模型类
    表示应用用户，存储用户认证信息和基本信息。
    variables:
        id: Integer, 用户唯一标识
        username: String(80), 用户名，唯一
        email: String(120), 邮箱地址，唯一
        password_hash: String(128), 密码哈希值
        created_at: DateTime, 创建时间
        updated_at: DateTime, 更新时间
    functions:
        set_password: 设置用户密码
        check_password: 验证用户密码
        generate_auth_token: 生成JWT认证令牌
        to_dict: 将用户对象转换为字典
    '''
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    netease_account = db.relationship('NeteaseAccount', backref='user', uselist=False, cascade="all, delete-orphan")
    notes = db.relationship('Note', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        """设置密码（加密存储）"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """验证密码"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def generate_auth_token(self):
        """生成认证令牌"""
        return create_access_token(identity=str(self.id))
    
    def to_dict(self):
        """将对象转换为字典（用于JSON序列化）"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class NeteaseAccount(db.Model):
    '''NeteaseAccount
    网易云账户绑定模型类
    存储用户与网易云音乐账号的绑定关系。
    variables:
        id: Integer, 绑定记录唯一标识
        user_id: Integer, 关联的用户ID
        netease_user_id: String(100), 网易云用户ID，唯一
        netease_username: String(100), 网易云用户名
        is_bound: Boolean, 是否已绑定
        bound_at: DateTime, 绑定时间
        updated_at: DateTime, 更新时间
    functions:
        to_dict: 将绑定信息转换为字典
    '''
    __tablename__ = 'netease_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    netease_user_id = db.Column(db.String(100), unique=True, nullable=False)
    netease_username = db.Column(db.String(100))
    is_bound = db.Column(db.Boolean, default=False)
    bound_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'netease_user_id': self.netease_user_id,
            'netease_username': self.netease_username,
            'is_bound': self.is_bound,
            'bound_at': self.bound_at.isoformat() if self.bound_at else None
        }

class Song(db.Model):
    '''Song
    歌曲信息模型类
    存储用户添加过笔记的歌曲信息，包括基本信息和统计信息。
    variables:
        id: Integer, 歌曲唯一标识
        netease_song_id: String(100), 网易云歌曲ID，唯一
        title: String(200), 歌曲标题
        artist: String(200), 艺术家
        album: String(200), 专辑
        album_cover_url: String(500), 专辑封面URL
        duration: Integer, 歌曲时长（毫秒）
        created_at: DateTime, 创建时间
        updated_at: DateTime, 更新时间
        note_count: Integer, 笔记数量统计
    functions:
        to_dict: 将歌曲信息转换为完整字典
        to_simple_dict: 将歌曲信息转换为简化字典
    '''
    __tablename__ = 'songs'
    
    id = db.Column(db.Integer, primary_key=True)
    netease_song_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200))
    album = db.Column(db.String(200))
    album_cover_url = db.Column(db.String(500))
    duration = db.Column(db.Integer)  # 时长（毫秒）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    note_count = db.Column(db.Integer, default=0)  # 笔记数量，用于统计
    
    # 关联关系
    notes = db.relationship('Note', backref='song', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'netease_song_id': self.netease_song_id,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'album_cover_url': self.album_cover_url,
            'duration': self.duration,
            'note_count': self.note_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_simple_dict(self):
        """简化版歌曲信息"""
        return {
            'netease_song_id': self.netease_song_id,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'album_cover_url': self.album_cover_url
        }

class Note(db.Model):
    '''Note
    笔记模型类
    存储用户对歌曲的笔记，包括内容、时间戳和权限设置。
    variables:
        id: Integer, 笔记唯一标识
        user_id: Integer, 用户ID
        song_id: Integer, 歌曲ID
        content: Text, 笔记内容
        timestamp: Integer, 歌曲时间戳（毫秒）
        is_public: Boolean, 是否公开
        created_at: DateTime, 创建时间
        updated_at: DateTime, 更新时间
    functions:
        to_dict: 将笔记转换为字典，可选择包含歌曲信息
    '''
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id', ondelete='CASCADE'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.Integer, default=0)  # 歌曲时间戳（毫秒），0表示不指定
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引优化
    __table_args__ = (
        db.Index('idx_user_song', 'user_id', 'song_id'),
        db.Index('idx_song_public', 'song_id', 'is_public'),
    )
    
    def to_dict(self, include_song=True):
        """转换为字典，可选择是否包含歌曲信息"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'song_id': self.song_id,
            'content': self.content,
            'timestamp': self.timestamp,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_song and self.song:
            result['song'] = self.song.to_simple_dict()
            
        return result