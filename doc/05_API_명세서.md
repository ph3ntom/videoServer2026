# 05. API 명세서

> 라즈베리파이 최적화: 핵심 API만 유지, 불필요한 기능 제거

## 변경 사항 요약

### MVP에 포함된 API
- ✅ 인증 (회원가입, 로그인, 토큰 관리)
- ✅ 사용자 프로필 조회/수정
- ✅ 비디오 조회, 스트리밍 (공개)
- ✅ **Admin 전용 비디오 업로드** (일반 사용자 업로드 불가)
- ✅ 카테고리 브라우징
- ✅ **태그 시스템** (조회, 조합 검색)
- ✅ **검색** (제목 키워드 + 태그 조합)
- ✅ **썸네일 관리** (자동 생성, admin 선택)

### Phase 2 (추후 추가)
- ⏳ 평점 시스템 (별점 1-5)
- ⏳ 시청 기록 및 이어보기

### 제거된 API (불필요)
- ❌ 댓글 시스템
- ❌ 찜하기 (Favorites)
- ❌ 플레이리스트
- ❌ 소셜 공유
- ❌ 다운로드
- ❌ 라이브 스트리밍
- ❌ 실시간 알림

## API 기본 정보

### Base URL
```
Development: http://localhost:8000
Production: https://api.streamflix.com
```

### API 버전
```
/api/v1
```

### 인증 방식
- **JWT Bearer Token**
- Header: `Authorization: Bearer <access_token>`

### 응답 형식
- Content-Type: `application/json`
- 모든 응답은 일관된 구조를 따름

#### 성공 응답
```json
{
    "success": true,
    "data": { ... },
    "message": "Success message"
}
```

#### 에러 응답
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Error description",
        "details": { ... }
    }
}
```

### HTTP 상태 코드
- `200 OK`: 성공
- `201 Created`: 리소스 생성 성공
- `204 No Content`: 성공 (응답 본문 없음)
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 실패
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스 없음
- `422 Unprocessable Entity`: 유효성 검증 실패
- `500 Internal Server Error`: 서버 에러

---

## 1. 인증 (Authentication)

### 1.1 회원가입

**POST** `/api/v1/auth/register`

사용자 계정을 생성합니다.

#### Request Body
```json
{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "full_name": "John Doe"
}
```

#### Response (201 Created)
```json
{
    "success": true,
    "data": {
        "user": {
            "id": 1,
            "email": "user@example.com",
            "username": "johndoe",
            "full_name": "John Doe",
            "role": "user",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        },
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer"
    }
}
```

#### Errors
- `400`: 이메일 또는 사용자명 중복
- `422`: 유효성 검증 실패 (비밀번호 강도 등)

---

### 1.2 로그인

**POST** `/api/v1/auth/login`

사용자 인증 후 JWT 토큰을 발급합니다.

#### Request Body
```json
{
    "email": "user@example.com",
    "password": "SecurePass123!"
}
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "expires_in": 900
    }
}
```

#### Errors
- `401`: 이메일 또는 비밀번호 불일치
- `403`: 비활성화된 계정

---

### 1.3 토큰 갱신

**POST** `/api/v1/auth/refresh`

Refresh Token을 사용하여 새로운 Access Token을 발급합니다.

#### Request Body
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "expires_in": 900
    }
}
```

---

### 1.4 로그아웃

**POST** `/api/v1/auth/logout`

현재 토큰을 무효화합니다. (선택적: Redis에 블랙리스트 추가)

#### Headers
```
Authorization: Bearer <access_token>
```

#### Response (204 No Content)

---

## 2. 사용자 (Users)

### 2.1 내 프로필 조회

**GET** `/api/v1/users/me`

현재 로그인한 사용자의 프로필을 조회합니다.

#### Headers
```
Authorization: Bearer <access_token>
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "id": 1,
        "email": "user@example.com",
        "username": "johndoe",
        "full_name": "John Doe",
        "role": "user",
        "avatar_url": "https://example.com/avatars/1.jpg",
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}
```

---

### 2.2 프로필 수정

**PUT** `/api/v1/users/me`

현재 사용자의 프로필을 수정합니다.

#### Request Body
```json
{
    "full_name": "John Updated",
    "avatar_url": "https://example.com/new-avatar.jpg"
}
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "id": 1,
        "email": "user@example.com",
        "username": "johndoe",
        "full_name": "John Updated",
        "avatar_url": "https://example.com/new-avatar.jpg"
    }
}
```

---

### 2.3 비밀번호 변경

**POST** `/api/v1/users/me/change-password`

비밀번호를 변경합니다.

#### Request Body
```json
{
    "current_password": "OldPass123!",
    "new_password": "NewSecurePass456!"
}
```

