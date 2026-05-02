# 音乐记事本 API 文档

## 基础信息

- **基础URL**: `http://localhost:5000/api`
- **认证方式**: JWT Token
- **Content-Type**: `application/json`
- **返回格式**: JSON

## 认证相关API

### 1. 用户注册

注册新用户账号。

**请求**:
- **方法**: `POST`
- **端点**: `/auth/register`
- **认证**: 不需要
- **请求体**:
```json
{
    "username": "string, 用户名",
    "email": "string, 邮箱地址",
    "password": "string, 密码"
}
```
- **响应**:
  - **成功 (201)**:
```json
{
    "message": "User registered successfully",
    "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "created_at": "2023-10-01T12:00:00Z"
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```
  - **错误 (400)**: 缺少必填字段
  - **错误 (409)**: 用户名或邮箱已存在

---

### 2. 用户登录

用户登录获取访问令牌。

**请求**:
- **方法**: `POST`
- **端点**: `/auth/login`
- **认证**: 不需要
- **请求体**:
```json
{
    "identifier": "string, 用户名或邮箱",
    "password": "string, 密码"
}
```
- **响应**:
  - **成功 (200)**:
```json
{
    "message": "Login successful",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "created_at": "2023-10-01T12:00:00Z"
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```
  - **错误 (400)**: 缺少用户名/邮箱或密码
  - **错误 (401)**: 认证失败

---

### 3. 获取用户资料

获取当前登录用户的资料。

**请求**:
- **方法**: `GET`
- **端点**: `/auth/profile`
- **认证**: 需要 (Bearer Token)
- **请求头**: `Authorization: Bearer <access_token>`

**响应**:
- **成功 (200)**:
```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "created_at": "2023-10-01T12:00:00Z",
    "netease_account": {
        "netease_user_id": "netease_123456",
        "netease_username": "netease_user",
        "is_bound": true,
        "bound_at": "2023-10-01T12:00:00Z"
    }
}
```
  - **错误 (401)**: 未认证
  - **错误 (404)**: 用户不存在

---

### 4. 绑定网易云音乐账号

绑定网易云音乐账号到用户账户。

**请求**:
- **方法**: `POST`
- **端点**: `/auth/bind-netease`
- **认证**: 需要 (Bearer Token)
- **请求体**:
```json
{
    "netease_username": "string, 网易云用户名",
    "netease_password": "string, 网易云密码"
}
```
**响应**:
- **成功 (200)**:
```json
{
    "message": "Netease account bound successfully",
    "netease_account": {
        "netease_username": "netease_user",
        "is_bound": true
    }
}
```
  - **错误 (400)**: 缺少网易云账号信息
  - **错误 (401)**: 未认证

---

### 5. 解绑网易云音乐账号

解绑已绑定的网易云音乐账号。

**请求**:
- **方法**: `POST`
- **端点**: `/auth/unbind-netease`
- **认证**: 需要 (Bearer Token)

**响应**:
- **成功 (200)**:
```json
{
    "message": "Netease account unbound successfully"
}
```
- **错误 (404)**: 未绑定网易云账号
- **错误 (401)**: 未认证

---

## 音乐相关API

### 6. 搜索歌曲

搜索网易云音乐中的歌曲。

**请求**:
- **方法**: `GET`
- **端点**: `/music/search`
- **认证**: 需要 (Bearer Token)
- **查询参数**:
  - `q`: 搜索关键词 (必需)
  - `limit`: 返回数量，默认30，最大100
  - `offset`: 偏移量，默认0

**示例请求**:
```
GET /api/music/search?q=周杰伦&limit=20&offset=0

Authorization: Bearer <access_token>
```
**响应**:
- **成功 (200)**:
```json
{
    "keyword": "周杰伦",
    "total": 20,
    "offset": 0,
    "limit": 20,
    "songs": [
        {
            "id": "song_123",
            "netease_song_id": "song_123",
            "title": "七里香",
            "artist": "周杰伦",
            "album": "七里香",
            "album_cover_url": "https://example.com/cover.jpg",
            "duration": 240000
        }
    ],
    "source": "combined"
}
```
- **错误 (400)**: 缺少搜索关键词或关键词过长
- **错误 (401)**: 未认证
- **错误 (500)**: 服务器内部错误

