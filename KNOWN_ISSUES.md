# 알려진 문제 및 해결 방법 (Known Issues)

## 📋 개요
ParseNoteLM 프로젝트에서 발생할 수 있는 알려진 문제들과 해결 방법을 정리한 문서입니다.

## 🔧 문서 요약 관련 문제

### 1. 두 번째 문서 요약 실패 문제
**문제 설명:**
- 첫 번째 문서 요약은 성공하지만 두 번째 문서 요약이 실패하는 현상
- "콘텐츠 청크가 비어있음" 오류 발생

**원인:**
1. **벡터 저장소와 데이터베이스 동기화 문제**
   - 데이터베이스에는 문서가 존재하지만 벡터 저장소에 해당 문서의 청크가 없음
   - 문서 처리 상태는 COMPLETED이지만 실제 벡터 인덱싱이 실패

2. **Document ID 타입 불일치 문제**
   - RAG 서비스에서 반환하는 `document_id`는 문자열
   - API에서 비교하는 `document_id`는 정수
   - 필터링 과정에서 타입 불일치로 매칭 실패

3. **JWT 토큰 권한 문제**
   - 잘못된 사용자의 JWT 토큰 사용
   - 프로젝트 소유자와 토큰 사용자 불일치

**해결 방법:**

#### A. 벡터 저장소 재인덱싱
```bash
# 특정 문서 재인덱싱
curl -X POST "http://localhost:8000/api/rag/reindex" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"document_id": 63}'
```

#### B. JWT 토큰 갱신
```bash
# 올바른 사용자로 로그인
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "your_email@gmail.com", "password": "your_password"}'
```

#### C. 백엔드 코드 수정 (이미 적용됨)
```python
# /backend/app/routes/rag.py의 필터링 로직 개선
filtered_results = [
    r for r in search_results 
    if int(r['document_id']) if isinstance(r['document_id'], str) else r['document_id'] == document_id
]
```

### 2. 문서 처리 상태 불일치
**문제 설명:**
- 문서 상태가 COMPLETED이지만 실제로는 처리되지 않음
- 청크 수는 0이지만 상태는 완료로 표시

**해결 방법:**
1. 문서 상태 확인 스크립트 실행
```bash
cd backend
python check_db_state.py
```

2. 문제가 있는 문서 재처리
```bash
# 문서 재업로드 또는 재인덱싱
```

## 🔍 디버깅 도구

### 데이터베이스 상태 확인
```bash
cd backend
source venv/bin/activate
python check_db_state.py
```

### 특정 프로젝트 상태 확인
```bash
cd backend
source venv/bin/activate
python check_project_13.py
```

### 요약 API 테스트
```bash
cd backend
source venv/bin/activate
python test_summary.py
```

## 📊 성능 최적화

### 1. 벡터 검색 성능
- FAISS 인덱스 최적화 필요
- 대용량 문서 처리 시 메모리 사용량 증가

### 2. 토큰 사용량 최적화
- 긴 문서의 경우 요약 시 토큰 사용량이 많음 (2000-3000 토큰)
- 청크 크기 조정으로 최적화 가능

## 🚧 개발 환경 문제

### 1. 모듈 Import 에러
**문제:** `ModuleNotFoundError: No module named 'app.models.database'`
**해결:** 올바른 import 경로 사용
```python
# 잘못된 경로
from app.models.database import Project, Document, User

# 올바른 경로
from app.models.user import User
from app.models.project import Project  
from app.models.document import Document
```

### 2. 백엔드 서버 시작 실패
**문제:** `Error loading ASGI app. Could not import module "app.main"`
**해결:** 올바른 uvicorn 명령어 사용
```bash
# 백엔드 폴더에서
cd backend
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📞 문제 해결이 안 될 때

1. **로그 확인:**
   ```bash
   tail -f logs/parsenotelm.log
   ```

2. **데이터베이스 초기화:** (주의: 모든 데이터 삭제됨)
   ```bash
   rm backend/parsenotelm.db
   # 서버 재시작
   ```

3. **벡터 저장소 초기화:**
   ```bash
   rm -rf backend/data/vector_stores/*
   # 문서 재업로드 필요
   ```

## 💡 예방 방법

1. **정기적인 동기화 확인**
   - 문서 업로드 후 벡터 저장소 상태 확인
   - 주기적인 데이터 일관성 검사

2. **적절한 에러 처리**
   - 타입 안전성 확보
   - 상세한 로깅으로 디버깅 용이성 확보

3. **테스트 자동화**
   - 요약 API 테스트 스크립트 활용
   - CI/CD 파이프라인에 테스트 포함

---

**마지막 업데이트:** 2025-06-02  
**버전:** 1.0.0
