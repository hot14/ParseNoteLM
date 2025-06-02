#!/usr/bin/env python3
"""
JWT 토큰 생성 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.auth import create_access_token
from datetime import timedelta

def generate_token():
    """test@gmail.com 사용자의 JWT 토큰을 생성합니다."""
    
    # test@gmail.com (user_id: 7)의 토큰 생성
    access_token = create_access_token(
        data={"sub": "7", "email": "test@gmail.com"},
        expires_delta=timedelta(days=30)  # 30일 유효
    )
    
    print("=== JWT 토큰 생성 ===")
    print(f"사용자: test@gmail.com (ID: 7)")
    print(f"토큰: {access_token}")
    
    return access_token

if __name__ == "__main__":
    token = generate_token()