#### Response (200 OK)
```json
{
    "success": true,
    "message": "Password changed successfully"
}
```

#### Errors
- `401`: 현재 비밀번호 불일치
- `422`: 새 비밀번호 유효성 검증 실패

---

## 3. 비디오 (Videos)

### 3.1 비디오 목록 조회

**GET** `/api/v1/videos`

비디오 목록을 페이지네이션하여 조회합니다.

#### Query Parameters
- `page` (integer, default: 1): 페이지 번호
- `size` (integer, default: 20): 페이지 크기
- `category_id` (integer, optional): 카테고리 필터
- `sort_by` (string, default: "created_at"): 정렬 기준 (created_at, view_count, rating)
- `order` (string, default: "desc"): 정렬 순서 (asc, desc)
- `status` (string, default: "ready"): 비디오 상태

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "id": 1,
                "title": "Sample Video",
                "description": "This is a sample video",
                "thumbnail_url": "https://example.com/thumbnails/1.jpg",
                "duration": 3600,
                "view_count": 1234,
                "user": {
                    "id": 1,
                    "username": "creator",
                    "avatar_url": "https://example.com/avatars/1.jpg"
                },
                "created_at": "2024-01-01T00:00:00Z",
                "published_at": "2024-01-01T00:00:00Z"
            }
        ],
        "total": 100,
        "page": 1,
        "size": 20,
        "pages": 5
    }
}
```

---

### 3.2 비디오 상세 조회

**GET** `/api/v1/videos/{video_id}`

특정 비디오의 상세 정보를 조회합니다.

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "id": 1,
        "title": "Sample Video",
        "description": "Detailed description",
        "thumbnail_url": "https://example.com/thumbnails/1.jpg",
        "duration": 3600,
        "file_size": 1073741824,
        "resolution": "1920x1080",
        "view_count": 1234,
        "categories": [
            {
                "id": 1,
                "name": "영화",
                "slug": "movies"
            }
        ],
        "user": {
            "id": 1,
            "username": "creator",
            "full_name": "Creator Name",
            "avatar_url": "https://example.com/avatars/1.jpg"
        },
        "avg_rating": 4.5,
        "rating_count": 100,
        "created_at": "2024-01-01T00:00:00Z",
        "published_at": "2024-01-01T00:00:00Z"
    }
}
```

#### Errors
- `404`: 비디오를 찾을 수 없음

---

### 3.3 비디오 업로드

**POST** `/api/v1/videos/upload`

비디오 파일을 업로드합니다.

#### Headers
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### Request Body (multipart/form-data)
- `file` (file): 비디오 파일
- `title` (string): 제목
- `description` (string, optional): 설명
- `category_ids` (array[integer]): 카테고리 ID 목록

#### Response (201 Created)
```json
{
    "success": true,
    "data": {
        "id": 1,
        "title": "My Video",
        "description": "My video description",
        "status": "processing",
        "file_path": "/uploads/videos/abc123.mp4",
        "created_at": "2024-01-01T00:00:00Z"
    },
    "message": "Video uploaded successfully. Processing in progress."
}
```

#### Errors
- `400`: 잘못된 파일 형식
- `413`: 파일 크기 초과 (최대 2GB)
- `422`: 유효성 검증 실패

---

### 3.4 비디오 스트리밍

**GET** `/api/v1/videos/{video_id}/stream`

비디오를 스트리밍합니다. Range 요청을 지원합니다.

#### Headers (Optional)
```
Range: bytes=0-1023
```

#### Response (200 OK or 206 Partial Content)
- Content-Type: `video/mp4`
- Accept-Ranges: `bytes`
- Content-Range: `bytes 0-1023/1073741824`

#### Errors
- `404`: 비디오를 찾을 수 없음
- `403`: 비공개 비디오에 대한 권한 없음

---

### 3.5 비디오 수정

**PUT** `/api/v1/videos/{video_id}`

비디오 메타데이터를 수정합니다.

#### Headers
```
Authorization: Bearer <access_token>
```

#### Request Body
```json
{
    "title": "Updated Title",
    "description": "Updated description",
    "category_ids": [1, 2]
}
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "id": 1,
        "title": "Updated Title",
        "description": "Updated description"
    }
}
```

#### Errors
- `403`: 권한 없음 (본인의 비디오만 수정 가능)
- `404`: 비디오를 찾을 수 없음

---

### 3.6 비디오 삭제

**DELETE** `/api/v1/videos/{video_id}`

비디오를 삭제합니다.

#### Headers
```
Authorization: Bearer <access_token>
```

#### Response (204 No Content)

#### Errors
- `403`: 권한 없음
- `404`: 비디오를 찾을 수 없음

---

## 4. 카테고리 (Categories)

### 4.1 카테고리 목록 조회

**GET** `/api/v1/categories`

