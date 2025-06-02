"""
RAG(검색 증강 생성) 시스템 API 라우터
문서 검색, 질의응답, 컨텍스트 기반 답변 생성을 담당합니다.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

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


@router.post("/projects/{project_id}/summary")
async def generate_project_summary(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
    openai_service: OpenAIService = Depends(get_openai_service),
    document_id: Optional[int] = Query(None, description="특정 문서 ID (선택사항)")
):
    """
    프로젝트 문서 요약 생성 - 특정 문서 또는 전체 프로젝트 요약
    """
    try:
        logger.info(f"요약 요청 받음: project_id={project_id}, document_id={document_id}, user={current_user.email}")
        
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
        
        # 문서 내용 수집
        content_chunks = []
        document_titles = []
        
        if document_id:
            logger.info(f" 특정 문서 요약 요청: document_id={document_id}")
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.project_id == project_id
            ).first()
            
            if not document:
                logger.error(f" 문서를 찾을 수 없음: document_id={document_id}, project_id={project_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="문서를 찾을 수 없습니다"
                )
            
            logger.info(f" 문서 발견: {document.original_filename}")
            
            # 문서의 청크 검색 (일반적인 내용 검색)
            logger.info(f" 문서 청크 검색 시작")
            search_results = await rag_service.search_documents(
                str(project_id), 
                "주요 내용 핵심 개념 요약", 
                max_results=10,
                score_threshold=0.1  # 낮은 임계값으로 더 많은 내용 포함
            )
            
            logger.info(f" 전체 검색 결과: {len(search_results)}개")
            
            # 검색 결과의 document_id들을 확인
            for i, r in enumerate(search_results):
                logger.info(f"  검색결과[{i}]: document_id={r.get('document_id')} (타입: {type(r.get('document_id'))})")
            
            # 특정 문서의 청크만 필터링 - 안전한 타입 변환
            doc_chunks = []
            for r in search_results:
                try:
                    # document_id가 문자열이나 정수일 수 있으므로 안전하게 변환
                    r_doc_id = int(r['document_id']) if isinstance(r['document_id'], str) else r['document_id']
                    logger.debug(f"  비교중: {r_doc_id} == {document_id} ? {r_doc_id == document_id}")
                    if r_doc_id == document_id:
                        doc_chunks.append(r)
                        logger.info(f"  ✅ 문서 {document_id} 청크 발견: {r['content'][:100]}...")
                except (ValueError, TypeError) as e:
                    logger.warning(f"document_id 변환 실패: {r.get('document_id')} -> {e}")
                    continue
                    
            logger.info(f" 문서 {document_id} 청크 필터링 결과: {len(doc_chunks)}개")
            content_chunks = [chunk['content'] for chunk in doc_chunks[:8]]  # 최대 8개 청크
            document_titles = [document.original_filename]
            
            if not content_chunks:
                logger.error(f" 문서 {document_id}의 콘텐츠 청크가 비어있음")
                logger.error(f" 실제 존재하는 문서들: {[int(r['document_id']) for r in search_results]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"문서 ID {document_id}에 대한 요약할 내용이 없습니다. 존재하는 문서 ID: {list(set([int(r['document_id']) for r in search_results]))}"
                )
        
        else:
            # 전체 프로젝트 요약
            documents = db.query(Document).filter(
                Document.project_id == project_id,
                Document.processing_status == "completed"
            ).all()
            
            if not documents:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="처리 완료된 문서가 없습니다"
                )
            
            # 각 문서에서 핵심 내용 추출
            for doc in documents:
                search_results = await rag_service.search_documents(
                    str(project_id),
                    f"문서 {doc.original_filename} 주요 내용",
                    max_results=5,
                    score_threshold=0.1
                )
                
                doc_chunks = [r for r in search_results if r['document_id'] == str(doc.id)]
                content_chunks.extend([chunk['content'] for chunk in doc_chunks[:3]])  # 문서당 최대 3개 청크
                document_titles.append(doc.original_filename)
        
        if not content_chunks:
            return {
                "summary": "요약할 문서 내용을 찾을 수 없습니다. 문서가 올바르게 처리되었는지 확인해주세요.",
                "document_titles": document_titles,
                "tokens_used": 0
            }
        
        # 요약 생성을 위한 프롬프트 구성
        combined_content = "\n\n".join(content_chunks[:10])  # 최대 10개 청크로 제한
        
        if document_id:
            summary_prompt = f"""다음은 '{document_titles[0]}' 문서의 주요 내용입니다. 이 문서의 핵심 개념과 주요 내용을 상세하고 구조적으로 요약해주세요.

문서 내용:
{combined_content}

