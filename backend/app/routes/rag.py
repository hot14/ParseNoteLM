"""
RAG(검색 증강 생성) 시스템 API 라우터
문서 검색, 질의응답, 컨텍스트 기반 답변 생성을 담당합니다.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.models.chat_history import ChatHistory
from app.schemas.openai import ChatRequest, ChatResponse
from app.services.rag_service import get_rag_service, RAGService
from app.services.openai_service import get_openai_service, OpenAIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.post("/projects/{project_id}/search")
async def search_documents(
    project_id: int,
    query: str,
    max_results: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    프로젝트 내 문서에서 쿼리와 유사한 내용 검색
    """
    try:
        # 프로젝트 권한 확인
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
            Project.is_deleted == False
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프로젝트를 찾을 수 없습니다"
            )
        
        # 문서 검색
        results = await rag_service.search_documents(
            str(project_id), 
            query, 
            max_results
        )
        
        return {
            "query": query,
            "project_id": str(project_id),
            "total_results": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"문서 검색 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 검색 중 오류가 발생했습니다"
        )


@router.post("/projects/{project_id}/chat", response_model=ChatResponse)
async def rag_chat(
    project_id: int,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    RAG 기반 질의응답 - 프로젝트 문서를 기반으로 답변 생성
    """
    try:
        # 프로젝트 권한 확인
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
            Project.is_deleted == False
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프로젝트를 찾을 수 없습니다"
            )
        
        # 1. 관련 문서 검색
        search_results = await rag_service.search_documents(
            str(project_id), 
            request.message, 
            max_results=3  # 상위 3개 문서만 사용
        )
        
        if not search_results:
            return ChatResponse(
                message="관련된 문서를 찾을 수 없어 답변을 생성할 수 없습니다. 프로젝트에 관련 문서를 업로드해주세요.",
                sources=[],
                tokens_used=0
            )
        
        # 2. 컨텍스트 구성
        context_chunks = []
        sources = []
        
        for result in search_results:
            context_chunks.append(f"[문서 {result['document_id']}]\n{result['content']}")
            if result['document_id'] not in sources:
                sources.append(result['document_id'])
        
        context = "\n\n".join(context_chunks)
        
        # 3. RAG 프롬프트 구성
        rag_prompt = f"""당신은 주어진 문서들을 기반으로 질문에 답변하는 AI 어시스턴트입니다.

제공된 문서 내용:
{context}

사용자 질문: {request.message}

위 문서 내용을 바탕으로 정확하고 도움이 되는 답변을 제공해주세요. 
답변할 수 없는 내용이라면 솔직히 모른다고 말해주세요.
답변은 한국어로 해주세요."""
        
        # 4. OpenAI API로 답변 생성
        answer_response = await openai_service.generate_chat_response(rag_prompt)
        
        # 5. 채팅 기록 저장
        from app.models.chat_history import MessageRole, MessageType
        
        # 사용자 메시지 저장
        user_chat = ChatHistory(
            project_id=project_id,
            role=MessageRole.USER,
            message_type=MessageType.QUERY,
            content=request.message,
            total_tokens=0
        )
        db.add(user_chat)
        db.flush()  # ID 생성을 위해 flush
        
        # AI 응답 저장
        assistant_chat = ChatHistory(
            project_id=project_id,
            role=MessageRole.ASSISTANT,
            message_type=MessageType.ANSWER,
            content=answer_response.message,
            model_used="gpt-3.5-turbo",
            total_tokens=answer_response.tokens_used,
            context_documents=sources,
            context_used=len(search_results) > 0,
            parent_message_id=user_chat.id
        )
        db.add(assistant_chat)
        db.commit()
        
        logger.info(f"RAG 답변 생성 완료 - 사용자: {current_user.id}, 프로젝트: {project_id}")
        
        return ChatResponse(
            message=answer_response.message,
            sources=sources,
            tokens_used=answer_response.tokens_used,
            context_used=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"RAG 채팅 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="답변 생성 중 오류가 발생했습니다"
        )


@router.post("/documents/{document_id}/reindex")
async def reindex_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    문서를 RAG 시스템에 재인덱싱
    """
    try:
        # 문서 권한 확인
        document = db.query(Document).join(Project).filter(
            Document.id == document_id,
            Project.user_id == current_user.id,
            Document.is_deleted == False
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="문서를 찾을 수 없습니다"
            )
        
        # RAG 재처리
        success = await rag_service.process_document_for_rag(document_id, db)
        
        if success:
            return {"message": "문서 재인덱싱이 완료되었습니다", "document_id": str(document_id)}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="문서 재인덱싱에 실패했습니다"
            )
        
    except Exception as e:
        logger.error(f"문서 재인덱싱 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 재인덱싱 중 오류가 발생했습니다"
        )


@router.get("/projects/{project_id}/chat/history")
async def get_chat_history(
    project_id: int,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    프로젝트의 채팅 기록 조회
    """
    try:
        # 프로젝트 권한 확인
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
            Project.is_deleted == False
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프로젝트를 찾을 수 없습니다"
            )
        
        # 채팅 기록 조회
        chat_history = db.query(ChatHistory).filter(
            ChatHistory.project_id == project_id,
            ChatHistory.user_id == current_user.id
        ).order_by(ChatHistory.created_at.desc()).limit(limit).all()
        
        return {
            "project_id": str(project_id),
            "total_chats": len(chat_history),
            "chats": [
                {
                    "id": str(chat.id),
                    "message": chat.message,
                    "response": chat.response,
                    "created_at": chat.created_at.isoformat(),
                    "tokens_used": chat.tokens_used,
                    "sources": chat.sources,
                    "rating": chat.rating
                }
                for chat in chat_history
            ]
        }
        
    except Exception as e:
        logger.error(f"채팅 기록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="채팅 기록 조회 중 오류가 발생했습니다"
        )


@router.post("/chat/{chat_id}/feedback")
async def submit_chat_feedback(
    chat_id: UUID,
    rating: int,
    feedback: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    채팅 답변에 대한 피드백 제출
    """
    try:
        if not 1 <= rating <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="평점은 1-5 사이의 값이어야 합니다"
            )
        
        # 채팅 기록 조회
        chat = db.query(ChatHistory).filter(
            ChatHistory.id == chat_id,
            ChatHistory.user_id == current_user.id
        ).first()
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="채팅 기록을 찾을 수 없습니다"
            )
        
        # 피드백 업데이트
        chat.rating = rating
        chat.feedback = feedback
        db.commit()
        
        return {"message": "피드백이 저장되었습니다", "chat_id": str(chat_id)}
        
    except Exception as e:
        logger.error(f"피드백 저장 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="피드백 저장 중 오류가 발생했습니다"
        )