---

### 7. 获取歌曲详情

获取指定歌曲的详细信息。

**请求**:
- **方法**: `GET`
- **端点**: `/music/song/<song_id>`
- **认证**: 需要 (Bearer Token)
- **路径参数**:
  - `song_id`: 网易云音乐歌曲ID

**示例请求**:
```
GET /api/music/song/123456
Authorization: Bearer <access_token>
```
**响应**:
- **成功 (200)**:
```json
{
    "song": {
        "id": 1,
        "netease_song_id": "123456",
        "title": "七里香",
        "artist": "周杰伦",
        "album": "七里香",
        "album_cover_url": "https://example.com/cover.jpg",
        "duration": 240000,
        "note_count": 5,
        "created_at": "2023-10-01T12:00:00Z",
        "updated_at": "2023-10-01T12:00:00Z"
    },
    "source": "database"
}
```
- **错误 (400)**: 歌曲ID不能为空
- **错误 (404)**: 未找到歌曲
- **错误 (401)**: 未认证

---

### 8. 批量获取歌曲信息

批量获取多首歌曲的信息。

**请求**:
- **方法**: `POST`
- **端点**: `/music/batch-songs`
- **认证**: 需要 (Bearer Token)
- **请求体**:
```json
{
    "song_ids": ["123", "456", "789"]
}
```
**响应**:
- **成功 (200)**:
```json
{
    "songs": [
        {
            "netease_song_id": "123",
            "title": "七里香",
            "artist": "周杰伦",
            "album": "七里香",
            "album_cover_url": "https://example.com/cover.jpg",
            "duration": 240000
        }
    ],
    "source_counts": {
        "cache": 0,
        "database": 1,
        "api": 2
    },
    "found_count": 3,
    "requested_count": 3
}
```
- **错误 (400)**: 未提供歌曲ID列表或格式错误
- **错误 (401)**: 未认证

---

## 笔记管理API

### 9. 创建笔记

为指定歌曲创建笔记。

**请求**:
- **方法**: `POST`
- **端点**: `/notes`
- **认证**: 需要 (Bearer Token)
- **请求体**:
```json
{
    "netease_song_id": "string, 网易云歌曲ID",
    "content": "string, 笔记内容",
    "timestamp": 0,
    "is_public": false
}
```
**响应**:
- **成功 (201)**:
```json
{
    "message": "笔记创建成功",
    "note": {
        "id": 1,
        "user_id": 1,
        "song_id": 1,
        "content": "这是一条笔记",
        "timestamp": 123456,
        "is_public": false,
        "created_at": "2023-10-01T12:00:00Z",
        "updated_at": "2023-10-01T12:00:00Z",
        "song": {
            "netease_song_id": "123456",
            "title": "七里香",
            "artist": "周杰伦",
            "album": "七里香",
            "album_cover_url": "https://example.com/cover.jpg"
        }
    }
}
```
- **错误 (400)**: 缺少必填字段或内容为空
- **错误 (401)**: 未认证
- **错误 (500)**: 服务器内部错误

---

### 10. 获取用户笔记

获取当前用户的所有笔记。

**请求**:
- **方法**: `GET`
- **端点**: `/notes`
- **认证**: 需要 (Bearer Token)
- **查询参数**:
  - `page`: 页码，默认1
  - `per_page`: 每页数量，默认20
  - `song_id`: 按歌曲ID筛选（可选）

