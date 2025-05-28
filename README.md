# ParseNoteLM

AI 기반 문서 분석 및 질의응답 서비스 MVP

## 프로젝트 개요

ParseNoteLM은 대학생과 대학원생을 위한 AI 기반 문서 분석 서비스입니다. PDF, TXT 파일을 업로드하여 AI가 분석하고, RAG(Retrieval-Augmented Generation) 기술을 통해 문서 내용에 대한 질의응답을 제공합니다.

## 기술 스택

### 백엔드
- Python 3.11 - 주 프로그래밍 언어
- FastAPI 0.95.1 - 웹 프레임워크
- SQLite / PostgreSQL - 데이터베이스 (개발/프로덕션)
- SQLAlchemy 2.0 - ORM
- JWT 토큰 - 인증 시스템
- BCrypt - 비밀번호 해싱
- OpenAI API - AI 서비스 (향후 구현)

### 프론트엔드 (향후 구현)
- React 18 - UI 라이브러리
- TypeScript 4.9 - 타입 시스템
- Tailwind CSS 3.3 - 스타일링

## 현재 구현된 기능

### Task 2: 사용자 인증 시스템 (완료)
- 사용자 등록/로그인 - 이메일 기반 회원가입 및 로그인
- JWT 토큰 인증 - 안전한 토큰 기반 인증 시스템
- 비밀번호 재설정 - 이메일 기반 비밀번호 재설정 (토큰 30분 유효)
- 사용자 프로필 관리 - 프로필 조회 및 업데이트
- 권한 관리 시스템 (RBAC) - USER, PREMIUM, ADMIN 역할 기반 접근 제어
- 로그인 시도 제한 - 보안을 위한 Rate Limiting
- 관리자 기능 - 사용자 관리 및 시스템 통계

### Task 3: 데이터베이스 스키마 (완료)
- 완전한 데이터 모델 설계 - User, Project, Document, Embedding, ChatHistory
- 관계형 데이터베이스 설계 - 외래키 관계 및 데이터 무결성
- Pydantic 스키마 - API 요청/응답 검증 및 직렬화
- 소프트 삭제 지원 - 데이터 복구 가능한 삭제 시스템

### Task 4: 문서 업로드 및 처리 (완료)
- 파일 업로드 시스템 - PDF, TXT 파일 업로드 지원
- 파일 검증 - 10MB 크기 제한, 허용된 파일 형식 검증
- 사용자별/프로젝트별 파일 저장 - 체계적인 디렉토리 구조
- TXT 파일 내용 추출 - 업로드 즉시 텍스트 내용 추출
- 문서 CRUD API - 생성, 조회, 삭제, 재처리 기능
- 프로젝트당 5개 문서 제한 - 비즈니스 룰 적용

### 향후 구현 예정
- AI 문서 분석 (Task 5)
- RAG 기반 질의응답 (Task 6)
- 프로젝트 관리 (Task 7)
- React 프론트엔드 (Task 8-9)

## 서비스 제한사항

- 사용자당 최대 3개 프로젝트
- 프로젝트당 최대 5개 문서
- 파일 크기 제한: 10MB
- 지원 파일 형식: PDF, TXT (현재 TXT만 완전 지원)

## 설치 및 설정

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/ParseNoteLM.git
cd ParseNoteLM
```

### 2. 백엔드 설정
```bash
cd backend

# Python 가상환경 생성 및 활성화
python3.11 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env 파일 생성)
DATABASE_URL=sqlite:///./parsenotelm.db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### 3. 데이터베이스 초기화
```bash
# 데이터베이스 테이블 생성 및 관리자 계정 생성
python init_db.py
```

기본 관리자 계정:
- 이메일: admin@parsenotelm.com
- 비밀번호: admin123!

## 실행 방법

### 백엔드 서버 시작
```bash
cd backend
source venv/bin/activate

# 개발 서버 실행
export DATABASE_URL="sqlite:///./parsenotelm.db"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

서버 접속:
- API 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs
- OpenAPI 스펙: http://localhost:8000/redoc

## API 사용 예제

### 사용자 등록
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

### 로그인
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### 사용자 프로필 조회 (인증 필요)
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 관리자 - 사용자 목록 조회
```bash
curl -X GET "http://localhost:8000/api/admin/users" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

### 프로젝트 생성
```bash
curl -X POST "http://localhost:8000/api/projects" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "내 프로젝트",
    "description": "프로젝트 설명"
  }'
```

### 문서 업로드
```bash
curl -X POST "http://localhost:8000/api/projects/{project_id}/documents/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@example.txt"
```

### 프로젝트 문서 목록 조회
```bash
curl -X GET "http://localhost:8000/api/projects/{project_id}/documents" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 문서 삭제
```bash
curl -X DELETE "http://localhost:8000/api/documents/{document_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 프로젝트 구조

```
ParseNoteLM/
├── backend/
│   ├── app/
│   │   ├── core/             # 핵심 설정
│   │   │   ├── config.py     # 앱 설정
│   │   │   ├── database.py   # DB 연결
│   │   │   └── security.py   # JWT, 권한 관리
│   │   ├── models/           # 데이터베이스 모델
│   │   │   ├── user.py       # 사용자 모델
│   │   │   ├── project.py    # 프로젝트 모델
│   │   │   ├── document.py   # 문서 모델
│   │   │   ├── embedding.py  # 임베딩 모델
│   │   │   └── chat_history.py # 채팅 기록 모델
│   │   ├── routes/           # API 라우터
│   │   │   ├── auth.py       # 인증 API
│   │   │   ├── admin.py      # 관리자 API
│   │   │   ├── projects.py   # 프로젝트 API
│   │   │   └── documents.py  # 문서 API
│   │   ├── schemas/          # Pydantic 스키마
│   │   │   ├── user.py       # 사용자 스키마
│   │   │   ├── project.py    # 프로젝트 스키마
│   │   │   ├── document.py   # 문서 스키마
│   │   │   ├── embedding.py  # 임베딩 스키마
│   │   │   └── chat_history.py # 채팅 스키마
│   │   ├── services/         # 비즈니스 로직
│   │   │   └── user_service.py
│   │   └── utils/            # 유틸리티
│   │       └── file_validator.py # 파일 검증
│   ├── uploads/              # 업로드된 파일 저장소
│   ├── init_db.py            # DB 초기화 스크립트
│   ├── main.py               # FastAPI 앱 진입점
│   └── requirements.txt      # Python 의존성
├── frontend/                 # 프론트엔드 (향후 구현)
├── tasks/                    # 개발 태스크 관리
├── PRD.md                    # 제품 요구사항 문서
└── README.md
```

## 보안 기능

- JWT 토큰 인증 - 안전한 stateless 인증
- BCrypt 비밀번호 해싱 - 단방향 암호화
- 역할 기반 접근 제어 - USER, PREMIUM, ADMIN 권한
- 로그인 시도 제한 - 무차별 대입 공격 방어
- 비밀번호 재설정 - 안전한 토큰 기반 재설정

## 테스트

### API 테스트
```bash
# 사용자 등록 테스트
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "password": "test123"}'

# 로그인 테스트
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'
```

## 배포

### 개발 환경
- SQLite 데이터베이스 사용
- 로컬 파일 저장

### 프로덕션 환경 (향후)
- PostgreSQL + pgvector 사용
- 클라우드 스토리지 연동
- Docker 컨테이너화

## 기여 가이드라인

1. 이슈를 생성하거나 기존 이슈를 확인합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 라이선스

This project is licensed under the MIT License.