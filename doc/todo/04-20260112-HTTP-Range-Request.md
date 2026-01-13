# Todo: HTTP Range Request 구현

**작성일:** 2026-01-12
**상태:** ✅ 완료
**관련 명세:** [8.v0.6.1-http-range-request.md](../dev_Process/8.v0.6.1-http-range-request.md)

---

## 작업 개요

비디오 재생 중 구간 이동(seeking) 시 0:00초로 돌아가는 문제를 해결하기 위해 HTTP Range Request를 구현합니다.

---

## 문제 상황

### 발생한 문제
- ❌ 비디오 로딩 완료 직후 구간 이동 시 0:00초로 돌아감
- ❌ 타임라인 클릭이 작동하지 않음
- ❌ Video.js 플레이어가 seeking 불가

### 원인 분석
```
사용자: 10초로 이동!
  ↓
플레이어: "Range: bytes=1000000-" 요청
  ↓
백엔드: Range 헤더 무시하고 전체 파일 전송 (0부터)
  ↓
플레이어: 0초부터 다시 재생 😞
```

백엔드가 HTTP Range Request를 지원하지 않아서 발생한 문제입니다.

---

## 체크리스트

### 백엔드 구현

- [x] **Request import 추가** (`fastapi.Request`)
- [x] **stream_video 함수 수정**
  - [x] `request: Request` 파라미터 추가
  - [x] Range 헤더 파싱 로직 구현
  - [x] 파일 크기 계산 (`os.path.getsize`)
  - [x] Range 요청 시 조회수 증가 방지

- [x] **Partial Content 응답 구현**
  - [x] Range 헤더 파싱 ("bytes=start-end")
  - [x] start, end 값 추출 및 검증
  - [x] 파일의 특정 범위만 읽기 (`f.seek(start)`)
  - [x] 1MB 청크 단위 스트리밍
  - [x] 206 Partial Content 상태 코드
  - [x] Content-Range 헤더 추가
  - [x] Accept-Ranges: bytes 헤더

- [x] **전체 파일 응답 개선**
  - [x] Accept-Ranges: bytes 헤더 추가
  - [x] Content-Length 헤더 추가
  - [x] 청크 단위 스트리밍 (1MB)

### 테스트

- [x] 서버 자동 재시작 확인 (--reload)
- [x] Health check 확인
- [ ] Range Request 기능 테스트
  - [ ] 브라우저에서 비디오 재생
  - [ ] 구간 이동 (seeking) 테스트
  - [ ] 개발자 도구에서 206 응답 확인

### 문서화

- [x] Todo 문서 작성
- [x] Dev_Process 명세 작성

---

## 구현 세부사항

### 파일 변경

**`backend/app/api/v1/videos.py`**

#### Before (문제 코드)
```python
@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Range 요청 무시
    def iterfile():
        with open(video.file_path, "rb") as f:
            yield from f  # 항상 처음부터 끝까지

    return StreamingResponse(iterfile(), media_type="video/mp4")
```

#### After (해결 코드)
```python
@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    request: Request,  # ✅ Request 추가
    db: AsyncSession = Depends(get_db)
):
    file_size = os.path.getsize(video.file_path)
    range_header = request.headers.get("range")

    # Range 요청 처리
    if range_header:
        # "bytes=1000-2000" 파싱
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1

        # 파일의 특정 부분만 읽기
        def iterfile_range():
            with open(video.file_path, "rb") as f:
                f.seek(start)  # ✅ 시작 위치로 이동
                remaining = end - start + 1
                while remaining > 0:
                    chunk = f.read(min(1024*1024, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            iterfile_range(),
            status_code=206,  # ✅ Partial Content
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(end - start + 1)
            }
        )

    # 전체 파일
    return StreamingResponse(
        iterfile(),
        headers={
            "Accept-Ranges": "bytes",  # ✅ Range 지원 알림
            "Content-Length": str(file_size)
        }
    )
```

---

## HTTP Range Request 개념

### 1. Range 요청 예시

**초기 재생 (Range 없음)**
```http
GET /api/v1/videos/1/stream HTTP/1.1

HTTP/1.1 200 OK
Accept-Ranges: bytes
Content-Length: 52428800
```