**示例请求**:
```
GET /api/notes?page=1&per_page=20&song_id=123456
Authorization: Bearer <access_token>
```
**响应**:
- **成功 (200)**:
```json
{
    "notes": [
        {
            "id": 1,
            "user_id": 1,
            "song_id": 1,
            "content": "这是一条笔记",
            "timestamp": 123456,
            "is_public": false,
            "created_at": "2023-10-01T12:00:00Z",
            "updated_at": "2023-10-01T12:00:00Z",
            "song": {
                "netease_song_id": "123456",
                "title": "七里香",
                "artist": "周杰伦",
                "album": "七里香",
                "album_cover_url": "https://example.com/cover.jpg"
            }
        }
    ],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
}
```
- **错误 (401)**: 未认证

---

### 11. 获取单个笔记

获取指定ID的笔记。

**请求**:
- **方法**: `GET`
- **端点**: `/notes/<note_id>`
- **认证**: 需要 (Bearer Token)
- **路径参数**:
  - `note_id`: 笔记ID

**响应**:
- **成功 (200)**:
```json
{
    "note": {
        "id": 1,
        "user_id": 1,
        "song_id": 1,
        "content": "这是一条笔记",
        "timestamp": 123456,
        "is_public": false,
        "created_at": "2023-10-01T12:00:00Z",
        "updated_at": "2023-10-01T12:00:00Z",
        "song": {
            "netease_song_id": "123456",
            "title": "七里香",
            "artist": "周杰伦",
            "album": "七里香",
            "album_cover_url": "https://example.com/cover.jpg"
        }
    }
}
```
- **错误 (401)**: 未认证
- **错误 (403)**: 笔记是私有的
- **错误 (404)**: 笔记不存在

---

### 12. 更新笔记

更新指定ID的笔记。

**请求**:
- **方法**: `PUT`
- **端点**: `/notes/<note_id>`
- **认证**: 需要 (Bearer Token)
- **请求体** (可选字段):
```json
{
    "content": "string, 更新后的内容",
    "timestamp": 123456,
    "is_public": true
}
```
**响应**:
- **成功 (200)**:
```json
{
    "message": "笔记更新成功",
    "note": {
        "id": 1,
        "user_id": 1,
        "song_id": 1,
        "content": "更新后的内容",
        "timestamp": 123456,
        "is_public": true,
        "created_at": "2023-10-01T12:00:00Z",
        "updated_at": "2023-10-01T12:30:00Z",
        "song": {
            "netease_song_id": "123456",
            "title": "七里香",
            "artist": "周杰伦",
            "album": "七里香",
            "album_cover_url": "https://example.com/cover.jpg"
        }
    }
}
```
- **错误 (400)**: 内容为空或格式错误
- **错误 (401)**: 未认证
- **错误 (403)**: 无权限
- **错误 (404)**: 笔记不存在
- **错误 (500)**: 服务器内部错误

---

### 13. 删除笔记

删除指定ID的笔记。

**请求**:
- **方法**: `DELETE`
- **端点**: `/notes/<note_id>`
- **认证**: 需要 (Bearer Token)

**响应**:
- **成功 (200)**:
```json
{
    "message": "笔记删除成功"
}
```
- **错误 (401)**: 未认证
- **错误 (403)**: 无权限
- **错误 (404)**: 笔记不存在
- **错误 (500)**: 服务器内部错误

---

### 14. 获取公开笔记

获取所有公开的笔记。

**请求**:
- **方法**: `GET`
- **端点**: `/notes/public`
- **认证**: 不需要
- **查询参数**:
  - `page`: 页码，默认1
  - `per_page`: 每页数量，默认20
  - `song_id`: 按歌曲ID筛选（可选）
  - `user_id`: 按用户ID筛选（可选）

**示例请求**:
```
GET /api/notes/public?page=1&per_page=20&song_id=123456
```
**响应**:
- **成功 (200)**:
```json
{
    "notes": [
        {
            "id": 1,
            "user_id": 1,
            "song_id": 1,
            "content": "这是一条公开笔记",
            "timestamp": 123456,
            "is_public": true,
            "created_at": "2023-10-01T12:00:00Z",
            "updated_at": "2023-10-01T12:00:00Z",
            "song": {
                "netease_song_id": "123456",
                "title": "七里香",
                "artist": "周杰伦",
                "album": "七里香",
                "album_cover_url": "https://example.com/cover.jpg"
            },
            "user": {
                "id": 1,
                "username": "testuser"
            }
        }
    ],
    "total": 50,
    "page": 1,
    "per_page": 20,
    "pages": 3
}
```
---

