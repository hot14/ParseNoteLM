#!/usr/bin/env python3
"""
OpenAI API 통합 테스트 스크립트
"""
import asyncio
import httpx
import json
import os
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 테스트 설정
BASE_URL = "http://localhost:8002"
TEST_EMAIL = "openai_test@example.com"
TEST_PASSWORD = "testpassword123"

class OpenAIIntegrationTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.project_id = None
        self.client = httpx.AsyncClient()
    
    async def register_and_login(self):
        """사용자 등록 및 로그인"""
        print("🔐 사용자 등록 및 로그인 중...")
        
        # 사용자 등록
        register_data = {
            "email": TEST_EMAIL,
            "username": "testuser",
            "password": TEST_PASSWORD
        }
        
        try:
            register_response = await self.client.post(
                f"{self.base_url}/auth/register",
                json=register_data
            )
            print(f"등록 응답 상태코드: {register_response.status_code}")
            print(f"등록 응답 내용: {register_response.text}")
            
            if register_response.status_code in [200, 201]:
                print("✅ 사용자 등록 성공")
            elif register_response.status_code == 400:
                print("ℹ️ 사용자가 이미 존재하거나 검증 오류")
            else:
                print(f"❌ 등록 실패: {register_response.text}")
                logger.error(f"사용자 등록 실패: {register_response.text}")
        except Exception as e:
            print(f"❌ 등록 중 오류: {e}")
            logger.error(f"사용자 등록 중 오류: {e}")
        
        # 로그인 (OAuth2 token 엔드포인트 사용)
        login_data = {
            "username": TEST_EMAIL,  # FastAPI OAuth2에서는 username 필드 사용
            "password": TEST_PASSWORD
        }
        
        try:
            login_response = await self.client.post(
                f"{self.base_url}/auth/token",
                data=login_data,  # form data로 전송
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if login_response.status_code == 200:
                login_result = login_response.json()
                self.token = login_result.get("access_token")
                print("✅ 로그인 성공")
                return True
            else:
                print(f"❌ 로그인 실패: {login_response.text}")
                logger.error(f"로그인 실패: {login_response.text}")
                return False
        except Exception as e:
            print(f"❌ 로그인 중 오류: {e}")
            logger.error(f"로그인 중 오류: {e}")
            return False
    
    async def create_test_project(self):
        """테스트 프로젝트 생성"""
        print("📁 테스트 프로젝트 생성 중...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        project_data = {
            "title": "OpenAI 테스트 프로젝트",
            "description": "OpenAI API 통합 테스트를 위한 프로젝트"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/projects/",
                json=project_data,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                project = response.json()
                self.project_id = project["id"]
                print(f"✅ 프로젝트 생성 성공: ID {self.project_id}")
                return True
            else:
                print(f"❌ 프로젝트 생성 실패: {response.text}")
                logger.error(f"프로젝트 생성 실패: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 프로젝트 생성 중 오류: {e}")
            logger.error(f"프로젝트 생성 중 오류: {e}")
            return False
    
    async def test_document_analysis(self):
        """문서 분석 API 테스트"""
        print("📄 문서 분석 API 테스트 중...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        test_content = """
        인공지능(AI)은 현대 기술의 핵심 분야 중 하나입니다. 
        머신러닝, 딥러닝, 자연어처리 등의 기술을 통해 
        인간의 지능을 모방하고 때로는 능가하는 성능을 보여줍니다.
        
        특히 대화형 AI는 사용자와의 자연스러운 상호작용을 가능하게 하며,
        교육, 의료, 고객 서비스 등 다양한 분야에서 활용되고 있습니다.
        """
        
        analysis_data = {"content": test_content.strip()}
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/openai/analyze",
                json=analysis_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 문서 분석 성공:")
                print(f"   📝 요약: {result.get('summary', 'N/A')}")
                print(f"   🔑 키워드: {', '.join(result.get('keywords', []))}")
                print(f"   📂 카테고리: {result.get('category', 'N/A')}")
                print(f"   📚 주제: {result.get('topic', 'N/A')}")
                print(f"   📊 난이도: {result.get('difficulty', 'N/A')}")
                return True
            else:
                print(f"❌ 문서 분석 실패: {response.text}")
                logger.error(f"문서 분석 실패: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 문서 분석 중 오류: {e}")
            logger.error(f"문서 분석 중 오류: {e}")
            return False
    
    async def test_summary_generation(self):
        """텍스트 요약 API 테스트"""
        print("📝 텍스트 요약 API 테스트 중...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        test_text = """
        FastAPI는 Python으로 API를 빠르게 개발할 수 있는 현대적인 웹 프레임워크입니다.
        이 프레임워크는 타입 힌트를 기반으로 한 자동 문서화, 빠른 성능, 그리고 직관적인 사용법을 제공합니다.
        또한 비동기 프로그래밍을 지원하여 높은 성능의 웹 애플리케이션을 구축할 수 있습니다.
        개발자들은 FastAPI를 사용하여 RESTful API와 GraphQL 엔드포인트를 쉽게 만들 수 있으며,
        자동으로 생성되는 OpenAPI 문서를 통해 API를 테스트하고 문서화할 수 있습니다.
        """
        
        summary_data = {
            "text": test_text.strip(),
            "max_length": 100
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/openai/summary",
                json=summary_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 텍스트 요약 성공:")
                print(f"   📝 요약: {result.get('summary', 'N/A')}")
                print(f"   📏 원본 길이: {result.get('original_length', 0)}자")
                print(f"   📏 요약 길이: {result.get('summary_length', 0)}자")
                return True
            else:
                print(f"❌ 텍스트 요약 실패: {response.text}")
                logger.error(f"텍스트 요약 실패: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 텍스트 요약 중 오류: {e}")
            logger.error(f"텍스트 요약 중 오류: {e}")
            return False
    
    async def test_embedding_generation(self):
        """임베딩 생성 API 테스트"""
        print("🔢 임베딩 생성 API 테스트 중...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        embedding_data = {
            "text": "인공지능과 머신러닝에 대한 연구"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/openai/embedding",
                json=embedding_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get('embedding', [])
                dimension = result.get('dimension', 0)
                print("✅ 임베딩 생성 성공:")
                print(f"   📐 차원: {dimension}")
                print(f"   🔢 첫 5개 값: {embedding[:5] if embedding else 'N/A'}")
                return True
            else:
                print(f"❌ 임베딩 생성 실패: {response.text}")
                logger.error(f"임베딩 생성 실패: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 임베딩 생성 중 오류: {e}")
            logger.error(f"임베딩 생성 중 오류: {e}")
            return False
    
    async def test_qa_generation(self):
        """질의응답 API 테스트"""
        print("❓ 질의응답 API 테스트 중...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        qa_data = {
            "question": "FastAPI의 주요 특징은 무엇인가요?",
            "context": """
            FastAPI는 Python으로 API를 빠르게 개발할 수 있는 현대적인 웹 프레임워크입니다.
            이 프레임워크는 타입 힌트를 기반으로 한 자동 문서화, 빠른 성능, 그리고 직관적인 사용법을 제공합니다.
            또한 비동기 프로그래밍을 지원하여 높은 성능의 웹 애플리케이션을 구축할 수 있습니다.
            """
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/openai/answer",
                json=qa_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 질의응답 성공:")
                print(f"   ❓ 질문: {qa_data['question']}")
                print(f"   💬 답변: {result.get('answer', 'N/A')}")
                print(f"   📄 컨텍스트 사용: {result.get('context_used', False)}")
                return True
            else:
                print(f"❌ 질의응답 실패: {response.text}")
                logger.error(f"질의응답 실패: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 질의응답 중 오류: {e}")
            logger.error(f"질의응답 중 오류: {e}")
            return False
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 OpenAI API 통합 테스트 시작\n")
        
        success_count = 0
        total_tests = 5
        
        # 인증 테스트
        if await self.register_and_login():
            success_count += 1
        
        if self.token:
            # 프로젝트 생성 테스트
            if await self.create_test_project():
                success_count += 1
            
            # OpenAI API 테스트들
            if await self.test_document_analysis():
                success_count += 1
            
            if await self.test_summary_generation():
                success_count += 1
            
            if await self.test_embedding_generation():
                success_count += 1
            
            if await self.test_qa_generation():
                success_count += 1
                total_tests += 1  # 추가 테스트
        
        await self.client.aclose()
        
        print(f"\n📊 테스트 결과: {success_count}/{total_tests} 성공")
        if success_count == total_tests:
            print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        else:
            print("⚠️ 일부 테스트가 실패했습니다.")
        
        return success_count == total_tests

async def main():
    """메인 함수"""
    test = OpenAIIntegrationTest()
    success = await test.run_all_tests()
    return success

if __name__ == "__main__":
    asyncio.run(main())
