"""
문서 처리 서비스
"""
import logging
import os
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.embedding import Embedding
from app.services.openai_service import get_openai_service
from app.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """문서 처리 서비스"""
    
    def __init__(self):
        self.openai_service = get_openai_service()
    
    async def process_document(self, document: Document, db: Session) -> bool:
        """
        문서 처리 (분석 + 임베딩 생성)
        
        Args:
            document: 처리할 문서
            db: 데이터베이스 세션
            
        Returns:
            처리 성공 여부
        """
        try:
            logger.info(f"문서 처리 시작: {document.id} - {document.filename}")
            
            # 문서 상태를 PROCESSING으로 변경
            document.status = "PROCESSING"
            db.commit()
            
            # 문서 내용 읽기
            content = await self._read_document_content(document)
            if not content:
                logger.error(f"문서 내용을 읽을 수 없습니다: {document.id}")
                document.status = "FAILED"
                db.commit()
                return False
            
            # 문서 분석
            analysis_result = await self.openai_service.analyze_document(content)
            
            # 문서 메타데이터 업데이트
            document.summary = analysis_result.get("summary", "")
            document.keywords = analysis_result.get("keywords", [])
            document.category = analysis_result.get("category", "일반")
            document.topic = analysis_result.get("topic", "기타")
            document.difficulty = analysis_result.get("difficulty", "중급")
            
            # 텍스트 청킹 및 임베딩 생성
            logger.info(f"📝 텍스트 청킹 시작: document_id={document.id}")
            chunks = self._split_text_into_chunks(content)
            logger.info(f"📊 청킹 완료: {len(chunks)}개 청크 생성")
            
            logger.info(f"🎯 임베딩 생성 시작: document_id={document.id}")
            embeddings_created = await self._create_embeddings(document, chunks, db)
            logger.info(f"🎯 임베딩 생성 완료: success={embeddings_created}")
            
            if embeddings_created:
                document.status = "COMPLETED"
                logger.info(f"✅ 문서 처리 완료: {document.id}")
            else:
                document.status = "FAILED"
                logger.error(f"❌ 임베딩 생성 실패: {document.id}")
            
            logger.info(f"💾 최종 상태 커밋 시작: document_id={document.id}, status={document.status}")
            db.commit()
            logger.info(f"💾 최종 상태 커밋 완료: document_id={document.id}")
            
            return embeddings_created
            
        except Exception as e:
            logger.error(f"문서 처리 실패: {document.id} - {str(e)}")
            document.status = "FAILED"
            db.commit()
            return False
    
    async def _read_document_content(self, document: Document) -> Optional[str]:
        """문서 내용 읽기"""
        try:
            file_path = document.file_path
            if not os.path.exists(file_path):
                logger.error(f"파일이 존재하지 않습니다: {file_path}")
                return None
            
            # 이미 추출된 내용이 있으면 반환
            if document.content:
                return document.content
            
            # 파일 확장자에 따른 내용 추출
            if document.file_type.lower() == "txt":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content
            
            elif document.file_type.lower() == "pdf":
                # PDF 처리 (PyPDF2 사용)
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        content = ""
                        for page in pdf_reader.pages:
                            content += page.extract_text() + "\n"
                    return content
                except Exception as e:
                    logger.error(f"PDF 처리 실패: {file_path} - {str(e)}")
                    return None
            
            else:
                logger.error(f"지원하지 않는 파일 형식: {document.file_type}")
                return None
                
        except Exception as e:
            logger.error(f"문서 내용 읽기 실패: {document.file_path} - {str(e)}")
            return None
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 분할할 텍스트
            chunk_size: 청크 크기
            overlap: 중복 크기
            
        Returns:
            분할된 텍스트 청크 목록
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 문장 경계에서 분할하려고 시도
            if end < len(text):
                # 마지막 문장 부호를 찾기
                last_period = text.rfind('.', start, end)
                last_exclamation = text.rfind('!', start, end)
                last_question = text.rfind('?', start, end)
                
                sentence_end = max(last_period, last_exclamation, last_question)
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 다음 시작점 설정 (중복 고려)
            start = max(start + 1, end - overlap)
        
        logger.info(f"텍스트를 {len(chunks)}개 청크로 분할")
        return chunks
    
    async def _create_embeddings(self, document: Document, chunks: List[str], db: Session) -> bool:
        """
        청크들에 대한 임베딩 생성 및 저장
        
        Args:
            document: 문서 객체
            chunks: 텍스트 청크 목록
            db: 데이터베이스 세션
            
        Returns:
            임베딩 생성 성공 여부
        """
        try:
            logger.info(f"🎯 임베딩 생성 시작: document_id={document.id}, chunks={len(chunks)}")
            
            if not chunks:
                logger.warning(f"⚠️ 생성할 청크가 없습니다: {document.id}")
                return True
            
            # 기존 임베딩 삭제 (reprocess에서 이미 했지만 안전을 위해)
            existing_count = db.query(Embedding).filter(Embedding.document_id == document.id).count()
            if existing_count > 0:
                logger.info(f"🗑️ 기존 임베딩 추가 삭제: {existing_count}개")
                db.query(Embedding).filter(Embedding.document_id == document.id).delete()
            
            # 배치로 임베딩 생성
            logger.info(f"🚀 OpenAI 임베딩 생성 호출: document_id={document.id}")
            embeddings = await self.openai_service.generate_embeddings_batch(chunks)
            logger.info(f"📦 OpenAI 임베딩 응답 받음: {len(embeddings)}개")
            
            if len(embeddings) != len(chunks):
                logger.error(f"❌ 임베딩 수와 청크 수가 일치하지 않습니다: {len(embeddings)} vs {len(chunks)}")
                return False
            
            # 임베딩 저장
            logger.info(f"💾 임베딩 객체 생성 및 DB 저장 시작: document_id={document.id}")
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedding_obj = Embedding(
                    document_id=document.id,
                    chunk_text=chunk,
                    chunk_index=i,
                    chunk_size=len(chunk),  # chunk_size 설정
                    embedding_vector=embedding,
                    tokens=len(chunk.split()) if chunk else 0  # 토큰 수 설정
                )
                db.add(embedding_obj)
                if i % 10 == 0:  # 10개마다 로그
                    logger.debug(f"📝 임베딩 객체 추가: {i+1}/{len(chunks)}")
            
            logger.info(f"💾 임베딩 커밋 시작: document_id={document.id}")
            db.commit()
            logger.info(f"✅ 임베딩 생성 완료: {document.id} - {len(embeddings)}개")
            return True
            
        except Exception as e:
            logger.error(f"💥 임베딩 생성 실패: {document.id} - {str(e)}", exc_info=True)
            try:
                db.rollback()
                logger.info(f"🔄 DB 롤백 완료: document_id={document.id}")
            except Exception as rollback_error:
                logger.error(f"💥 DB 롤백 실패: {rollback_error}")
            return False
    
    async def reprocess_document(self, document: Document, db: Session) -> bool:
        """
        문서 재처리
        
        Args:
            document: 재처리할 문서
            db: 데이터베이스 세션
            
        Returns:
            재처리 성공 여부
        """
        try:
            logger.info(f"🔄 문서 재처리 시작: document_id={document.id}, filename={document.filename}")
            
            # 기존 임베딩 개수 확인
            existing_embeddings = db.query(Embedding).filter(Embedding.document_id == document.id).count()
            logger.info(f"🗑️ 삭제할 기존 임베딩 개수: {existing_embeddings}")
            
            # 기존 임베딩 삭제
            deleted_count = db.query(Embedding).filter(Embedding.document_id == document.id).delete()
            logger.info(f"✂️ 임베딩 삭제 완료: {deleted_count}개")
            
            db.commit()
            logger.info(f"💾 임베딩 삭제 커밋 완료")
            
            # 문서 다시 처리
            logger.info(f"🚀 문서 다시 처리 시작: document_id={document.id}")
            result = await self.process_document(document, db)
            logger.info(f"✅ 문서 재처리 완료: document_id={document.id}, success={result}")
            
            return result
            
        except Exception as e:
            logger.error(f"💥 문서 재처리 중 예외 발생: document_id={document.id}, error={str(e)}", exc_info=True)
            return False

# 전역 문서 처리 서비스 인스턴스
_document_service: Optional[DocumentProcessingService] = None

def get_document_service() -> DocumentProcessingService:
    """문서 처리 서비스 인스턴스 반환"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentProcessingService()
    return _document_service