모든 카테고리를 조회합니다.

#### Response (200 OK)
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "영화",
            "slug": "movies",
            "description": "장편 영화 콘텐츠",
            "video_count": 150
        },
        {
            "id": 2,
            "name": "드라마",
            "slug": "drama",
            "description": "TV 드라마 시리즈",
            "video_count": 80
        }
    ]
}
```

---

## 4.2 태그 목록 조회

**GET** `/api/v1/tags`

모든 태그를 조회합니다.

#### Query Parameters
- `type` (string, optional): 태그 유형 필터 (country, genre, mood, general)

#### Response (200 OK)
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "한국영화",
            "slug": "korean-movie",
            "type": "country",
            "description": "한국에서 제작된 영화"
        },
        {
            "id": 2,
            "name": "공상과학",
            "slug": "sci-fi",
            "type": "genre",
            "description": "SF 장르"
        }
    ]
}
```

---

## 5. 검색 (Search)

### 5.1 기본 비디오 검색

**GET** `/api/v1/search/videos`

제목 및 설명으로 비디오를 검색합니다.

#### Query Parameters
- `q` (string, required): 검색 키워드
- `page` (integer, default: 1): 페이지 번호
- `size` (integer, default: 20): 페이지 크기

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "id": 1,
                "title": "Matching Video",
                "description": "Description with keyword",
                "thumbnail_url": "https://example.com/thumbnails/1.jpg",
                "view_count": 1234
            }
        ],
        "total": 10,
        "page": 1,
        "size": 20
    }
}
```

---

### 5.2 고급 태그 조합 검색 ⭐ 핵심 기능

**GET** `/api/v1/search/videos/advanced`

여러 태그를 조합하여 비디오를 검색합니다. 포함 조건(+)과 제외 조건(-)을 지원합니다.

#### Query Parameters
- `include_tags` (string): 포함할 태그 slug 목록 (쉼표 구분)
- `exclude_tags` (string, optional): 제외할 태그 slug 목록 (쉼표 구분)
- `page` (integer, default: 1): 페이지 번호
- `size` (integer, default: 20): 페이지 크기
- `sort_by` (string, default: "published_at"): 정렬 기준
- `order` (string, default: "desc"): 정렬 순서

#### 요청 예시
```
GET /api/v1/search/videos/advanced?include_tags=korean-movie,sci-fi&exclude_tags=war-movie&page=1&size=20
```

**의미**: "한국영화 + 공상과학 - 전쟁영화" 조건으로 검색
- 한국영화 태그가 있고
- 공상과학 태그가 있으며
- 전쟁영화 태그가 없는 비디오만 반환

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "id": 1,
                "title": "우주로 간 한국인",
                "description": "한국 우주 탐험 SF 영화",
                "thumbnail_url": "https://example.com/thumbnails/1.jpg",
                "duration": 7200,
                "view_count": 5000,
                "tags": [
                    {
                        "id": 1,
                        "name": "한국영화",
                        "slug": "korean-movie",
                        "type": "country"
                    },
                    {
                        "id": 2,
                        "name": "공상과학",
                        "slug": "sci-fi",
                        "type": "genre"
                    }
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "published_at": "2024-01-01T00:00:00Z"
            }
        ],
        "total": 15,
        "page": 1,
        "size": 20,
        "pages": 1,
        "filters": {
            "included_tags": ["korean-movie", "sci-fi"],
            "excluded_tags": ["war-movie"]
        }
    }
}
```

#### Errors
- `400`: 잘못된 태그 slug
- `422`: 필수 파라미터 누락 (include_tags)

---

## 6. 사용자 상호작용

### 6.1 시청 기록 업데이트

**POST** `/api/v1/videos/{video_id}/watch-progress`

시청 진행 상황을 업데이트합니다.

#### Headers
```
Authorization: Bearer <access_token>
```

#### Request Body
```json
{
    "progress": 1800,
    "completed": false
}
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "video_id": 1,
        "progress": 1800,
        "completed": false,
        "last_watched_at": "2024-01-01T12:00:00Z"
    }
}
```

---

### 6.2 평점 등록

**POST** `/api/v1/videos/{video_id}/rating`

비디오에 평점을 등록합니다.

#### Request Body
```json
{
    "score": 5
}
```

#### Response (201 Created)
```json
{
    "success": true,
    "data": {
        "video_id": 1,
        "score": 5,
        "created_at": "2024-01-01T12:00:00Z"
    }
}
```

---

## 7. 썸네일 (Thumbnails)

### 7.1 비디오 썸네일 목록 조회 (공개)

**GET** `/api/v1/videos/{video_id}/thumbnails`

비디오의 모든 썸네일을 조회합니다. (미리보기 기능용)

