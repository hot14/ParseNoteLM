#!/usr/bin/env python3
"""
요약 API 테스트 스크립트
"""
import requests
import json
import sys
import os

# JWT 토큰 (test@gmail.com)
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3IiwiZW1haWwiOiJ0ZXN0QGdtYWlsLmNvbSIsImV4cCI6MTc1MTQ0Mjk0MX0.tU6uXA6Sp28rLDLYvF_5XfP09ARfXOpLKqoDRnDqc9o"

def test_summary_api():
    """요약 API를 테스트합니다."""
    
    print("=== 프로젝트 13 문서 요약 테스트 ===")
    
    # 첫 번째 문서 (ID: 63) 요약 테스트
    print("\n🧪 첫 번째 문서 (ID: 63) 요약 테스트...")
    try:
        response = requests.post(
            "http://localhost:8000/api/rag/projects/13/summary",
            json={"document_id": 63},
            headers={"Authorization": f"Bearer {JWT_TOKEN}"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 성공! 토큰 수: {result.get('tokens_used', 'N/A')}")
            print(f"요약 길이: {len(result.get('summary', ''))}")
        else:
            print(f"❌ 실패: {response.text}")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
    
    # 두 번째 문서 (ID: 64) 요약 테스트
    print("\n🧪 두 번째 문서 (ID: 64) 요약 테스트...")
    try:
        response = requests.post(
            "http://localhost:8000/api/rag/projects/13/summary",
            json={"document_id": 64},
            headers={"Authorization": f"Bearer {JWT_TOKEN}"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 성공! 토큰 수: {result.get('tokens_used', 'N/A')}")
            print(f"요약 길이: {len(result.get('summary', ''))}")
        else:
            print(f"❌ 실패: {response.text}")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
    
    # 세 번째 문서 (ID: 65) 요약 테스트
    print("\n🧪 세 번째 문서 (ID: 65) 요약 테스트...")
    try:
        response = requests.post(
            "http://localhost:8000/api/rag/projects/13/summary",
            json={"document_id": 65},
            headers={"Authorization": f"Bearer {JWT_TOKEN}"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 성공! 토큰 수: {result.get('tokens_used', 'N/A')}")
            print(f"요약 길이: {len(result.get('summary', ''))}")
        else:
            print(f"❌ 실패: {response.text}")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")

if __name__ == "__main__":
    test_summary_api()