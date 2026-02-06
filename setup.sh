#!/bin/bash
# StreamFlix v1.0 Setup Script

set -e

echo "🚀 StreamFlix v1.0 설치 시작..."
echo ""

# Check Python version
echo "1️⃣  Python 버전 확인..."
python3 --version || { echo "❌ Python 3.8+ 필요"; exit 1; }

# Check Node version
echo "2️⃣  Node.js 버전 확인..."
node --version || { echo "❌ Node.js 16+ 필요"; exit 1; }

# Check PostgreSQL
echo "3️⃣  PostgreSQL 확인..."
psql --version || { echo "❌ PostgreSQL 필요"; exit 1; }

# Check FFmpeg
echo "4️⃣  FFmpeg 확인..."
ffmpeg -version > /dev/null 2>&1 || { echo "❌ FFmpeg 필요"; exit 1; }

echo ""
echo "✅ 모든 필수 프로그램 설치 확인 완료"
echo ""

# Backend setup
echo "📦 백엔드 설정 중..."
cd backend

if [ ! -f ".env" ]; then
    echo "  - .env 파일 생성 중..."
    cp .env.example .env
    echo "  ⚠️  backend/.env 파일을 수정하여 데이터베이스 정보를 입력하세요!"
fi

echo "  - Python 가상환경 생성 중..."
python3 -m venv venv

echo "  - 의존성 패키지 설치 중..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ 백엔드 설정 완료"
echo ""

# Frontend setup
cd ../frontend
echo "📦 프론트엔드 설정 중..."

if [ ! -f ".env" ]; then
    echo "  - .env 파일 생성 중..."
    cp .env.example .env
fi

echo "  - npm 패키지 설치 중..."
npm install

echo ""
echo "✅ 프론트엔드 설정 완료"
echo ""

# Storage directories
cd ..
echo "📁 스토리지 디렉토리 확인 중..."
mkdir -p storage/videos storage/videos/thumbnails storage/thumbnails
echo "✅ 스토리지 디렉토리 생성 완료"
echo ""

# Database setup reminder
echo "═══════════════════════════════════════════════════════════"
echo "📋 다음 단계를 진행하세요:"
echo ""
echo "1. PostgreSQL 데이터베이스 생성:"
echo "   psql -U postgres"
echo "   CREATE DATABASE streamflix;"
echo "   CREATE USER streamflix WITH PASSWORD 'your_password';"
echo "   GRANT ALL PRIVILEGES ON DATABASE streamflix TO streamflix;"
echo "   \\q"
echo ""
echo "2. backend/.env 파일 수정:"
echo "   DATABASE_URL=postgresql+asyncpg://streamflix:your_password@localhost:5432/streamflix"
echo "   SECRET_KEY=<랜덤한 비밀키 생성>"
echo ""
echo "3. 데이터베이스 마이그레이션:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   alembic upgrade head"
echo ""
echo "4. 관리자 계정 생성:"
echo "   python create_admin.py"
echo ""
echo "5. 서버 실행:"
echo "   # 터미널 1 - 백엔드"
echo "   cd backend && source venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "   # 터미널 2 - 프론트엔드"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "6. 브라우저에서 접속:"
echo "   http://localhost:5173"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "✅ 설치 스크립트 완료!"