#### Response (200 OK)
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "file_path": "/uploads/thumbnails/1/thumb_10s.jpg",
            "timestamp": 10,
            "is_selected": true
        },
        {
            "id": 2,
            "file_path": "/uploads/thumbnails/1/thumb_20s.jpg",
            "timestamp": 20,
            "is_selected": false
        }
    ]
}
```

---

## 8. 관리자 (Admin)

### 8.1 대시보드 통계

**GET** `/api/v1/admin/dashboard/stats`

관리자 대시보드 통계를 조회합니다.

#### Headers
```
Authorization: Bearer <admin_access_token>
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "total_users": 1000,
        "total_videos": 500,
        "total_views": 100000,
        "storage_used": 107374182400,
        "active_users_today": 150
    }
}
```

---

### 8.2 비디오 썸네일 관리 (Admin 전용) ⭐ 핵심 기능

#### 9.2.1 썸네일 목록 조회

**GET** `/api/v1/admin/videos/{video_id}/thumbnails`

비디오의 모든 썸네일을 조회합니다. (관리자용 - 상세 정보 포함)

#### Headers
```
Authorization: Bearer <admin_access_token>
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "video_id": 1,
            "file_path": "/uploads/thumbnails/1/thumb_10s.jpg",
            "timestamp": 10,
            "width": 1920,
            "height": 1080,
            "is_selected": true,
            "is_auto_generated": true,
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 2,
            "file_path": "/uploads/thumbnails/1/thumb_20s.jpg",
            "timestamp": 20,
            "width": 1920,
            "height": 1080,
            "is_selected": false,
            "is_auto_generated": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

---

#### 9.2.2 썸네일 선택

**PUT** `/api/v1/admin/videos/{video_id}/thumbnails/{thumbnail_id}/select`

특정 썸네일을 메인 썸네일로 선택합니다.

#### Headers
```
Authorization: Bearer <admin_access_token>
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "id": 2,
        "is_selected": true
    },
    "message": "Thumbnail selected successfully"
}
```

---

#### 9.2.3 외부 이미지로 썸네일 업로드

**POST** `/api/v1/admin/videos/{video_id}/thumbnails`

외부 이미지를 썸네일로 업로드합니다.

#### Headers
```
Authorization: Bearer <admin_access_token>
Content-Type: multipart/form-data
```

#### Request Body (multipart/form-data)
- `file` (file): 이미지 파일 (jpg, png)
- `set_as_selected` (boolean, default: true): 업로드 즉시 선택 여부

#### Response (201 Created)
```json
{
    "success": true,
    "data": {
        "id": 10,
        "video_id": 1,
        "file_path": "/uploads/thumbnails/1/custom_thumb.jpg",
        "timestamp": 0,
        "is_selected": true,
        "is_auto_generated": false,
        "created_at": "2024-01-01T00:00:00Z"
    },
    "message": "Custom thumbnail uploaded successfully"
}
```

#### Errors
- `400`: 잘못된 파일 형식
- `413`: 파일 크기 초과 (최대 10MB)

---

### 8.3 태그 관리 (Admin 전용)

#### 9.3.1 태그 생성

**POST** `/api/v1/admin/tags`

새로운 태그를 생성합니다.

#### Headers
```
Authorization: Bearer <admin_access_token>
```

#### Request Body
```json
{
    "name": "한국영화",
    "slug": "korean-movie",
    "type": "country",
    "description": "한국에서 제작된 영화"
}
```

#### Response (201 Created)
```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "한국영화",
        "slug": "korean-movie",
        "type": "country",
        "description": "한국에서 제작된 영화",
        "created_at": "2024-01-01T00:00:00Z"
    }
}
```

---

#### 9.3.2 비디오에 태그 추가

**POST** `/api/v1/admin/videos/{video_id}/tags`

비디오에 태그를 추가합니다.

#### Request Body
```json
{
    "tag_ids": [1, 2, 3]
}
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "video_id": 1,
        "tags": [
            {"id": 1, "name": "한국영화", "slug": "korean-movie"},
            {"id": 2, "name": "공상과학", "slug": "sci-fi"},
            {"id": 3, "name": "액션", "slug": "action"}
        ]
    }
}
```

---

#### 9.3.3 비디오에서 태그 제거

**DELETE** `/api/v1/admin/videos/{video_id}/tags/{tag_id}`

비디오에서 특정 태그를 제거합니다.

#### Response (204 No Content)

---

## Webhook (선택적)

### 비디오 처리 완료 알림

트랜스코딩 완료 시 외부 시스템으로 전송

```json
{
    "event": "video.processing.completed",
    "video_id": 1,
    "status": "ready",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Rate Limiting

- 인증된 사용자: 100 requests/minute
- 비인증 사용자: 20 requests/minute
- 파일 업로드: 10 requests/hour

헤더 응답:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```
