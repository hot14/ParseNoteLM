# ParseNoteLM 문제 해결 가이드

이 문서는 개발 과정에서 발생한 주요 문제들과 해결 방법을 기록합니다.

## 데이터베이스 연결 문제

### 문제 1: 환경변수 로딩 실패
**증상**: `.env` 파일이 존재하지만 환경변수가 제대로 읽히지 않음
**원인**: `dotenv.load_dotenv()`가 호출되지 않음
**해결책**: 
```python
# app/core/config.py
from dotenv import load_dotenv
load_dotenv()  # 명시적으로 .env 파일 로드
```

### 문제 2: 데이터베이스 경로 문제
**증상**: `sqlite:///./backend/parsenotelm.db` 같은 상대경로로 인한 연결 실패
**원인**: 실행 위치에 따라 상대경로가 달라짐
**해결책**:
```python
@property
def DATABASE_URL(self) -> str:
    """데이터베이스 URL을 절대경로로 변환"""
    if self._DATABASE_URL.startswith("sqlite:///./backend/"):
        db_path = self._DATABASE_URL.replace("sqlite:///./backend/", "")
        abs_path = f"/Users/kelly/Desktop/Space/[2025]/ParseNoteLM/backend/{db_path}"
        return f"sqlite:///{abs_path}"
    # 기타 상대경로 처리 로직...
    return self._DATABASE_URL
```

### 문제 3: SQLAlchemy 2.0 호환성
**증상**: `AttributeError: 'str' object has no attribute 'execute'`
**원인**: SQLAlchemy 2.0에서 문자열 SQL을 직접 실행할 수 없음
**해결책**:
```python
from sqlalchemy import text
# 변경 전: session.execute("PRAGMA foreign_keys=ON")
# 변경 후: session.execute(text("PRAGMA foreign_keys=ON"))
```

## 인증 시스템 문제

### 문제 4: LoginRateLimiter 메서드명 오류
**증상**: `AttributeError: type object 'LoginRateLimiter' has no attribute 'reset_attempts'`
**원인**: 실제 메서드명은 `clear_attempts`인데 `reset_attempts`로 호출
**해결책**: 메서드명을 올바르게 수정
```python
# 변경 전: LoginRateLimiter.reset_attempts(email)
# 변경 후: LoginRateLimiter.clear_attempts(email)
```

## 디버깅 개선 사항

### 문제 5: 로깅 부족
**증상**: 오류 발생 시 원인 파악이 어려움
**해결책**: 주요 지점에 상세한 로그 추가
```python
import logging
logger = logging.getLogger(__name__)

# 사용자 등록/로그인 시도 로그
logger.info(f"사용자 등록 시도: {email}")
logger.info(f"로그인 시도: {email}")
logger.error(f"로그인 오류: {email} - {str(e)}")
```

## 예방 조치

### 1. 설정 검증 스크립트
환경변수와 설정이 올바른지 확인하는 테스트 스크립트 작성:
```python
# test_config.py - 설정 확인용
from app.core.config import settings
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"DB 파일 존재: {os.path.exists(settings.DATABASE_URL.replace('sqlite:///', ''))}")
```

### 2. 절대경로 사용 원칙
- 모든 파일 경로는 절대경로로 설정
- 상대경로가 필요한 경우 자동 변환 로직 구현

### 3. 에러 핸들링 표준화
```python
try:
    # 위험한 작업
    pass
except SpecificException as e:
    logger.error(f"구체적인 오류 설명: {str(e)}")
    raise HTTPException(status_code=500, detail="사용자 친화적 메시지")
```

### 4. API 테스트 자동화
주요 엔드포인트에 대한 curl 테스트 스크립트 작성:
```bash
# 사용자 등록 테스트
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!!", "username": "test"}'

# 로그인 테스트  
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!!"}'
```

## 체크리스트

새로운 기능 개발 시 확인사항:
- [ ] .env 파일이 올바르게 로드되는가?
- [ ] 모든 파일 경로가 절대경로인가?
- [ ] SQLAlchemy 쿼리에 text() 함수를 사용했는가?
- [ ] 에러 핸들링과 로깅이 충분한가?
- [ ] API 테스트가 통과하는가?

---
**작성일**: 2025-05-30  
**최종 업데이트**: 2025-05-30  
**담당자**: ParseNoteLM 개발팀
