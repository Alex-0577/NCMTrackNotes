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

绑定网易云音乐账号到用户账户。支持两种登录方式：密码登录和验证码登录。

**请求**:
- **方法**: `POST`
- **端点**: `/auth/bind-netease`
- **认证**: 需要 (Bearer Token)
- **请求体** (密码登录):
```json
{
    "netease_username": "string, 手机号或邮箱",
    "netease_password": "string, 密码",
    "login_type": "password"  // 可选，默认为password
}
```
或 (验证码登录):
```json
{
    "phone": "string, 手机号",
    "captcha": "string, 验证码",
    "login_type": "captcha"  // 必须为captcha
}
```

**响应**:
- **成功 (200)**:
```json
{
    "message": "Netease account bound successfully",
    "netease_account": {
        "netease_user_id": "netease_user_id",
        "netease_username": "netease_username",
        "is_bound": true
    }
}
```
  - **错误 (400)**: 缺少必要信息或绑定失败
  - **错误 (401)**: 未认证

---

### 5. 发送验证码

向指定手机号发送短信验证码，用于验证码登录绑定网易云账号。

**请求**:
- **方法**: `POST`
- **端点**: `/auth/send-captcha`
- **认证**: 需要 (Bearer Token)
- **请求体**:
```json
{
    "phone": "string, 手机号",
    "ctcode": "string, 国家代码，默认86"
}
```

**响应**:
- **成功 (200)**:
```json
{
    "success": true,
    "message": "验证码发送成功",
    "data": {
        "phone": "手机号",
        "captcha_sent": true
    }
}
```
  - **错误 (400)**: 手机号不能为空或发送失败
  - **错误 (401)**: 未认证

---

### 6. 验证验证码

验证用户输入的短信验证码是否正确，用于验证码登录前的验证。

**请求**:
- **方法**: `POST`
- **端点**: `/auth/verify-captcha`
- **认证**: 需要 (Bearer Token)
- **请求体**:
```json
{
    "phone": "string, 手机号",
    "captcha": "string, 验证码",
    "ctcode": "string, 国家代码，默认86"
}
```

**响应**:
- **成功 (200)**:
```json
{
    "success": true,
    "message": "验证码验证成功",
    "data": {
        "phone": "手机号",
        "captcha_verified": true
    }
}
```
  - **错误 (400)**: 手机号和验证码不能为空或验证失败
  - **错误 (401)**: 未认证

---

### 7. 解绑网易云音乐账号

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
  
### 8. 通过UID绑定网易云账号

**请求**:
- **方法**: `POST`
- **端点**: `/auth/bind-netease-uid`
- **认证**: 需要 (Bearer Token)
- **请求体**:
```json
{
    "netease_user_id": "string, 网易云用户ID（必需）",
}
```

**描述**:
此端点用于直接将网易云UID与当前登录的记事本账号绑定，无需进行网易云账号的登录验证。适用于已知网易云UID的场景，可以跳过登录流程快速绑定账号。

**响应**:
- **成功 (200)**:
```json
{
    "success": true,
    "message": "Netease account bound successfully by UID (created/updated)",
    "netease_account": {
        "netease_user_id": "netease_user_id",
        "is_bound": true,
        "bound_at": "2023-10-01T12:00:00Z"
    }
}
```
- **错误 (400)**: 缺少必要参数或参数格式错误
- **错误 (409)**: 该网易云UID已被其他用户绑定
- **错误 (401)**: 未认证
- **错误 (500)**: 服务器内部错误

---

## 音乐相关API

### 8. 搜索歌曲

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

### 9. 获取歌曲详情

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

### 10. 批量获取歌曲信息

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

### 11. 创建笔记

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

### 12. 获取用户笔记

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

### 13. 获取单个笔记

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

### 14. 更新笔记

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

### 15. 删除笔记

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

### 16. 获取公开笔记

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

### 17. 通过歌曲获取笔记

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