### 15. 通过歌曲获取笔记

获取指定歌曲的所有笔记。

**请求**:
- **方法**: `GET`
- **端点**: `/notes/by-song/<song_id>`
- **认证**: 不需要
- **路径参数**:
  - `song_id`: 网易云音乐歌曲ID
- **查询参数**:
  - `page`: 页码，默认1
  - `per_page`: 每页数量，默认20
  - `include_private`: 是否包含私有笔记，默认false
  - `user_id`: 当include_private=true时，必须指定用户ID

**示例请求**:

```
# 获取公开笔记
GET /api/notes/by-song/123456?page=1&per_page=20
# 获取指定用户的私有笔记
GET /api/notes/by-song/123456?page=1&include_private=true&user_id=1
```
**响应**:
- **成功 (200)**:
```json
{
    "song_id": "123456",
    "song_info": {
        "id": 1,
        "netease_song_id": "123456",
        "title": "七里香",
        "artist": "周杰伦",
        "album": "七里香",
        "album_cover_url": "https://example.com/cover.jpg",

"duration": 240000,
        "note_count": 5,
        "created_at": "2023-10-01T12:00:00Z",
        "updated_at": "2023-10-01T12:00:00Z"
    },
    "notes": [
        {
            "id": 1,
            "user_id": 1,
            "song_id": 1,
            "content": "这是一条笔记",
            "timestamp": 123456,
            "is_public": true,
            "created_at": "2023-10-01T12:00:00Z",
            "updated_at": "2023-10-01T12:00:00Z",
            "user": {
                "id": 1,
                "username": "testuser"
            }
        }
    ],
    "total": 5,
    "page": 1,
    "per_page": 20,
    "pages": 1
}
```
---

### 16. 获取指定用户对指定歌曲的笔记

获取指定用户对指定歌曲的笔记。

**请求**:
- **方法**: `GET`
- **端点**: `/notes/user/<user_id>/by-song/<song_id>`
- **认证**: 需要 (Bearer Token)
- **路径参数**:
  - `user_id`: 用户ID
  - `song_id`: 网易云音乐歌曲ID
- **查询参数**:
  - `page`: 页码，默认1
  - `per_page`: 每页数量，默认20

**示例请求**:
```
GET /api/notes/user/1/by-song/123456?page=1&per_page=20
Authorization: Bearer <access_token>
```
**响应**:
- **成功 (200)**:
```json
{
    "song_id": "123456",
    "song_info": {
        "id": 1,
        "netease_song_id": "123456",
        "title": "七里香",
        "artist": "周杰伦",
        "album": "七里香",
        "album_cover_url": "https://example.com/cover.jpg",

"duration": 240000,
        "note_count": 2,
        "created_at": "2023-10-01T12:00:00Z",
        "updated_at": "2023-10-01T12:00:00Z"
    },
    "notes": [
        {
            "id": 1,
            "user_id": 1,
            "song_id": 1,
            "content": "这是一条笔记",
            "timestamp": 123456,
            "is_public": true,
            "created_at": "2023-10-01T12:00:00Z",
            "updated_at": "2023-10-01T12:00:00Z"
        }
    ],
    "total": 2,
    "page": 1,
    "per_page": 20,
    "pages": 1
}
```
- **特殊规则**:
  - 如果查询自己的用户ID，可以查看所有笔记（包括私有）
  - 如果查询其他用户的ID，只能查看公开笔记

---

## 健康检查

### 17. 健康检查

检查服务是否正常运行。

**请求**:
- **方法**: `GET`
- **端点**: `/health`
- **认证**: 不需要

**响应**:
- **成功 (200)**:
```json
{
    "status": "healthy",
    "service": "music-notepad-backend"
}
```
---

## 错误处理

