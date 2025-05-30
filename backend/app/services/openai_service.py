"""
OpenAI API 통합 서비스
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, NamedTuple
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class OpenAIChatResponse(NamedTuple):
    """OpenAI 채팅 응답 타입"""
    message: str
    tokens_used: int

class OpenAIService:
    """OpenAI API 서비스 클래스"""
    
    def __init__(self):
        """OpenAI 클라이언트 초기화"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다")
        
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY
        )
        
        # 모델 설정
        self.chat_model = "gpt-3.5-turbo"
        self.embedding_model = "text-embedding-3-small"
        
        # 설정값
        self.max_tokens = 1000
        self.temperature = 0.7
        self.max_retries = 3
        self.timeout = 30.0
    
    async def generate_summary(self, text: str, max_length: int = 200) -> str:
        """
        텍스트 요약 생성
        
        Args:
            text: 요약할 텍스트
            max_length: 최대 요약 길이
            
        Returns:
            생성된 요약 텍스트
        """
        try:
            # 텍스트가 너무 긴 경우 잘라내기
            if len(text) > 8000:
                text = text[:8000] + "..."
            
            prompt = f"""
다음 텍스트를 {max_length}자 이내로 간결하고 명확하게 요약해주세요. 
핵심 내용과 주요 포인트를 포함하여 한국어로 작성해주세요.

텍스트:
{text}

요약:
"""
            
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"텍스트 요약 생성 완료. 원본 길이: {len(text)}, 요약 길이: {len(summary)}")
            
            return summary
            
        except Exception as e:
            logger.error(f"텍스트 요약 생성 실패: {str(e)}")
            raise Exception(f"요약 생성 중 오류가 발생했습니다: {str(e)}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        텍스트 임베딩 생성
        
        Args:
            text: 임베딩을 생성할 텍스트
            
        Returns:
            생성된 임베딩 벡터
        """
        try:
            # 텍스트 전처리
            text = text.strip()
            if not text:
                raise ValueError("빈 텍스트로는 임베딩을 생성할 수 없습니다")
            
            # 텍스트 길이 제한 (8192 토큰 제한)
            if len(text) > 6000:
                text = text[:6000]
            
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
                timeout=self.timeout
            )
            
            embedding = response.data[0].embedding
            logger.info(f"임베딩 생성 완료. 텍스트 길이: {len(text)}, 임베딩 차원: {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            raise Exception(f"임베딩 생성 중 오류가 발생했습니다: {str(e)}")
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 목록에 대한 배치 임베딩 생성
        
        Args:
            texts: 임베딩을 생성할 텍스트 목록
            
        Returns:
            생성된 임베딩 벡터 목록
        """
        try:
            if not texts:
                return []
            
            # 텍스트 전처리
            processed_texts = []
            for text in texts:
                text = text.strip()
                if text:
                    if len(text) > 6000:
                        text = text[:6000]
                    processed_texts.append(text)
            
            if not processed_texts:
                return []
            
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=processed_texts,
                timeout=self.timeout * 2  # 배치 처리는 더 긴 타임아웃
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.info(f"배치 임베딩 생성 완료. 텍스트 수: {len(processed_texts)}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"배치 임베딩 생성 실패: {str(e)}")
            raise Exception(f"배치 임베딩 생성 중 오류가 발생했습니다: {str(e)}")
    
    async def analyze_document(self, content: str) -> Dict[str, Any]:
        """
        문서 분석 (요약 + 키워드 추출 + 카테고리 분류)
        
        Args:
            content: 분석할 문서 내용
            
        Returns:
            분석 결과 딕셔너리
        """
        try:
            if len(content) > 8000:
                content = content[:8000] + "..."
            
            prompt = f"""
다음 문서를 분석하여 JSON 형식으로 결과를 제공해주세요:

1. 요약 (200자 이내)
2. 주요 키워드 (5개 이내)
3. 문서 카테고리 (학술, 기술, 일반, 법률, 의료 중 하나)
4. 주제 분야
5. 난이도 (초급, 중급, 고급)

문서 내용:
{content}

응답 형식:
{{
    "summary": "문서 요약",
    "keywords": ["키워드1", "키워드2", "키워드3"],
    "category": "문서 카테고리",
    "topic": "주제 분야",
    "difficulty": "난이도"
}}
"""
            
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3,  # 분석은 더 일관된 결과를 위해 낮은 temperature
                timeout=self.timeout
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # JSON 파싱 시도
            try:
                import json
                # JSON 부분만 추출
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_text = result_text[start_idx:end_idx]
                    result = json.loads(json_text)
                else:
                    raise ValueError("JSON 형식을 찾을 수 없습니다")
            except:
                # JSON 파싱 실패 시 기본값 반환
                result = {
                    "summary": result_text[:200] if result_text else "요약을 생성할 수 없습니다",
                    "keywords": [],
                    "category": "일반",
                    "topic": "기타",
                    "difficulty": "중급"
                }
            
            logger.info(f"문서 분석 완료. 내용 길이: {len(content)}")
            return result
            
        except Exception as e:
            logger.error(f"문서 분석 실패: {str(e)}")
            raise Exception(f"문서 분석 중 오류가 발생했습니다: {str(e)}")
    
    async def generate_answer(self, question: str, context: str) -> str:
        """
        RAG 기반 질의응답
        
        Args:
            question: 사용자 질문
            context: 검색된 컨텍스트
            
        Returns:
            생성된 답변
        """
        try:
            prompt = f"""
주어진 컨텍스트를 바탕으로 사용자의 질문에 정확하고 유용한 답변을 제공해주세요.
컨텍스트에 없는 정보는 추측하지 말고, 컨텍스트 내에서만 답변해주세요.
답변은 한국어로 작성하고, 명확하고 이해하기 쉽게 설명해주세요.

컨텍스트:
{context}

질문: {question}

답변:
"""
            
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7,
                timeout=self.timeout
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"RAG 답변 생성 완료. 질문: {question[:50]}...")
            
            return answer
            
        except Exception as e:
            logger.error(f"RAG 답변 생성 실패: {str(e)}")
            raise Exception(f"답변 생성 중 오류가 발생했습니다: {str(e)}")
    
    async def generate_chat_response(self, prompt: str) -> OpenAIChatResponse:
        """
        채팅 응답 생성 (RAG용)
        
        Args:
            prompt: 사용자 프롬프트 (컨텍스트 포함)
            
        Returns:
            ChatResponse 객체 (message, tokens_used)
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7,
                timeout=self.timeout
            )
            
            message = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.info(f"채팅 응답 생성 완료. 토큰 사용량: {tokens_used}")
            
            return OpenAIChatResponse(
                message=message,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            logger.error(f"채팅 응답 생성 실패: {str(e)}")
            raise Exception(f"채팅 응답 생성 중 오류가 발생했습니다: {str(e)}")

# 전역 OpenAI 서비스 인스턴스
_openai_service: Optional[OpenAIService] = None

def get_openai_service() -> OpenAIService:
    """OpenAI 서비스 인스턴스 반환"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service