**구간 이동 (Range 있음)**
```http
GET /api/v1/videos/1/stream HTTP/1.1
Range: bytes=5242880-

HTTP/1.1 206 Partial Content
Content-Range: bytes 5242880-52428799/52428800
Accept-Ranges: bytes
Content-Length: 47185920
```

### 2. Range 헤더 형식

| Range 헤더 | 의미 |
|-----------|------|
| `bytes=0-999` | 처음 1000바이트 |
| `bytes=1000-1999` | 1000~1999 바이트 (1000바이트) |
| `bytes=5000000-` | 5MB부터 끝까지 |
| `bytes=-1000` | 마지막 1000바이트 |

### 3. 응답 상태 코드

| 코드 | 의미 | 사용 시점 |
|------|------|----------|
| 200 OK | 전체 파일 | Range 헤더 없을 때 |
| 206 Partial Content | 일부 전송 | Range 헤더 있을 때 |
| 416 Range Not Satisfiable | 범위 오류 | 잘못된 Range 값 |

### 4. 필수 응답 헤더

```http
Accept-Ranges: bytes           # Range 요청 지원 알림
Content-Range: bytes 0-999/5000  # 전송 범위/전체 크기
Content-Length: 1000           # 실제 전송 크기
```

---

## 성능 최적화

### 청크 단위 스트리밍

**Before:**
```python
def iterfile():
    with open(file_path, "rb") as f:
        yield from f  # 메모리에 전체 파일 로드 (위험!)
```

**After:**
```python
def iterfile():
    with open(file_path, "rb") as f:
        chunk_size = 1024 * 1024  # 1MB
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk  # ✅ 1MB씩 전송
```

### 조회수 최적화

```python
# Range 요청 시 조회수 증가 안 함
if not range_header:
    await video_service.increment_view_count(db, video)
```

**이유:**
- 초기 재생 시에만 조회수 증가
- 구간 이동 시마다 증가하면 부정확

---

## 테스트 방법

### 1. 브라우저 테스트

1. 비디오 업로드: http://localhost:5173/upload
2. 비디오 재생
3. **구간 이동 테스트:**
   - 타임라인 중간 클릭
   - ✅ 클릭한 위치에서 즉시 재생
   - ❌ 0:00초로 돌아가지 않음

### 2. 개발자 도구 확인

**F12 → Network 탭:**

```
Name: stream
Status: 206 Partial Content ✅
Request Headers:
  Range: bytes=5242880-
Response Headers:
  Content-Range: bytes 5242880-52428799/52428800
  Accept-Ranges: bytes
```

### 3. curl 테스트

```bash
# 전체 파일
curl -I http://localhost:8000/api/v1/videos/1/stream
# → 200 OK, Accept-Ranges: bytes

# Range 요청
curl -I -H "Range: bytes=1000-2000" http://localhost:8000/api/v1/videos/1/stream
# → 206 Partial Content, Content-Range: bytes 1000-2000/52428800
```

---

## 트러블슈팅

### 문제 1: 여전히 0초로 돌아감

**원인:** 브라우저 캐시

**해결:**
```
Ctrl+Shift+R (캐시 무시 새로고침)
```

### 문제 2: 206 응답이 안 옴

**원인:** Range 헤더가 전송되지 않음

**확인:**
- Video.js 버전 확인
- 비디오 포맷 확인 (mp4 권장)

### 문제 3: 파일을 찾을 수 없음

**원인:** 저장소 경로 문제

**해결:**
```bash
# .env 확인
UPLOAD_DIR=/Users/.../storage/videos  # /tmp/videos 아님!
```

---

## 다음 단계

- [ ] 프론트엔드에서 실제 테스트
- [ ] 다양한 비디오 포맷 테스트
- [ ] 대용량 파일 테스트 (1GB+)
- [ ] 네트워크 속도 제한 테스트

---

## 참고 자료

- [MDN: HTTP Range Requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests)
- [RFC 7233: Range Requests](https://datatracker.ietf.org/doc/html/rfc7233)
- [Video.js Documentation](https://videojs.com/)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)

---

## 완료 확인

- [x] 코드 구현 완료
- [x] 서버 재시작 완료
- [ ] 브라우저 테스트 완료
- [x] 문서 작성 완료

**상태:** 코드 구현 완료, 사용자 테스트 대기 중