### 18. 获取指定用户对指定歌曲的笔记

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

### 19. 健康检查

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

## 使用示例（PowerShell Invoke-RestMethod格式）

### 完整工作流程示例

#### 1. 注册用户
```powershell
$registerBody = @{
    username = "testuser"
    email = "test@example.com"
    password = "password123"
} | ConvertTo-Json

$registerResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/register" `
    -Method Post `
    -Headers @{ "Content-Type" = "application/json" } `
    -Body $registerBody

Write-Host "注册成功！用户ID: $($registerResponse.user.id)"
Write-Host "访问令牌: $($registerResponse.access_token)"
```

#### 2. 用户登录
```powershell
$loginBody = @{
    identifier = "testuser"
    password = "password123"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" `
    -Method Post `
    -Headers @{ "Content-Type" = "application/json" } `
    -Body $loginBody

$accessToken = $loginResponse.access_token
Write-Host "登录成功！访问令牌: $accessToken"
```

#### 3. 发送验证码（绑定网易云账号前）
```powershell
$sendCaptchaBody = @{
    phone = "13800138000"
    ctcode = "86"
} | ConvertTo-Json

$captchaResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/send-captcha" `
    -Method Post `
    -Headers @{ 
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $accessToken"
    } `
    -Body $sendCaptchaBody

if ($captchaResponse.success) {
    Write-Host "验证码发送成功！"
} else {
    Write-Host "验证码发送失败: $($captchaResponse.message)"
}
```

#### 4. 验证验证码
```powershell
$verifyCaptchaBody = @{
    phone = "13800138000"
    captcha = "123456"
    ctcode = "86"
} | ConvertTo-Json

$verifyResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/verify-captcha" `
    -Method Post `
    -Headers @{ 
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $accessToken"
    } `
    -Body $verifyCaptchaBody

if ($verifyResponse.success) {
    Write-Host "验证码验证成功！"
} else {
    Write-Host "验证码验证失败: $($verifyResponse.message)"
}
```

#### 5. 绑定网易云账号（验证码登录）
```powershell
$bindAccountBody = @{
    phone = "13800138000"
    captcha = "123456"
    login_type = "captcha"
} | ConvertTo-Json

$bindResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/bind-netease" `
    -Method Post `
    -Headers @{ 
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $accessToken"
    } `
    -Body $bindAccountBody

if ($bindResponse.netease_account.is_bound) {
    Write-Host "网易云账号绑定成功！"
    Write-Host "网易云用户ID: $($bindResponse.netease_account.netease_user_id)"
} else {
    Write-Host "网易云账号绑定失败"
}
```

#### 6. 搜索歌曲
```powershell
$searchUri = "http://localhost:5000/api/music/search?q=周杰伦&limit=10"
$searchResponse = Invoke-RestMethod -Uri $searchUri `
    -Headers @{ "Authorization" = "Bearer $accessToken" }

Write-Host "搜索到 $($searchResponse.total) 首歌曲"
foreach ($song in $searchResponse.songs) {
    Write-Host "  - $($song.title) - $($song.artist)"
}
```

#### 7. 创建笔记
```powershell
$noteBody = @{
    netease_song_id = "123456"
    content = "这是一条测试笔记，关于周杰伦的歌曲"
    is_public = $true
} | ConvertTo-Json

$noteResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/notes" `
    -Method Post `
    -Headers @{ 
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $accessToken"
    } `
    -Body $noteBody

if ($noteResponse.message -eq "笔记创建成功") {
    Write-Host "笔记创建成功！笔记ID: $($noteResponse.note.id)"
    Write-Host "歌曲: $($noteResponse.note.song.title)"
    Write-Host "内容: $($noteResponse.note.content)"
}
```

如果需要处理中文，可以指定UTF-8编码：
```powershell
$body = [System.Text.Encoding]::UTF8.GetBytes($jsonString)
```