"""
FastAPI TestClient를 사용한 인증 시스템 테스트
"""
import sys
import logging
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from fastapi.testclient import TestClient
from main import app

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_authentication_system():
    """인증 시스템 종합 테스트"""
    client = TestClient(app)
    
    print("🧪 FastAPI TestClient 인증 시스템 테스트")
    print("=" * 50)
    
    # 1. 사용자 등록 테스트
    print("\n1️⃣ 사용자 등록 테스트")
    print("-" * 30)
    
    registration_data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "testpass123!"
    }
    
    response = client.post("/auth/register", json=registration_data)
    print(f"  📝 등록 응답 코드: {response.status_code}")
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"  ✅ 등록 성공: {user_data['email']}")
        print(f"     사용자 ID: {user_data['id']}")
        print(f"     역할: {user_data['role']}")
    else:
        print(f"  ❌ 등록 실패: {response.text}")
        return False
    
    # 2. 중복 등록 테스트
    print("\n2️⃣ 중복 등록 테스트")
    print("-" * 30)
    
    duplicate_response = client.post("/auth/register", json=registration_data)
    if duplicate_response.status_code == 400:
        print("  ✅ 중복 등록 올바르게 거부됨")
    else:
        print(f"  ❌ 중복 등록 처리 오류: {duplicate_response.status_code}")
    
    # 3. 로그인 테스트
    print("\n3️⃣ 로그인 테스트")
    print("-" * 30)
    
    login_data = {
        "email": "testuser@example.com",
        "password": "testpass123!"
    }
    
    login_response = client.post("/auth/login", json=login_data)
    print(f"  📝 로그인 응답 코드: {login_response.status_code}")
    
    if login_response.status_code == 200:
        token_data = login_response.json()
        access_token = token_data["access_token"]
        print(f"  ✅ 로그인 성공")
        print(f"     토큰 타입: {token_data['token_type']}")
        print(f"     토큰 길이: {len(access_token)} 문자")
    else:
        print(f"  ❌ 로그인 실패: {login_response.text}")
        return False
    
    # 4. 잘못된 비밀번호 테스트
    print("\n4️⃣ 잘못된 비밀번호 테스트")
    print("-" * 30)
    
    wrong_login_data = {
        "email": "testuser@example.com",
        "password": "wrongpassword"
    }
    
    wrong_response = client.post("/auth/login", json=wrong_login_data)
    if wrong_response.status_code == 401:
        print("  ✅ 잘못된 비밀번호 올바르게 거부됨")
    else:
        print(f"  ❌ 잘못된 비밀번호 처리 오류: {wrong_response.status_code}")
    
    # 5. 토큰 검증 테스트 (/me 엔드포인트)
    print("\n5️⃣ 토큰 검증 테스트")
    print("-" * 30)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = client.get("/auth/me", headers=headers)
    
    if me_response.status_code == 200:
        user_info = me_response.json()
        print(f"  ✅ 토큰 검증 성공")
        print(f"     사용자: {user_info['email']}")
        print(f"     ID: {user_info['id']}")
    else:
        print(f"  ❌ 토큰 검증 실패: {me_response.text}")
        return False
    
    # 6. 잘못된 토큰 테스트
    print("\n6️⃣ 잘못된 토큰 테스트")
    print("-" * 30)
    
    wrong_headers = {"Authorization": "Bearer invalid_token"}
    invalid_response = client.get("/auth/me", headers=wrong_headers)
    
    if invalid_response.status_code == 401:
        print("  ✅ 잘못된 토큰 올바르게 거부됨")
    else:
        print(f"  ❌ 잘못된 토큰 처리 오류: {invalid_response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 모든 인증 테스트 통과!")
    return True

if __name__ == "__main__":
    try:
        success = test_authentication_system()
        if success:
            print("\n✨ 인증 시스템이 올바르게 작동하고 있습니다!")
            sys.exit(0)
        else:
            print("\n❌ 일부 테스트가 실패했습니다.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
