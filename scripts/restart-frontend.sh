#!/bin/bash

# ParseNoteLM 프론트엔드 서버 재시작 스크립트
# 포트 3000에서 실행 중인 프로세스를 종료하고 새로 시작

echo "🔄 ParseNoteLM 프론트엔드 서버를 재시작합니다..."

# 현재 디렉토리를 프로젝트 루트로 변경
cd "$(dirname "$0")/.."

# 포트 3000에서 실행 중인 프로세스 찾기
FRONTEND_PID=$(lsof -ti:3000)

if [ ! -z "$FRONTEND_PID" ]; then
    echo "📍 포트 3000에서 실행 중인 프로세스 발견: PID $FRONTEND_PID"
    echo "⏹️  기존 프론트엔드 프로세스를 종료합니다..."
    kill -15 $FRONTEND_PID
    sleep 2
    
    # 강제 종료가 필요한 경우
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🚫 강제 종료합니다..."
        kill -9 $FRONTEND_PID
        sleep 1
    fi
    echo "✅ 기존 프로세스가 종료되었습니다."
else
    echo "📍 포트 3000에서 실행 중인 프로세스가 없습니다."
fi

# 프론트엔드 디렉토리로 이동
cd frontend

# node_modules 확인
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules가 없습니다. npm install을 먼저 실행해주세요."
    exit 1
fi

echo "🚀 프론트엔드 서버를 시작합니다..."
echo "📋 서버 URL: http://localhost:3000"
echo "⏹️  종료하려면 Ctrl+C를 누르세요"
echo ""

# 프론트엔드 서버 시작
npm start
