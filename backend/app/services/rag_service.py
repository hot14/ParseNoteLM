"""
RAG(검색 증강 생성) 시스템 구현
문서 검색, 청킹, 벡터화, 유사도 검색을 담당합니다.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

import numpy as np
from sqlalchemy.orm import Session
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

from app.core.database import get_db
from app.models.document import Document as DocumentModel
from app.models.embedding import Embedding
from app.config import settings

logger = logging.getLogger(__name__)


class DocumentChunker:
    """문서를 의미적 단위로 분할하는 클래스"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def chunk_document(self, content: str, document_id: str) -> List[Dict[str, Any]]:
        """문서를 청크로 분할"""
        try:
            chunks = self.text_splitter.split_text(content)
            
            chunk_data = []
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) > 20:  # 너무 짧은 청크 제외
                    chunk_data.append({
                        "text": chunk.strip(),
                        "document_id": document_id,
                        "chunk_index": i,
                        "metadata": {
                            "length": len(chunk),
                            "position": i,
                            "total_chunks": len(chunks)
                        }
                    })
            
            logger.info(f"문서 {document_id}: {len(chunks)}개 청크 생성 → {len(chunk_data)}개 유효 청크")
            return chunk_data
            
        except Exception as e:
            logger.error(f"문서 청킹 실패 {document_id}: {e}")
            return []