### 通用错误响应格式
```json
{
    "error": "错误描述信息"
}
```
### 常见HTTP状态码

- **200**: 请求成功
- **201**: 创建成功
- **400**: 请求参数错误
- **401**: 未认证或认证失败
- **403**: 无权限访问
- **404**: 资源不存在
- **409**: 资源冲突
- **500**: 服务器内部错误

---

## 使用示例

### 完整工作流程示例

1. **注册用户**
```bash
curl -X POST http://localhost:5000/api/auth/register -H "Content-Type: application/json" -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
```
2. **用户登录**
```bash
curl -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d '{"identifier": "testuser", "password": "password123"}'
```
3. **搜索歌曲**
```bash
curl -X GET "http://localhost:5000/api/music/search?q=周杰伦&limit=10" -H "Authorization: Bearer <access_token>"
```
4. **创建笔记**
```bash
curl -X POST http://localhost:5000/api/notes
 -H "Content-Type: application/json" -H "Authorization: Bearer <access_token>" -d '{"netease_song_id": "123456", "content": "这首歌很好听", "is_public": true}'
```
5. **获取歌曲相关笔记**
```bash
curl -X GET "http://localhost:5000/api/notes/by-song/123456?page=1&per_page=10"
```
6. **获取自己的笔记**
```bash
curl -X GET "http://localhost:5000/api/notes?page=1&per_page=20" -H "Authorization: Bearer <access_token>"
```
---

## 数据结构说明

### 歌曲信息 (Song)
```json
{
    "id": 1,
    "netease_song_id": "123456",
    "title": "歌曲标题",
    "artist": "艺术家",
    "album": "专辑",
    "album_cover_url": "封面图片URL",
    "duration": 240000,
    "note_count": 5,
    "created_at": "创建时间",
    "updated_at": "更新时间"
}
```
### 笔记信息 (Note)
```json
{
    "id": 1,
    "user_id": 1,
    "song_id": 1,
    "content": "笔记内容",
    "timestamp": 123456,
    "is_public": true,
    "created_at": "创建时间",
    "updated_at": "更新时间",
    "song": {
        "netease_song_id": "123456",
        "title": "歌曲标题",
        "artist": "艺术家",
        "album": "专辑",
        "album_cover_url": "封面图片URL"
    },
    "user": {
        "id": 1,
        "username": "用户名"
    }
}
```
### 用户信息 (User)
```json
{
    "id": 1,
    "username": "用户名",
    "email": "邮箱",
    "created_at": "创建时间",
    "netease_account": {
        "netease_user_id": "网易云用户ID",
        "netease_username": "网易云用户名",
        "is_bound": true,
        "bound_at": "绑定时间"
    }
}
```
---

## 注意事项

1. **认证**: 大部分API需要JWT Token认证，Token在登录或注册时获得
2. **分页**: 列表类API都支持分页，默认每页20条
3. **歌曲ID**: 使用网易云音乐歌曲ID，不是数据库自增ID
4. **缓存策略**: 歌曲信息采用三级缓存策略（内存缓存 > 数据库 > API）
5. **错误处理**: 所有API都有统一的错误响应格式
6. **数据验证**: 所有输入都有基本的验证和清理

---

## 更新说明

### 主要改进：

1. **数据库优化**：
   - 重新引入Song表，但仅在创建笔记时保存歌曲信息
   - 添加了note_count字段，记录歌曲的笔记数量
   - 添加了适当的索引优化查询性能

2. **缓存策略**：
   - 三级数据获取策略：缓存 > 数据库 > API
   - 搜索和歌曲详情都有独立的缓存
   - 缓存大小有限制，避免内存溢出

3. **新API端点**：
   - `/notes/by-song/<song_id>`: 通过歌曲获取笔记
   - `/notes/user/<user_id>/by-song/<song_id>`: 获取指定用户对指定歌曲的笔记

4. **性能优化**：
   - 批量获取歌曲信息，减少API调用
   - 数据库查询优化，添加索引
   - 减少不必要的数据传输