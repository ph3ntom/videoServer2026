# StreamFlix v1.0

> 라즈베리파이 기반 개인용 스트리밍 플랫폼

Netflix와 YouTube의 핵심 기능을 결합한 경량 비디오 스트리밍 서비스입니다. 태그 기반 고급 검색, HLS 적응형 스트리밍, 호버 미리보기 등 현대적인 스트리밍 서비스의 모든 필수 기능을 제공합니다.

[![Version](https://img.shields.io/badge/version-1.0-blue.svg)](doc/v1.0-Release-Notes.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)

---

## 📋 목차

- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [시스템 요구사항](#-시스템-요구사항)
- [빠른 시작](#-빠른-시작)
- [설치 가이드](#-설치-가이드)
- [프로젝트 구조](#-프로젝트-구조)
- [문제 해결](#-문제-해결)
- [문서](#-문서)
- [로드맵](#-로드맵)
- [기여](#-기여)
- [라이센스](#-라이센스)

---

## ✨ 주요 기능

### 🔍 검색 & 발견
- **키워드 검색**: 제목/설명 전체 텍스트 검색
- **태그 조합 검색**: 포함/제외 조건으로 정밀 필터링
  ```
  예: korea + SF - action → 한국 SF 영화 중 액션 제외
  ```
- **정렬 옵션**: 최신순, 인기순, 평점순, 시청수순
- **카테고리 브라우징**: 장르별 탐색

### 🎬 비디오 스트리밍
- **HLS (HTTP Live Streaming)**: 네트워크 상황에 따른 자동 화질 조정
- **다중 화질 지원**: 480p, 720p, 1080p, 4K
- **화질 선택 UI**: 플레이어 내장 메뉴 (YouTube 스타일)
- **빠른 시킹**: HTTP Range Requests 지원
- **변환 진행률**: HLS 변환 상태 실시간 표시

### 🖼️ 썸네일 시스템
- **자동 생성**: FFmpeg 장면 전환 감지로 10-15개 썸네일 생성
- **호버 미리보기**:
  - **이미지 순환**: 1초 간격으로 12개 썸네일 순환
  - **비디오 클립**: 3초짜리 MP4 클립 7개 자동 재생 (Netflix 방식)
- **썸네일 관리**: 원하는 썸네일을 메인 이미지로 설정
- **외부 이미지**: 포스터 이미지 등 커스텀 업로드 가능

### 👤 사용자 & 권한
- **JWT 인증**: 안전한 토큰 기반 인증
- **역할 관리**: user (일반), admin (관리자), premium (추후)
- **Admin 전용**: 비디오 업로드/수정/삭제, 태그 관리

### ⭐ 사용자 상호작용
- **평점 시스템**: 별점 1-5점
- **시청 기록**: 시청한 비디오 자동 추적
- **이어보기**: 마지막 시청 위치에서 재개
- **진행률 표시**: 비디오 카드에 시청 진행률 바

### ⚡ 성능 최적화
- **DB 인덱스**: 검색 및 정렬 쿼리 최적화
- **프론트엔드**: 코드 스플리팅, 메모이제이션, Lazy Loading
- **캐시 제어**: 브라우저 캐싱 방지로 즉시 업데이트

---

## 🛠️ 기술 스택

### 백엔드
```
FastAPI 0.104+           # 비동기 웹 프레임워크
Python 3.11+             # 프로그래밍 언어
PostgreSQL 14+           # 관계형 데이터베이스
SQLAlchemy 2.0+          # ORM
Alembic                  # DB 마이그레이션
python-jose              # JWT 인증
passlib                  # 비밀번호 해싱
FFmpeg 6.0+              # 비디오 처리
```

### 프론트엔드
```
React 18                 # UI 라이브러리
TypeScript 5.0+          # 타입 안정성
Vite 5.0+                # 빌드 도구
Tailwind CSS 3.3+        # 스타일링
React Router 6.20+       # 라우팅
Zustand 4.4+             # 상태 관리
Axios 1.6+               # HTTP 클라이언트
Video.js 8.0+            # 비디오 플레이어
```

### 인프라
```
Docker                   # 컨테이너화 (추후)
라즈베리파이 4B/5 (8GB)   # 서버 하드웨어
외장 HDD 4TB             # 스토리지
```

---

## 💻 시스템 요구사항

### 최소 사양
- **CPU**: 2 cores
- **RAM**: 2GB (권장: 4GB 이상)
- **저장공간**: 10GB + 비디오 저장용 공간
- **OS**:
  - Raspberry Pi OS (64-bit)
  - Ubuntu 20.04+
  - macOS 11+
  - Windows 10/11 (WSL2)

### 권장 사양 (라즈베리파이)
- **모델**: Raspberry Pi 4B/5
- **RAM**: 8GB
- **저장공간**: 4TB 외장 HDD (USB 3.0)
- **네트워크**: 유선 이더넷 연결

### 필수 소프트웨어
- Python 3.11+
- PostgreSQL 14+
- FFmpeg 6.0+
- Node.js 18+
- Git

---

## 🚀 빠른 시작

> **자동 설치**: `./setup.sh` 스크립트를 실행하면 대부분의 설정을 자동화할 수 있습니다.

### 1. 저장소 클론
```bash
git clone https://github.com/ph3ntom/videoServer2026.git
cd videoServer2026
```

### 2. 자동 설치 (추천)
```bash
chmod +x setup.sh
./setup.sh
# 스크립트가 안내하는 데로 데이터베이스 설정 및 .env 파일 수정
```

**또는 수동 설치를 원하시면 아래 단계를 따르세요.**

### 3. 데이터베이스 생성
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE streamflix;
CREATE USER streamflix WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE streamflix TO streamflix;
\q
```

### 3. 백엔드 설정
```bash
cd backend

# 가상환경 생성 및 활성화
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
nano .env  # 아래 항목들을 수정하세요

# 필수 수정 항목:
# DATABASE_URL=postgresql+asyncpg://streamflix:your_password@localhost:5432/streamflix
# SECRET_KEY=<아래 명령으로 생성한 랜덤 키>
# python -c "import secrets; print(secrets.token_urlsafe(32))"

# 데이터베이스 마이그레이션
alembic upgrade head

# 슈퍼 관리자 생성
python create_admin.py
```

### 4. 프론트엔드 설정
```bash
cd ../frontend

# 의존성 설치
npm install

# 환경변수 설정 (필요시)
cp .env.example .env
nano .env
```

### 5. 실행
```bash
# 백엔드 (터미널 1)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 (터미널 2)
cd frontend
npm run dev
```

**접속**:
- 프론트엔드: http://localhost:5173
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs

---

## 📦 설치 가이드

<details>
<summary><b>Raspberry Pi (Raspbian/Debian)</b></summary>

### 1. 시스템 업데이트
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 필수 패키지 설치
```bash
# Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# FFmpeg
sudo apt install -y ffmpeg

# Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Git
sudo apt install -y git
```

### 3. 외장 HDD 마운트
```bash
# USB 장치 확인
lsblk

# 파일시스템 생성 (필요시)
sudo mkfs.ext4 /dev/sda1

# 마운트 포인트 생성
sudo mkdir -p /mnt/external_hdd

# 마운트
sudo mount /dev/sda1 /mnt/external_hdd

# 자동 마운트 설정
echo "/dev/sda1 /mnt/external_hdd ext4 defaults 0 2" | sudo tee -a /etc/fstab

# 디렉토리 생성 및 권한 설정
sudo mkdir -p /mnt/external_hdd/videos /mnt/external_hdd/thumbnails
sudo chown -R $USER:$USER /mnt/external_hdd
```

### 4. 환경변수 설정 (.env)
```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://streamflix:your_password@localhost/streamflix
SECRET_KEY=your_secret_key_here
UPLOAD_DIR=/mnt/external_hdd/videos
FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe
```

</details>

<details>
<summary><b>Ubuntu/Linux</b></summary>

### 1. 시스템 업데이트
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 필수 패키지 설치
```bash
# Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# FFmpeg
sudo apt install -y ffmpeg

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Git
sudo apt install -y git
```

</details>

<details>
<summary><b>macOS</b></summary>

### 1. Homebrew 설치 (없는 경우)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. 필수 패키지 설치
```bash
# Python 3.11
brew install python@3.11

# PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# FFmpeg
brew install ffmpeg

# Node.js
brew install node@18

# Git
brew install git
```

### 3. 데이터베이스 생성
```bash
psql postgres
```

```sql
CREATE DATABASE streamflix;
CREATE USER streamflix WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE streamflix TO streamflix;
\q
```

</details>

<details>
<summary><b>Windows (WSL2)</b></summary>

### 1. WSL2 설치
```powershell
# PowerShell을 관리자 권한으로 실행
wsl --install -d Ubuntu-22.04
```

### 2. Ubuntu 재시작 후 패키지 설치
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib
sudo service postgresql start

# FFmpeg
sudo apt install -y ffmpeg

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

</details>

---

## 📁 프로젝트 구조

```
videos_web_server/
├── backend/                    # 백엔드 (FastAPI)
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/            # API 엔드포인트
│   │   │       ├── auth.py    # 인증 API
│   │   │       ├── users.py   # 사용자 API
│   │   │       ├── videos.py  # 비디오 API (50+ 엔드포인트)
│   │   │       ├── tags.py    # 태그 API
│   │   │       └── ...
│   │   ├── core/              # 설정 및 보안
│   │   │   ├── config.py      # 환경 설정
│   │   │   ├── security.py    # JWT, 비밀번호 해싱
│   │   │   └── deps.py        # 의존성
│   │   ├── models/            # SQLAlchemy 모델 (10개)
│   │   │   ├── user.py
│   │   │   ├── video.py
│   │   │   ├── tag.py
│   │   │   ├── rating.py
│   │   │   ├── watch_history.py
│   │   │   └── ...
│   │   ├── schemas/           # Pydantic 스키마
│   │   ├── services/          # 비즈니스 로직
│   │   │   ├── video_service.py
│   │   │   ├── thumbnail_service.py  # 썸네일 & 미리보기 클립
│   │   │   ├── hls_service.py        # HLS 변환
│   │   │   └── ...
│   │   ├── utils/             # 유틸리티
│   │   └── main.py            # FastAPI 앱
│   ├── alembic/               # 데이터베이스 마이그레이션 (15+)
│   ├── create_admin.py        # 관리자 생성 스크립트
│   ├── generate_preview_clips.py  # 미리보기 클립 생성
│   ├── requirements.txt
│   └── .env
│
├── frontend/                  # 프론트엔드 (React)
│   ├── src/
│   │   ├── components/        # React 컴포넌트 (20+)
│   │   │   ├── layout/        # Header, Footer
│   │   │   └── video/         # VideoCard, VideoPlayer
│   │   ├── pages/             # 페이지 컴포넌트 (10+)
│   │   │   ├── Home.tsx
│   │   │   ├── VideoPlayer.tsx
│   │   │   ├── Search.tsx
│   │   │   ├── Admin/
│   │   │   └── ...
│   │   ├── hooks/             # 커스텀 훅
│   │   ├── services/          # API 클라이언트
│   │   │   └── api.client.ts
│   │   ├── store/             # Zustand 스토어
│   │   │   └── authStore.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── .env
│
├── doc/                       # 문서
│   ├── 01_프로젝트_개요.md
│   ├── 02_기술_스택.md
│   ├── 03_시스템_아키텍처.md
│   ├── 04_데이터베이스_스키마.md
│   ├── 05_API_명세서.md
│   ├── 06_개발_로드맵.md
│   ├── 07_핵심_요구사항_명세.md
│   ├── Phase1-MVP-Status.md
│   ├── v1.0-Release-Notes.md
│   ├── dev_Process/           # 버전별 개발 문서 (17개)
│   │   ├── 1.v0.1-authentication.md
│   │   ├── 15.v0.13-phase-3.2-hls-streaming.md
│   │   ├── 17.v1.0-preview-clips-implementation.md
│   │   └── ...
│   └── archive/               # 아카이브 문서
│
└── README.md
```

---

## 🔧 데이터베이스 마이그레이션

### 마이그레이션 생성
```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Description of changes"
```

### 마이그레이션 적용
```bash
alembic upgrade head
```

### 마이그레이션 롤백
```bash
alembic downgrade -1
```

### 현재 버전 확인
```bash
alembic current
```

### 마이그레이션 히스토리
```bash
alembic history
```

---

## 🛠️ 문제 해결

### 초기 설치 시 자주 발생하는 오류

#### 1. Alembic 마이그레이션 실패
```bash
# 오류: sqlalchemy.exc.ProgrammingError: relation "users" already exists
# 해결: 데이터베이스 초기화 후 다시 마이그레이션
psql -U streamflix -d streamflix -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
cd backend
source venv/bin/activate
alembic upgrade head
```

#### 2. Storage 디렉토리 없음 오류
```bash
# 오류: FileNotFoundError: [Errno 2] No such file or directory: 'storage/videos'
# 해결: 디렉토리 수동 생성
mkdir -p storage/videos storage/videos/thumbnails storage/thumbnails
chmod 755 storage
```

#### 3. SECRET_KEY 관련 오류
```bash
# 오류: SECRET_KEY not set
# 해결: .env 파일에 랜덤 키 생성
cd backend
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')" >> .env
```

#### 4. 의존성 설치 실패
```bash
# 오류: pip install 실패
# 해결: pip 업그레이드 후 재시도
cd backend
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### PostgreSQL 연결 오류
```bash
# PostgreSQL 서비스 상태 확인
# Linux/Raspberry Pi:
sudo systemctl status postgresql
sudo systemctl restart postgresql

# macOS:
brew services list
brew services restart postgresql@14

# 연결 테스트
psql -U streamflix -d streamflix -h localhost
```

### Python 가상환경 활성화 오류
```bash
# 가상환경 재생성
cd backend
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### FFmpeg 명령어 찾을 수 없음
```bash
# FFmpeg 경로 확인
which ffmpeg
which ffprobe

# .env 파일 수정
FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe
```

### 포트 충돌
```bash
# 포트 사용 중인 프로세스 확인
# Linux/macOS:
lsof -i :8000  # 백엔드
lsof -i :5173  # 프론트엔드

# 프로세스 종료
kill -9 <PID>
```

### 외장 HDD 마운트 실패
```bash
# 장치 확인
lsblk
dmesg | tail

# 수동 마운트
sudo mount -t ext4 /dev/sda1 /mnt/external_hdd

# 권한 문제
sudo chown -R $USER:$USER /mnt/external_hdd
sudo chmod -R 755 /mnt/external_hdd
```

### 썸네일/미리보기 클립 생성 실패
```bash
# FFmpeg 버전 확인 (6.0+ 권장)
ffmpeg -version

# 수동으로 생성 (기존 비디오)
cd backend
source venv/bin/activate
python generate_preview_clips.py
```

### HLS 변환 진행 안됨
```bash
# 백엔드 로그 확인
cd backend
tail -f app.log

# FFmpeg 프로세스 확인
ps aux | grep ffmpeg

# 수동 변환 테스트
python test_hls_conversion.py
```

---

## 📚 문서

### 사용자 가이드
- [프로젝트 개요](doc/01_프로젝트_개요.md)
- [핵심 요구사항](doc/07_핵심_요구사항_명세.md)
- [v1.0 릴리즈 노트](doc/v1.0-Release-Notes.md)

### 개발자 가이드
- [기술 스택](doc/02_기술_스택.md)
- [시스템 아키텍처](doc/03_시스템_아키텍처.md)
- [데이터베이스 스키마](doc/04_데이터베이스_스키마.md)
- [API 명세서](doc/05_API_명세서.md)
- [개발 로드맵](doc/06_개발_로드맵.md)

### 개발 히스토리
- [Phase 1 MVP 완성](doc/Phase1-MVP-Status.md)
- [버전별 개발 문서](doc/dev_Process/)
  - [v0.1: 인증 시스템](doc/dev_Process/1.v0.1-authentication.md)
  - [v0.13: HLS 스트리밍](doc/dev_Process/15.v0.13-phase-3.2-hls-streaming.md)
  - [v1.0: 미리보기 클립](doc/dev_Process/17.v1.0-preview-clips-implementation.md)

---

## 🗺️ 로드맵

### ✅ v1.0 (완료 - 2026-02-06)
- ✅ JWT 인증 & 권한 시스템
- ✅ 비디오 업로드/스트리밍
- ✅ 태그 조합 검색
- ✅ 썸네일 자동 생성 & 호버 미리보기
- ✅ 평점 시스템
- ✅ 시청 기록 & 이어보기
- ✅ HLS 적응형 스트리밍
- ✅ 미리보기 클립 (3초 MP4, 7개)

### 🔜 v1.1 (예정)
- [ ] 자막 지원 (.srt, .vtt)
- [ ] 관리자 대시보드 (통계)
- [ ] E2E 테스트 (Playwright)
- [ ] Docker 단일 컨테이너 배포
- [ ] Rate Limiting (보안 강화)

### 🔮 v1.2 (예정)
- [ ] 추천 시스템 (협업 필터링)
- [ ] 플레이리스트
- [ ] 알림 시스템
- [ ] CDN 통합

### 🚀 v2.0 (장기)
- [ ] 다중 오디오 트랙
- [ ] 라이브 스트리밍
- [ ] 소셜 기능 (댓글, 좋아요)
- [ ] 모바일 앱 (React Native)

---

## 🤝 기여

이슈 및 Pull Request는 언제든지 환영합니다!

### 기여 가이드
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📊 통계

```
총 개발 기간: 31일 (2026-01-06 ~ 2026-02-06)
총 커밋 수: 20+
총 버전 수: 17개 (v0.1 ~ v1.0)
코드 라인 수: ~14,000 lines
```

**버전 히스토리**:
- v0.1-v0.7: Phase 1 MVP (인증, 비디오, 태그, 검색)
- v0.8-v0.12: Phase 2 (평점, 시청기록, 성능 최적화)
- v0.13-v0.13.1: Phase 3.2 (HLS 스트리밍)
- **v1.0**: 미리보기 클립 & 정식 릴리즈

---

## 📄 라이센스

This project is licensed under the MIT License.

---

## 📞 문의

프로젝트 관련 문의사항은 GitHub Issues를 이용해주세요.

---

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들의 도움을 받았습니다:

- **FastAPI** - 훌륭한 비동기 웹 프레임워크
- **React** - 강력한 UI 라이브러리
- **Video.js** - 유연한 비디오 플레이어
- **FFmpeg** - 비디오 처리의 스위스 아미 나이프
- **PostgreSQL** - 안정적인 데이터베이스
- **Raspberry Pi Foundation** - 저렴하고 강력한 하드웨어

---

<div align="center">

**StreamFlix v1.0** - 개인용 스트리밍 플랫폼의 완성

Made with ❤️ for personal use

[Documentation](doc/) • [Release Notes](doc/v1.0-Release-Notes.md) • [Report Bug](https://github.com/yourusername/streamflix/issues) • [Request Feature](https://github.com/yourusername/streamflix/issues)

</div>
