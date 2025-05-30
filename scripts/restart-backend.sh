#!/bin/bash

# ParseNoteLM 백엔드 서버 재시작 스크립트
# 포트 8000에서 실행 중인 프로세스를 종료하고 새로 시작

echo "🔄 ParseNoteLM 백엔드 서버를 재시작합니다..."

# 현재 디렉토리를 프로젝트 루트로 변경
cd "$(dirname "$0")/.."

# 포트 8000 에서 실행 중인 프로세스 찾기
BACKEND_PID=$(lsof -ti:8000)

if [ ! -z "$BACKEND_PID" ]; then
    echo "📍 포트 8000에서 실행 중인 프로세스 발견: PID $BACKEND_PID"
    echo "⏹️  기존 백엔드 프로세스를 종료합니다..."
    kill -15 $BACKEND_PID
    sleep 2
    
    # 강제 종료가 필요한 경우
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🚫 강제 종료합니다..."
        kill -9 $BACKEND_PID
        sleep 1
    fi
    echo "✅ 기존 프로세스가 종료되었습니다."
else
    echo "📍 포트 8000에서 실행 중인 프로세스가 없습니다."
fi

# 백엔드 디렉토리로 이동
cd backend

# 가상환경 활성화 확인
if [ ! -d "venv" ]; then
    echo "❌ 가상환경이 없습니다. venv를 먼저 생성해주세요."
    exit 1
fi

echo "🚀 백엔드 서버를 시작합니다..."
echo "📋 서버 URL: http://localhost:8000"
echo "📋 API 문서: http://localhost:8000/docs"
echo "⏹️  종료하려면 Ctrl+C를 누르세요"
echo ""

# 가상환경 활성화하고 서버 시작
source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000
