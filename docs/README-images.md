# ParseNoteLM 이미지 저장 가이드

## 🖼️ 이미지 저장 위치
- **경로**: `/docs/images/`
- **권장 형식**: PNG, JPG
- **파일명 규칙**: `snake_case`

## 📊 필요한 이미지들

### 1. 데이터베이스 스키마 다이어그램
- **파일명**: `database_schema.png`
- **설명**: User, Project, Document, Embedding, ChatHistory 관계도
- **현재 상태**: 텍스트 다이어그램으로 대체됨

### 2. 시스템 아키텍처 다이어그램
- **파일명**: `system_architecture.png`  
- **설명**: 전체 시스템 구조 (백엔드-프론트엔드-AI)

### 3. 사용자 인터페이스 스크린샷
- **파일명**: `ui_dashboard.png`
- **설명**: React 프론트엔드 대시보드

## 📝 이미지 추가 방법

1. 이미지를 `docs/images/` 폴더에 저장
2. README.md에서 다음 형식으로 참조:
   ```markdown
   ![설명](docs/images/파일명.png)
   ```

3. 예시:
   ```markdown
   ![데이터베이스 스키마](docs/images/database_schema.png)
   ```