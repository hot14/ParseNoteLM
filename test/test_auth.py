#!/usr/bin/env python3
"""
인증 시스템 테스트
사용자 등록, 로그인, JWT 토큰 검증을 포함한 종합 테스트
"""
import os
import sys
import json
import requests
import time
import logging
from pathlib import Path
from typing import Dict, Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

def setup_test_logging():
    """테스트용 로깅 설정"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'auth_test.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class AuthTestClient:
    """인증 테스트용 HTTP 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def register_user(self, email: str, username: str, password: str) -> Dict:
        """사용자 등록 테스트"""
        url = f"{self.base_url}/auth/register"
        data = {
            "email": email,
            "username": username,
            "password": password
        }
        
        self.logger.info(f"🆕 사용자 등록 테스트: {email}")
        
        try:
            response = self.session.post(url, json=data, timeout=10)
            result = {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "success": response.status_code == 200
            }
            
            if result["success"]:
                self.logger.info(f"✅ 등록 성공: {email}")
            else:
                self.logger.warning(f"❌ 등록 실패: {email} - {result['data']}")
                
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"💥 등록 요청 오류: {e}")
            return {"status_code": 0, "data": {"detail": str(e)}, "success": False}
    
    def login_user(self, email: str, password: str) -> Dict:
        """사용자 로그인 테스트"""
        url = f"{self.base_url}/auth/login"
        data = {
            "email": email,
            "password": password
        }
        
        self.logger.info(f"🔐 로그인 테스트: {email}")
        
        try:
            response = self.session.post(url, json=data, timeout=10)
            result = {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "success": response.status_code == 200
            }
            
            if result["success"]:
                token = result["data"].get("access_token")
                if token:
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    self.logger.info(f"✅ 로그인 성공: {email}")
                else:
                    self.logger.warning(f"⚠️ 토큰 없음: {email}")
                    result["success"] = False
            else:
                self.logger.warning(f"❌ 로그인 실패: {email} - {result['data']}")
                
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"💥 로그인 요청 오류: {e}")
            return {"status_code": 0, "data": {"detail": str(e)}, "success": False}
    
    def verify_token(self) -> Dict:
        """JWT 토큰 검증 테스트"""
        url = f"{self.base_url}/auth/me"
        
        self.logger.info("🎫 토큰 검증 테스트")
        
        try:
            response = self.session.get(url, timeout=10)
            result = {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "success": response.status_code == 200
            }
            
            if result["success"]:
                user_info = result["data"]
                self.logger.info(f"✅ 토큰 검증 성공: {user_info.get('email', 'unknown')}")
            else:
                self.logger.warning(f"❌ 토큰 검증 실패: {result['data']}")
                
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"💥 토큰 검증 요청 오류: {e}")
            return {"status_code": 0, "data": {"detail": str(e)}, "success": False}

def check_server_health(base_url: str = "http://localhost:8000") -> bool:
    """서버 상태 확인"""
    logger = logging.getLogger("server_health")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ 서버 상태 정상")
            return True
        else:
            logger.warning(f"⚠️ 서버 응답 이상: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 서버 연결 실패: {e}")
        return False

def test_user_registration():
    """사용자 등록 테스트"""
    logger = logging.getLogger("registration_test")
    client = AuthTestClient()
    
    # 테스트 사용자 데이터
    test_users = [
        {
            "email": "test1@example.com",
            "username": "testuser1",
            "password": "testpass123!"
        },
        {
            "email": "test2@example.com", 
            "username": "testuser2",
            "password": "testpass456!"
        }
    ]
    
    results = []
    
    for user in test_users:
        result = client.register_user(
            user["email"], 
            user["username"], 
            user["password"]
        )
        results.append({
            "email": user["email"],
            "success": result["success"],
            "status_code": result["status_code"],
            "message": result["data"].get("detail", "OK")
        })
    
    # 중복 등록 테스트
    logger.info("🔄 중복 등록 테스트")
    duplicate_result = client.register_user(
        test_users[0]["email"],
        test_users[0]["username"], 
        test_users[0]["password"]
    )
    
    results.append({
        "email": f"{test_users[0]['email']} (중복)",
        "success": not duplicate_result["success"],  # 실패해야 성공
        "status_code": duplicate_result["status_code"],
        "message": duplicate_result["data"].get("detail", "OK")
    })
    
    return results

def test_user_login():
    """사용자 로그인 테스트"""
    logger = logging.getLogger("login_test")
    client = AuthTestClient()
    
    # 올바른 로그인 테스트
    login_result = client.login_user("test1@example.com", "testpass123!")
    
    # 잘못된 비밀번호 테스트
    wrong_password_result = client.login_user("test1@example.com", "wrongpassword")
    
    # 존재하지 않는 사용자 테스트
    nonexistent_result = client.login_user("nonexistent@example.com", "anypassword")
    
    results = [
        {
            "test": "올바른 로그인",
            "success": login_result["success"],
            "status_code": login_result["status_code"],
            "message": login_result["data"].get("detail", "OK")
        },
        {
            "test": "잘못된 비밀번호",
            "success": not wrong_password_result["success"],  # 실패해야 성공
            "status_code": wrong_password_result["status_code"],
            "message": wrong_password_result["data"].get("detail", "OK")
        },
        {
            "test": "존재하지 않는 사용자",
            "success": not nonexistent_result["success"],  # 실패해야 성공
            "status_code": nonexistent_result["status_code"],
            "message": nonexistent_result["data"].get("detail", "OK")
        }
    ]
    
    # 성공한 로그인이 있다면 토큰 검증
    if login_result["success"]:
        token_result = client.verify_token()
        results.append({
            "test": "JWT 토큰 검증",
            "success": token_result["success"],
            "status_code": token_result["status_code"],
            "message": token_result["data"].get("detail", "OK")
        })
    
    return results

def main():
    """메인 테스트 실행"""
    logger = setup_test_logging()
    
    print("🧪 ParseNoteLM 인증 시스템 테스트")
    print("=" * 50)
    
    # 서버 상태 확인
    if not check_server_health():
        print("❌ 서버가 실행되지 않았거나 응답하지 않습니다.")
        print("   다음 명령으로 서버를 시작하세요:")
        print("   cd backend && uvicorn main:app --reload")
        return 1
    
    # 1. 사용자 등록 테스트
    print("\n1️⃣ 사용자 등록 테스트")
    print("-" * 30)
    
    registration_results = test_user_registration()
    registration_success = sum(1 for r in registration_results if r["success"])
    
    for result in registration_results:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {result['email']}: {result['message']}")
    
    print(f"  📊 등록 테스트: {registration_success}/{len(registration_results)} 성공")
    
    # 2. 로그인 테스트
    print("\n2️⃣ 로그인 및 토큰 테스트")
    print("-" * 30)
    
    login_results = test_user_login()
    login_success = sum(1 for r in login_results if r["success"])
    
    for result in login_results:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {result['test']}: {result['message']}")
    
    print(f"  📊 로그인 테스트: {login_success}/{len(login_results)} 성공")
    
    # 전체 결과
    total_tests = len(registration_results) + len(login_results)
    total_success = registration_success + login_success
    
    print("\n" + "=" * 50)
    print("📊 최종 결과")
    print("=" * 50)
    print(f"전체 테스트: {total_success}/{total_tests} 성공")
    print(f"성공률: {total_success/total_tests*100:.1f}%")
    
    if total_success == total_tests:
        print("🎉 모든 인증 테스트 통과!")
        return 0
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