요약 시 다음 사항을 포함해주세요:
1. 문서의 주제와 목적
2. 핵심 개념들과 그 정의
3. 주요 내용과 논리적 구조
4. 중요한 결론이나 시사점

답변은 한국어로 작성하고, 마크다운 형식으로 구조화해서 제시해주세요."""
        else:
            summary_prompt = f"""다음은 프로젝트의 여러 문서들({', '.join(document_titles)})에서 추출한 주요 내용입니다. 전체 프로젝트의 핵심 개념과 주요 내용을 종합적으로 요약해주세요.

문서 내용:
{combined_content}

요약 시 다음 사항을 포함해주세요:
1. 프로젝트 전체의 주제와 목적
2. 문서들에서 공통으로 다루는 핵심 개념들
3. 각 문서의 주요 기여점
4. 전체적인 결론과 시사점

답변은 한국어로 작성하고, 마크다운 형식으로 구조화해서 제시해주세요."""
        
        # OpenAI API로 요약 생성
        summary_response = await openai_service.generate_chat_completion(
            messages=[
                {"role": "system", "content": "당신은 문서를 분석하고 핵심 내용을 정확하게 요약하는 전문가입니다."},
                {"role": "user", "content": summary_prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        summary = summary_response.get("content", "요약 생성에 실패했습니다.")
        tokens_used = summary_response.get("usage", {}).get("total_tokens", 0)
        
        return {
            "summary": summary,
            "document_titles": document_titles,
            "tokens_used": tokens_used
        }
        
    except Exception as e:
        logger.error(f"문서 요약 생성 실패: {e}")
        logger.error(f"에러 타입: {type(e)}")
        logger.error(f"에러 상세: {str(e)}")
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 요약 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/documents/{document_id}/reindex")
async def reindex_document(
    document_id: int,
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


@router.post("/documents/{document_id}/mindmap")
async def generate_mindmap(
    document_id: str,
    db: Session = Depends(get_db)
):
    """문서의 마인드맵 데이터를 생성합니다"""
    try:
        # 문서 조회
        result = db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
        
        # 문서 내용이 있는지 확인
        if not document.content:
            raise HTTPException(status_code=400, detail="문서 내용이 없습니다")
        
        # OpenAI를 사용하여 마인드맵 구조 생성
        openai_service = OpenAIService()
        
        # 문서 내용이 너무 길면 앞부분만 사용 (토큰 제한 고려)
        content_preview = document.content[:4000] if len(document.content) > 4000 else document.content
        
        mindmap_prompt = f"""
다음 문서 내용을 분석하여 마인드맵 구조로 변환해주세요.
문서명: {document.original_filename}
문서 내용:
{content_preview}

응답은 반드시 다음 JSON 형식으로만 답변해주세요:
{{
  "mainTopic": "문서의 핵심 주제 (간결하게)",
  "branches": [
    {{
      "title": "주요 카테고리 1",
      "color": "purple",
      "items": ["세부항목1", "세부항목2", "세부항목3", "세부항목4"]
    }},
    {{
      "title": "주요 카테고리 2", 
      "color": "orange",
      "items": ["세부항목1", "세부항목2", "세부항목3", "세부항목4"]
    }},
    {{
      "title": "주요 카테고리 3",
      "color": "blue", 
      "items": ["세부항목1", "세부항목2", "세부항목3"]
    }}
  ]
}}

규칙:
- mainTopic은 15자 이내로 간결하게
- branches는 2-4개 생성
- 각 branch의 items는 3-5개 생성  
- items는 각각 25자 이내로 간결하게
- color는 "purple", "orange", "blue" 중 하나만 사용
- JSON 형식 외의 다른 텍스트는 포함하지 마세요
"""
        
        # OpenAI API 호출
        response = await openai_service.generate_chat_response(mindmap_prompt)
        
        # JSON 파싱 시도
        try:
            import json
            mindmap_data = json.loads(response.message)
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 기본 구조 반환
            mindmap_data = {
                "mainTopic": document.original_filename or "문서 분석",
                "branches": [
                    {
                        "title": "주요 내용",
                        "color": "purple",
                        "items": ["문서 분석 중", "내용 추출 중", "구조화 진행 중"]
                    },
                    {
                        "title": "세부 정보",
                        "color": "orange", 
                        "items": ["추가 분석 필요", "내용 정리 중"]
                    }
                ]
            }
        
        return {
            "success": True,
            "document_id": document_id,
            "mindmap": mindmap_data,
            "tokens_used": response.tokens_used
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"마인드맵 생성 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"마인드맵 생성 중 오류가 발생했습니다: {str(e)}")
