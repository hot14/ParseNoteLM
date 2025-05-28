# ParseNoteLM

NotebookLM과 유사한 AI 기반 문서 분석 및 질의응답 서비스

## 주요 기능

- 📄 다양한 문서 형식 업로드 (PDF, DOCX, TXT)
- 🧠 AI 기반 문서 분석 및 임베딩
- 💬 자연어 질의응답 시스템 (RAG)
- 📝 자동 요약 및 노트 생성
- 🔍 문서 내 검색 및 인용

## 기술 스택

### Backend
- **FastAPI**: 고성능 API 서버
- **PostgreSQL**: 메인 데이터베이스
- **pgvector**: 벡터 임베딩 저장
- **OpenAI API**: LLM 및 임베딩

### Frontend
- **React**: 사용자 인터페이스
- **TypeScript**: 타입 안정성
- **Tailwind CSS**: 스타일링
- **Axios**: API 통신

## 시작하기

### 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 프론트엔드 실행
```bash
cd frontend
npm install
npm start
```

## 프로젝트 구조

```
ParseNoteLM/
├── backend/          # FastAPI 백엔드
├── frontend/         # React 프론트엔드
├── requirements.txt  # Python 의존성
└── README.md        # 프로젝트 설명
```
