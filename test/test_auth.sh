#!/bin/bash
# ParseNoteLM 인증 시스템 테스트 스크립트

echo "🧪 ParseNoteLM 인증 시스템 테스트 시작..."
echo "========================================"

BASE_URL="http://localhost:8000"
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_PASSWORD="Test123!!"
TEST_USERNAME="testuser$(date +%s)"

echo "📧 테스트 사용자: $TEST_EMAIL"
echo ""

# 1. 사용자 등록 테스트
echo "1️⃣ 사용자 등록 테스트..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\", \"username\": \"$TEST_USERNAME\"}")

if echo "$REGISTER_RESPONSE" | grep -q "\"email\""; then
    echo "✅ 사용자 등록 성공"
    echo "📄 응답: $REGISTER_RESPONSE"
else
    echo "❌ 사용자 등록 실패"
    echo "📄 응답: $REGISTER_RESPONSE"
    exit 1
fi

echo ""

# 2. 로그인 테스트
echo "2️⃣ 로그인 테스트..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ 로그인 성공"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
    echo "🔑 토큰 획득: ${ACCESS_TOKEN:0:20}..."
else
    echo "❌ 로그인 실패"
    echo "📄 응답: $LOGIN_RESPONSE"
    exit 1
fi

echo ""

# 3. 프로필 조회 테스트
echo "3️⃣ 프로필 조회 테스트..."
PROFILE_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$PROFILE_RESPONSE" | grep -q "$TEST_EMAIL"; then
    echo "✅ 프로필 조회 성공"
    echo "👤 프로필: $PROFILE_RESPONSE"
else
    echo "❌ 프로필 조회 실패"
    echo "📄 응답: $PROFILE_RESPONSE"
    exit 1
fi

echo ""
echo "🎉 모든 인증 테스트 통과!"
echo "========================================"