class VectorRetriever:
    """벡터 기반 문서 검색 클래스"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model="text-embedding-ada-002"
        )
        self.vector_stores: Dict[str, FAISS] = {}  # 프로젝트별 벡터 스토어
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """텍스트 리스트를 임베딩으로 변환"""
        try:
            # OpenAI API 우선 사용
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"OpenAI 임베딩 실패: {e}")
            return []
    
    async def add_documents_to_store(
        self, 
        project_id: str, 
        chunk_data: List[Dict[str, Any]]
    ) -> bool:
        """문서 청크들을 벡터 스토어에 추가"""
        try:
            if not chunk_data:
                return False
            
            # 텍스트 추출
            texts = [chunk["text"] for chunk in chunk_data]
            
            # 임베딩 생성
            embeddings = await self.create_embeddings(texts)
            
            # LangChain Document 객체 생성
            documents = []
            for chunk, embedding in zip(chunk_data, embeddings):
                doc = Document(
                    page_content=chunk["text"],
                    metadata={
                        "document_id": chunk["document_id"],
                        "chunk_index": chunk["chunk_index"],
                        **chunk["metadata"]
                    }
                )
                documents.append(doc)
            
            # FAISS 벡터 스토어 생성/업데이트
            if project_id in self.vector_stores:
                # 기존 스토어에 추가
                self.vector_stores[project_id].add_documents(documents)
            else:
                # 새 스토어 생성
                self.vector_stores[project_id] = FAISS.from_documents(
                    documents, 
                    self.embeddings
                )
            
            logger.info(f"프로젝트 {project_id}: {len(documents)}개 문서 청크 벡터화 완료")
            return True
            
        except Exception as e:
            logger.error(f"벡터 스토어 추가 실패: {e}")
            return False
    
    async def search_similar_documents(
        self, 
        project_id: str, 
        query: str, 
        k: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """유사한 문서 청크 검색"""
        try:
            if project_id not in self.vector_stores:
                logger.warning(f"프로젝트 {project_id}의 벡터 스토어가 없습니다")
                return []
            
            vector_store = self.vector_stores[project_id]
            
            # 유사도 검색 수행
            docs_with_scores = vector_store.similarity_search_with_score(
                query, k=k
            )
            
            # 점수 필터링 및 결과 포맷팅
            results = []
            for doc, score in docs_with_scores:
                # FAISS는 거리를 반환하므로 유사도로 변환
                similarity = 1.0 / (1.0 + score)
                
                if similarity >= score_threshold:
                    results.append({
                        "content": doc.page_content,
                        "similarity": similarity,
                        "metadata": doc.metadata,
                        "document_id": doc.metadata.get("document_id"),
                        "chunk_index": doc.metadata.get("chunk_index")
                    })
            
            # 유사도 기준 정렬
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            logger.info(f"쿼리 '{query}': {len(results)}개 유사 문서 발견")
            return results
            
        except Exception as e:
            logger.error(f"문서 검색 실패: {e}")
            return []
    
    def save_vector_store(self, project_id: str, path: str) -> bool:
        """벡터 스토어를 파일로 저장"""
        try:
            if project_id in self.vector_stores:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                self.vector_stores[project_id].save_local(path)
                logger.info(f"벡터 스토어 저장 완료: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"벡터 스토어 저장 실패: {e}")
            return False
    
    def load_vector_store(self, project_id: str, path: str) -> bool:
        """파일에서 벡터 스토어 로드"""
        try:
            if os.path.exists(path):
                self.vector_stores[project_id] = FAISS.load_local(
                    path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"벡터 스토어 로드 완료: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"벡터 스토어 로드 실패: {e}")
            return False


class RAGService:
    """RAG 시스템의 메인 서비스 클래스"""
    
    def __init__(self):
        self.chunker = DocumentChunker()
        self.retriever = VectorRetriever()
        from app.core.config import settings
        self.vector_store_base_path = settings.get_absolute_vector_store_dir
    
    async def process_document_for_rag(
        self, 
        document_id: int, 
        db: Session
    ) -> bool:
        """문서를 RAG 시스템에 추가 처리"""
        try:
            # 문서 조회
            document = db.query(DocumentModel).filter(
                DocumentModel.id == document_id
            ).first()
            
            if not document or not document.content:
                logger.warning(f"문서를 찾을 수 없거나 내용이 없음: {document_id}")
                return False
            
            # 문서 청킹
            chunks = self.chunker.chunk_document(
                document.content, 
                str(document_id)
            )
            
            if not chunks:
                logger.warning(f"문서 청킹 실패: {document_id}")
                return False
            
            # 벡터 스토어에 추가
            success = await self.retriever.add_documents_to_store(
                str(document.project_id), 
                chunks
            )
            
            if success:
                # 벡터 스토어 저장
                store_path = os.path.join(
                    self.vector_store_base_path, 
                    str(document.project_id)
                )
                self.retriever.save_vector_store(
                    str(document.project_id), 
                    store_path
                )
                
                # 임베딩 메타데이터 DB에 저장
                for chunk in chunks:
                    # 청크에 대한 임베딩 벡터 생성
                    chunk_embedding = await self.retriever.embeddings.aembed_query(chunk["text"])
                    
                    # 디버깅을 위한 로그 추가
                    chunk_text = chunk["text"]
                    chunk_size_val = len(chunk_text)
                    logger.info(f"청크 처리 중: chunk_size={chunk_size_val}, text_length={len(chunk_text)}")
                    
                    embedding = Embedding(
                        document_id=document_id,
                        chunk_text=chunk_text,
                        chunk_size=chunk_size_val,  # 청크 크기 (문자 수) 추가
                        chunk_index=chunk["chunk_index"],
                        embedding_vector=chunk_embedding,  # 임베딩 벡터 추가
                        embedding_model="text-embedding-ada-002",
                        vector_dimension=len(chunk_embedding) if chunk_embedding else 1536,
                        tokens=len(chunk_text.split()),  # 대략적인 토큰 수
                        document_metadata=chunk["metadata"]  # metadata_ → document_metadata로 수정
                    )
                    db.add(embedding)
                
                db.commit()
                
                # 문서의 chunk_count 업데이트
                document.chunk_count = len(chunks)
                db.commit()
                
                logger.info(f"문서 RAG 처리 완료: {document_id}, chunks: {len(chunks)}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"RAG 문서 처리 실패 {document_id}: {e}")
            db.rollback()
            return False
    
    async def load_project_vector_store(self, project_id: str) -> bool:
        """프로젝트의 벡터 스토어 로드"""
        store_path = os.path.join(
            self.vector_store_base_path, 
            project_id
        )
        return self.retriever.load_vector_store(project_id, store_path)
    
    async def search_documents(
        self, 
        project_id: str, 
        query: str, 
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """프로젝트 내 문서 검색"""
        # 벡터 스토어가 메모리에 없으면 로드
        if str(project_id) not in self.retriever.vector_stores:
            await self.load_project_vector_store(str(project_id))
        
        # 유사 문서 검색
        return await self.retriever.search_similar_documents(
            str(project_id), 
            query, 
            k=max_results
        )


# 전역 RAG 서비스 인스턴스
rag_service = RAGService()


async def get_rag_service() -> RAGService:
    """RAG 서비스 의존성 주입"""
    return rag_service
