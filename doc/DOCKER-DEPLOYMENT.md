# Docker 배포 가이드

StreamFlix v1.0을 Docker 컨테이너로 배포하는 완전한 가이드입니다.

## 📋 목차

- [사전 준비](#사전-준비)
- [빠른 시작](#빠른-시작)
- [상세 설정](#상세-설정)
- [볼륨 관리](#볼륨-관리)
- [프로덕션 배포](#프로덕션-배포)
- [문제 해결](#문제-해결)
- [유지보수](#유지보수)

---

## 사전 준비

### 필수 소프트웨어

1. **Docker 설치**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install -y docker.io docker-compose
   sudo systemctl start docker
   sudo systemctl enable docker

   # macOS
   # Docker Desktop 다운로드: https://www.docker.com/products/docker-desktop

   # Raspberry Pi OS
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Docker 버전 확인**
   ```bash
   docker --version          # 20.10+
   docker-compose --version  # 1.29+ 또는 2.0+
   ```

---

## 빠른 시작

### 1. 환경 변수 설정

```bash
# .env.docker를 .env로 복사
cp .env.docker .env

# SECRET_KEY 생성 및 설정
python3 -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')" >> .env

# 비밀번호 설정 (nano 또는 vi로 편집)
nano .env
```

**필수 수정 항목:**
```env
POSTGRES_PASSWORD=your_very_secure_password_123
SECRET_KEY=<위에서 생성한 키>
```

### 2. 컨테이너 빌드 및 실행

```bash
# 모든 서비스 빌드 및 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3. 관리자 계정 생성

```bash
# 백엔드 컨테이너에 접속
docker exec -it streamflix-backend bash

# 관리자 생성
python create_admin.py

# 컨테이너에서 나가기
exit
```

### 4. 접속

- **프론트엔드**: http://localhost
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

---

## 상세 설정

### 서비스 구성

```yaml
services:
  postgres:     # PostgreSQL 14 데이터베이스
  backend:      # FastAPI 백엔드 (Python 3.11)
  frontend:     # React 프론트엔드 (Nginx)
```

### 포트 매핑

| 서비스 | 호스트 포트 | 컨테이너 포트 |
|--------|------------|--------------|
| Frontend | 80 | 80 |
| Backend | 8000 | 8000 |
| PostgreSQL | 5432 | 5432 |

**포트 변경 방법:**

`docker-compose.yml` 파일 수정:
```yaml
services:
  frontend:
    ports:
      - "3000:80"  # 호스트 포트를 3000으로 변경
```

### 환경 변수 전체 목록

#### PostgreSQL
```env
POSTGRES_DB=streamflix
POSTGRES_USER=streamflix
POSTGRES_PASSWORD=your_password
```

#### Backend
```env
DATABASE_URL=postgresql+asyncpg://streamflix:password@postgres:5432/streamflix
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=http://localhost:3000,http://localhost
UPLOAD_DIR=/app/storage/videos
THUMBNAIL_DIR=/app/storage/thumbnails
FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe
DEBUG=false
```

---

## 볼륨 관리

### 영구 저장소

Docker Compose는 다음 3개의 볼륨을 생성합니다:

```yaml
volumes:
  postgres_data:      # 데이터베이스 데이터
  video_storage:      # 업로드된 비디오 파일
  thumbnail_storage:  # 썸네일 및 미리보기 클립
```

### 볼륨 위치 확인

```bash
# 모든 볼륨 목록
docker volume ls

# 특정 볼륨 정보
docker volume inspect videos_web_server_video_storage
```

### 외장 HDD 마운트 (라즈베리파이)

외장 HDD를 사용하려면 `docker-compose.yml` 수정:

```yaml
volumes:
  video_storage:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/external_hdd/videos

  thumbnail_storage:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/external_hdd/thumbnails
```

**사전 준비:**
```bash
# 외장 HDD 마운트
sudo mkdir -p /mnt/external_hdd
sudo mount /dev/sda1 /mnt/external_hdd

# 디렉토리 생성
sudo mkdir -p /mnt/external_hdd/videos /mnt/external_hdd/thumbnails
sudo chown -R $USER:$USER /mnt/external_hdd
```

### 볼륨 백업

```bash
# 비디오 볼륨 백업
docker run --rm -v videos_web_server_video_storage:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/videos_backup_$(date +%Y%m%d).tar.gz /data

# 데이터베이스 백업
docker exec streamflix-postgres pg_dump -U streamflix streamflix > backup_$(date +%Y%m%d).sql
```

### 볼륨 복원

```bash
# 비디오 볼륨 복원
docker run --rm -v videos_web_server_video_storage:/data \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/videos_backup_20260209.tar.gz -C /

# 데이터베이스 복원
cat backup_20260209.sql | docker exec -i streamflix-postgres psql -U streamflix streamflix
```

---

## 프로덕션 배포

### 1. 보안 강화

#### HTTPS 설정 (Let's Encrypt)

`docker-compose.prod.yml` 파일 생성:

```yaml
version: '3.8'

services:
  nginx-proxy:
    image: nginxproxy/nginx-proxy
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - ./certs:/etc/nginx/certs
      - ./vhost.d:/etc/nginx/vhost.d
      - ./html:/usr/share/nginx/html
    networks:
      - streamflix-network

  letsencrypt:
    image: nginxproxy/acme-companion
    container_name: nginx-proxy-acme
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./certs:/etc/nginx/certs
      - ./vhost.d:/etc/nginx/vhost.d
      - ./html:/usr/share/nginx/html
    environment:
      - DEFAULT_EMAIL=your-email@example.com
    depends_on:
      - nginx-proxy
    networks:
      - streamflix-network

  frontend:
    environment:
      - VIRTUAL_HOST=your-domain.com
      - LETSENCRYPT_HOST=your-domain.com
      - LETSENCRYPT_EMAIL=your-email@example.com
```

#### 실행:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2. 리소스 제한

메모리 및 CPU 제한 설정:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### 3. 로그 관리

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 문제 해결

### 컨테이너 상태 확인

```bash
# 모든 컨테이너 상태
docker-compose ps

# 특정 컨테이너 로그
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# 실시간 로그 추적
docker-compose logs -f backend
```

### 일반적인 문제들

#### 1. 데이터베이스 연결 실패

```bash
# PostgreSQL 컨테이너 확인
docker exec -it streamflix-postgres psql -U streamflix -d streamflix

# 네트워크 확인
docker network inspect videos_web_server_streamflix-network
```

#### 2. 포트 충돌

```bash
# 포트 사용 중인 프로세스 확인
sudo lsof -i :80
sudo lsof -i :8000

# 컨테이너 포트 변경
# docker-compose.yml에서 포트 수정 후 재시작
docker-compose down
docker-compose up -d
```

#### 3. 볼륨 권한 문제

```bash
# 볼륨 내용 확인
docker exec -it streamflix-backend ls -la /app/storage/videos

# 권한 수정
docker exec -it streamflix-backend chown -R root:root /app/storage
docker exec -it streamflix-backend chmod -R 755 /app/storage
```

#### 4. 이미지 빌드 실패

```bash
# 캐시 없이 재빌드
docker-compose build --no-cache

# 개별 서비스 재빌드
docker-compose build --no-cache backend
```

---

## 유지보수

### 컨테이너 관리

```bash
# 모든 서비스 시작
docker-compose up -d

# 모든 서비스 중지
docker-compose down

# 서비스 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart backend

# 볼륨 포함 완전 삭제 (주의!)
docker-compose down -v
```

### 업데이트

```bash
# 최신 코드 가져오기
git pull origin main

# 이미지 재빌드
docker-compose build

# 무중단 재시작
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend
```

### 데이터베이스 마이그레이션

```bash
# 백엔드 컨테이너에서 마이그레이션 실행
docker exec -it streamflix-backend alembic upgrade head

# 마이그레이션 히스토리 확인
docker exec -it streamflix-backend alembic history
```

### 리소스 사용량 모니터링

```bash
# 실시간 리소스 사용량
docker stats

# 디스크 사용량
docker system df

# 불필요한 리소스 정리
docker system prune -a
```

---

## 성능 최적화

### 1. 멀티스테이지 빌드 (이미 적용됨)

프론트엔드 Dockerfile에서 빌드 단계와 실행 단계 분리로 이미지 크기 최소화

### 2. 캐싱 전략

```yaml
services:
  backend:
    environment:
      # Redis 캐싱 (추후 추가 시)
      REDIS_URL: redis://redis:6379
```

### 3. 프로덕션 최적화

```bash
# Nginx gzip 압축 (이미 nginx.conf에 적용됨)
# React 프로덕션 빌드 (이미 Dockerfile에 적용됨)
```

---

## 참고 자료

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [PostgreSQL Docker 이미지](https://hub.docker.com/_/postgres)
- [Nginx Docker 이미지](https://hub.docker.com/_/nginx)

---

## 주의사항

⚠️ **프로덕션 환경에서 반드시 변경해야 할 항목:**

1. `.env` 파일의 모든 비밀번호 및 키 변경
2. `DEBUG=false` 설정
3. HTTPS 적용
4. 정기적인 백업 설정
5. 로그 로테이션 설정
6. 방화벽 규칙 설정

---

**작성일**: 2026-02-09
**버전**: v1.0
**문서 상태**: Draft (최종 배포 전 검토 필요)
