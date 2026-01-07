# StreamFlix

라즈베리파이 기반 경량 스트리밍 플랫폼

## 목차
- [시스템 요구사항](#시스템-요구사항)
- [설치 가이드](#설치-가이드)
  - [Raspberry Pi (Raspbian/Debian)](#raspberry-pi-raspbiandeb)
  - [Ubuntu/Linux](#ubuntulinux)
  - [macOS](#macos)
  - [Windows (WSL2)](#windows-wsl2)
- [개발 환경 설정](#개발-환경-설정)
- [프로젝트 구조](#프로젝트-구조)
- [데이터베이스 마이그레이션](#데이터베이스-마이그레이션)
- [실행 방법](#실행-방법)
- [문제 해결](#문제-해결)

## 시스템 요구사항

### 최소 사양
- CPU: 2 cores
- RAM: 2GB (권장: 4GB 이상)
- 저장공간: 10GB + 비디오 저장용 외장 하드
- OS: Raspberry Pi OS (64-bit), Ubuntu 20.04+, macOS 11+, Windows 10/11 (WSL2)

### 권장 사양 (Raspberry Pi 4B/5)
- RAM: 8GB
- 외장 HDD: 1TB 이상 (USB 3.0)
- 네트워크: 유선 이더넷 연결

## 설치 가이드

### Raspberry Pi (Raspbian/Debian)

#### 1. 시스템 업데이트
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. 필수 패키지 설치
```bash
# Python 3.11 설치
sudo apt install -y python3.11 python3.11-venv python3-pip

# PostgreSQL 설치
sudo apt install -y postgresql postgresql-contrib

# FFmpeg 설치 (비디오 처리)
sudo apt install -y ffmpeg

# Node.js 18.x 설치
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Git 설치
sudo apt install -y git
```

#### 3. 외장 HDD 마운트
```bash
# USB 장치 확인
lsblk

# 파일시스템이 없으면 포맷 (예: /dev/sda1)
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

### Ubuntu/Linux

#### 1. 시스템 업데이트
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. 필수 패키지 설치
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

### macOS

#### 1. Homebrew 설치 (없는 경우)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. 필수 패키지 설치
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

#### 3. Python 경로 확인
```bash
which python3.11
# /usr/local/bin/python3.11 또는 /opt/homebrew/bin/python3.11
```

### Windows (WSL2)

#### 1. WSL2 설치
```powershell
# PowerShell을 관리자 권한으로 실행
wsl --install -d Ubuntu-22.04
```

#### 2. Ubuntu 재시작 후 패키지 설치
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

## 개발 환경 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd videos_web_server
```

### 2. PostgreSQL 데이터베이스 생성

#### Linux/Raspberry Pi
```bash
sudo -u postgres psql

# PostgreSQL 쉘에서
CREATE DATABASE streamflix;
CREATE USER streamflix WITH ENCRYPTED PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE streamflix TO streamflix;
\q
```

#### macOS
```bash
psql postgres

# PostgreSQL 쉘에서
CREATE DATABASE streamflix;
CREATE USER streamflix WITH ENCRYPTED PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE streamflix TO streamflix;
\q
```

### 3. 백엔드 설정

```bash
cd backend

# 가상환경 생성
python3.11 -m venv venv

# 가상환경 활성화
# Linux/macOS:
source venv/bin/activate
# Windows (WSL):
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 환경변수 파일 생성
cp .env.example .env

# .env 파일 수정 (데이터베이스 비밀번호, SECRET_KEY 등)
nano .env
```

### 4. 프론트엔드 설정

```bash
cd ../frontend

# 의존성 설치
npm install

# 환경변수 파일 생성
cp .env.example .env

# .env 파일 수정 (필요시)
nano .env
```

## 프로젝트 구조

```
videos_web_server/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/          # API 엔드포인트
│   │   ├── core/            # 설정 및 보안
│   │   ├── models/          # SQLAlchemy 모델
│   │   ├── schemas/         # Pydantic 스키마
│   │   ├── services/        # 비즈니스 로직
│   │   ├── utils/           # 유틸리티 함수
│   │   └── main.py          # FastAPI 애플리케이션
│   ├── alembic/             # 데이터베이스 마이그레이션
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/      # React 컴포넌트
│   │   ├── pages/           # 페이지 컴포넌트
│   │   ├── hooks/           # 커스텀 훅
│   │   ├── services/        # API 클라이언트
│   │   ├── store/           # Zustand 스토어
│   │   └── main.tsx         # 진입점
│   ├── package.json
│   └── .env
├── doc/                     # 문서
└── README.md
```

## 데이터베이스 마이그레이션

### Alembic 초기화 (이미 설정됨)
```bash
cd backend
source venv/bin/activate
alembic init alembic
```

### 마이그레이션 생성
```bash
alembic revision --autogenerate -m "Initial migration"
```

### 마이그레이션 실행
```bash
alembic upgrade head
```

### 마이그레이션 롤백
```bash
alembic downgrade -1
```

## 실행 방법

### 개발 환경

#### 1. 백엔드 실행
```bash
cd backend
source venv/bin/activate
python -m app.main

# 또는 uvicorn 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

백엔드 서버: http://localhost:8000
API 문서: http://localhost:8000/docs

#### 2. 프론트엔드 실행 (새 터미널)
```bash
cd frontend
npm run dev
```

프론트엔드 서버: http://localhost:5173

### 프로덕션 환경 (Docker)

> Docker 설정은 개발 진행 중입니다. 현재는 개발 환경에서 실행해주세요.

## 문제 해결

### PostgreSQL 연결 오류
```bash
# PostgreSQL 서비스 상태 확인
# Linux/Raspberry Pi:
sudo systemctl status postgresql

# macOS:
brew services list

# 서비스 재시작
# Linux:
sudo systemctl restart postgresql

# macOS:
brew services restart postgresql@14
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

# .env 파일의 FFMPEG_PATH 수정
FFMPEG_PATH=/usr/bin/ffmpeg  # 또는 실제 경로
```

### Node.js 버전 문제
```bash
# Node.js 버전 확인 (18.x 필요)
node --version

# nvm으로 버전 관리 (선택사항)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
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

### 포트 충돌
```bash
# 포트 사용 중인 프로세스 확인
# Linux/macOS:
lsof -i :8000  # 백엔드 포트
lsof -i :5173  # 프론트엔드 포트

# 프로세스 종료
kill -9 <PID>
```

## 라이센스

MIT License

## 기여

이슈 및 PR은 언제든지 환영합니다.

## 문의

프로젝트 관련 문의사항은 이슈를 등록해주세요.
