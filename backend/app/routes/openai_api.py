"""
OpenAI API 라우터
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.openai_service import get_openai_service, OpenAIService
from app.schemas.openai import (
    DocumentAnalysisRequest, DocumentAnalysisResponse,
    EmbeddingRequest, EmbeddingResponse,
    BatchEmbeddingRequest, BatchEmbeddingResponse,
    SummaryRequest, SummaryResponse,
    QuestionAnswerRequest, QuestionAnswerResponse,
    APIErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/openai", tags=["OpenAI"])

@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    request: DocumentAnalysisRequest,
    current_user: User = Depends(get_current_user),
    openai_service: OpenAIService = Depends(get_openai_service),
    db: Session = Depends(get_db)
):
    """
    문서 분석 API
    - 문서 내용을 분석하여 요약, 키워드, 카테고리 등을 추출
    """
    try:
        logger.info(f"사용자 {current_user.email}의 문서 분석 요청")
        
        # OpenAI 서비스를 통해 문서 분석
        analysis_result = await openai_service.analyze_document(request.content)
        
        logger.info(f"문서 분석 완료: {current_user.email}")
        return DocumentAnalysisResponse(**analysis_result)
        
    except Exception as e:
        logger.error(f"문서 분석 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/summary", response_model=SummaryResponse)
async def generate_summary(
    request: SummaryRequest,
    current_user: User = Depends(get_current_user),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    텍스트 요약 생성 API
    - 주어진 텍스트의 요약을 생성
    """
    try:
        logger.info(f"사용자 {current_user.email}의 텍스트 요약 요청")
        
        # OpenAI 서비스를 통해 요약 생성
        summary = await openai_service.generate_summary(
            text=request.text,
            max_length=request.max_length
        )
        
        logger.info(f"텍스트 요약 완료: {current_user.email}")
        return SummaryResponse(
            summary=summary,
            original_length=len(request.text),
            summary_length=len(summary)
        )
        
    except Exception as e:
        logger.error(f"텍스트 요약 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"텍스트 요약 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/embedding", response_model=EmbeddingResponse)
async def generate_embedding(
    request: EmbeddingRequest,
    current_user: User = Depends(get_current_user),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    임베딩 생성 API
    - 주어진 텍스트의 임베딩 벡터를 생성
    """
    try:
        logger.info(f"사용자 {current_user.email}의 임베딩 생성 요청")
        
        # OpenAI 서비스를 통해 임베딩 생성
        embedding = await openai_service.generate_embedding(request.text)
        
        logger.info(f"임베딩 생성 완료: {current_user.email}")
        return EmbeddingResponse(
            embedding=embedding,
            dimension=len(embedding)
        )
        
    except Exception as e:
        logger.error(f"임베딩 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"임베딩 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/embeddings/batch", response_model=BatchEmbeddingResponse)
async def generate_batch_embeddings(
    request: BatchEmbeddingRequest,
    current_user: User = Depends(get_current_user),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    배치 임베딩 생성 API
    - 여러 텍스트의 임베딩 벡터를 한 번에 생성
    """
    try:
        logger.info(f"사용자 {current_user.email}의 배치 임베딩 생성 요청 (텍스트 수: {len(request.texts)})")
        
        # OpenAI 서비스를 통해 배치 임베딩 생성
        embeddings = await openai_service.generate_embeddings_batch(request.texts)
        
        logger.info(f"배치 임베딩 생성 완료: {current_user.email}")
        return BatchEmbeddingResponse(
            embeddings=embeddings,
            count=len(embeddings)
        )
        
    except Exception as e:
        logger.error(f"배치 임베딩 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"배치 임베딩 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/answer", response_model=QuestionAnswerResponse)
async def generate_answer(
    request: QuestionAnswerRequest,
    current_user: User = Depends(get_current_user),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    RAG 기반 질의응답 API
    - 주어진 컨텍스트를 바탕으로 질문에 대한 답변을 생성
    """
    try:
        logger.info(f"사용자 {current_user.email}의 질의응답 요청")
        
        # OpenAI 서비스를 통해 답변 생성
        answer = await openai_service.generate_answer(
            question=request.question,
            context=request.context
        )
        
        logger.info(f"질의응답 완료: {current_user.email}")
        return QuestionAnswerResponse(
            answer=answer,
            context_used=bool(request.context.strip())
        )
        
    except Exception as e:
        logger.error(f"질의응답 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"질의응답 중 오류가 발생했습니다: {str(e)}"
        )
