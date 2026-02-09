# Docker 빠른 시작 가이드

StreamFlix를 Docker로 5분 안에 실행하는 방법입니다.

## 1️⃣ 준비

```bash
# Docker 설치 확인
docker --version
docker-compose --version
```

## 2️⃣ 저장소 클론

```bash
git clone https://github.com/ph3ntom/videoServer2026.git
cd videoServer2026
```

## 3️⃣ 환경 변수 설정

```bash
# .env 파일 생성
cp .env.docker .env

# SECRET_KEY 생성
python3 -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')" >> .env

# 비밀번호 설정 (편집기로 열어서 수정)
nano .env
```

**필수 수정:**
```env
POSTGRES_PASSWORD=your_secure_password_here
SECRET_KEY=<위에서 생성된 키>
```

## 4️⃣ 실행

```bash
# 모든 서비스 시작 (백그라운드)
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

## 5️⃣ 관리자 계정 생성

```bash
# 백엔드 컨테이너 접속
docker exec -it streamflix-backend bash

# 관리자 생성
python create_admin.py

# 빠져나오기
exit
```

## 6️⃣ 접속

- 웹사이트: http://localhost
- API 문서: http://localhost:8000/docs
- 관리자 계정: admin@streamflix.com / admin123

## 🛑 중지 및 제거

```bash
# 서비스 중지 (데이터 유지)
docker-compose down

# 완전 삭제 (데이터 포함)
docker-compose down -v
```

## 📚 상세 가이드

전체 Docker 배포 가이드는 [doc/DOCKER-DEPLOYMENT.md](doc/DOCKER-DEPLOYMENT.md)를 참고하세요.

---

## 문제 해결

### 포트 충돌
```bash
# 포트 80이 사용 중인 경우
# docker-compose.yml에서 frontend 포트 수정
ports:
  - "3000:80"  # 80 -> 3000으로 변경
```

### 로그 확인
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

### 재시작
```bash
docker-compose restart
```
