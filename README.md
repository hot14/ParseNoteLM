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
- OpenAI API - AI 서비스 (✅ 완료)

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

### Task 5: OpenAI API 통합 (완료) 
- **문서 분석 API** - AI를 통한 자동 문서 분석
  - 텍스트 요약 - 핵심 내용 자동 추출
  - 키워드 추출 - 중요 키워드 식별
  - 카테고리 분류 - 문서 유형 자동 분류
  - 주제 추출 - 문서 주요 주제 파악
  - 난이도 평가 - 초급/중급/고급 자동 판별
- **텍스트 요약 API** - 긴 텍스트의 간결한 요약
- **임베딩 생성 API** - 1536차원 벡터 임베딩 생성
- **질의응답 API** - RAG 기반 컨텍스트 활용 답변 생성
- **완전한 OpenAI API 통합** - 모든 AI 기능 정상 작동

### Task 6: RAG 시스템 (완료)
- **문서 청킹 시스템** - 의미적 단위로 문서 분할 (512자 청크, 50자 겹침)
- **벡터 검색 엔진** - OpenAI 임베딩 + FAISS 기반 유사도 검색
- **RAG 파이프라인** - 검색-증강-생성 전체 프로세스 구현
- **컨텍스트 기반 답변** - GPT-3.5-turbo 활용 정확한 답변 생성
- **소스 추적 시스템** - 답변의 근거 문서 및 위치 제공
- **채팅 기록 관리** - 대화 히스토리 저장 및 조회
- **피드백 시스템** - 답변 품질 개선을 위한 사용자 피드백

### Task 7: 프로젝트 멤버 관리 (완료)
- **역할 기반 권한 시스템** - OWNER, ADMIN, EDITOR, VIEWER 4단계 권한
- **멤버 초대 시스템** - 이메일 기반 프로젝트 멤버 초대
- **권한 관리** - 역할별 세분화된 접근 제어
  - OWNER: 모든 권한 (프로젝트 관리, 멤버 관리, 문서 편집)
  - ADMIN: 멤버 관리, 문서 편집
  - EDITOR: 문서 편집
  - VIEWER: 문서 조회만 가능
- **멤버 관리 API** - 초대, 조회, 업데이트, 제거 기능
- **통계 시스템** - 프로젝트별 멤버 통계 및 역할 분포
- **소프트 삭제** - 멤버 제거 후 재초대 가능

### 향후 구현 예정
- 프로젝트 대시보드 및 관리 UI (Task 8)
- React 프론트엔드 (Task 9-10)
- 사용량 추적 및 제한 (Task 11)
- 성능 최적화 (Task 12) 
- 로깅 및 모니터링 (Task 13)

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
    "title": "내 프로젝트",
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

### OpenAI API 사용 예제 

#### 문서 분석
```bash
curl -X POST "http://localhost:8000/api/openai/analyze" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "인공지능은 머신러닝과 딥러닝 기술을 통해 인간의 지능을 모방하는 기술입니다."
  }'
```

#### 텍스트 요약
```bash
curl -X POST "http://localhost:8000/api/openai/summary" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "긴 텍스트 내용을 여기에 입력합니다...",
    "max_length": 100
  }'
```

#### 임베딩 생성
```bash
curl -X POST "http://localhost:8000/api/openai/embedding" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "임베딩으로 변환할 텍스트"
  }'
```

#### 질의응답 (RAG)
```bash
curl -X POST "http://localhost:8000/api/openai/answer" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "인공지능이 무엇인가요?",
    "context": "인공지능은 머신러닝과 딥러닝 기술을 통해 인간의 지능을 모방하는 기술입니다."
  }'
```

### 프로젝트 멤버 관리 API

#### 멤버 초대
```bash
curl -X POST "http://localhost:8000/api/projects/{project_id}/members" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "member@example.com",
    "role": "editor"
  }'
```

#### 멤버 목록 조회
```bash
curl -X GET "http://localhost:8000/api/projects/{project_id}/members" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 멤버 역할 업데이트
```bash
curl -X PUT "http://localhost:8000/api/projects/{project_id}/members/{member_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin"
  }'
```

#### 멤버 통계 조회
```bash
curl -X GET "http://localhost:8000/api/projects/{project_id}/members/stats" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 멤버 제거
```bash
curl -X DELETE "http://localhost:8000/api/projects/{project_id}/members/{member_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 테스트

### OpenAI API 통합 테스트 
```bash
# 완전한 OpenAI API 통합 테스트 실행
cd backend
python test_openai_integration.py

# 테스트 결과: 6/6 성공
# 사용자 등록/로그인
# 프로젝트 생성  
# 문서 분석 (요약, 키워드, 카테고리, 주제, 난이도)
# 텍스트 요약 (45% 압축률)
# 임베딩 생성 (1536차원)
# RAG 기반 질의응답
```

### 프로젝트 멤버 관리 테스트
```bash
# 프로젝트 멤버 관리 기능 테스트 실행
cd backend
python test_project_members.py

# 테스트 결과: 6/6 성공
# 사용자 등록 (3명: 소유자, 편집자, 뷰어)
# 프로젝트 생성 및 소유자 로그인
# 멤버 초대 (editor, viewer 역할)
# 멤버 목록 조회 (총 3명)
# 멤버 통계 조회 (소유자 1명, 편집자 1명, 뷰어 1명)
# 역할 기반 권한 시스템 검증
```

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