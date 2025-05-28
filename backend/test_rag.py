#!/usr/bin/env python3
"""
RAG 시스템 테스트 스크립트
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.services.rag_service import DocumentChunker, VectorRetriever, RAGService

async def test_document_chunker():
    """문서 청킹 테스트"""
    print("=== 문서 청킹 테스트 ===")
    
    chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
    
    sample_text = """
    이것은 RAG 시스템 테스트용 문서입니다.
    
    FastAPI는 현대적이고 빠른 (고성능) 웹 프레임워크입니다.
    Python 3.6+를 기반으로 하며 표준 Python 타입 힌트를 사용합니다.
    
    주요 특징:
    - 빠름: NodeJS 및 Go와 동등한 매우 높은 성능
    - 빠른 코딩: 개발 속도를 200% ~ 300% 증가
    - 적은 버그: 사람(개발자)에 의한 오류 약 40% 감소
    - 직관적: 훌륭한 편집기 지원, 자동완성
    - 쉬움: 쉽게 사용하고 배울 수 있도록 설계
    - 짧음: 코드 중복 최소화
    - 견고함: 자동 대화형 문서와 함께 프로덕션 준비된 코드 작성
    - 표준 기반: OpenAPI 및 JSON Schema와 같은 API에 대한 개방형 표준 기반
    
    랭체인(LangChain)은 대화형 AI 애플리케이션을 개발하기 위한 프레임워크입니다.
    """
    
    chunks = chunker.chunk_document(sample_text, "test_doc_1")
    
    print(f"총 {len(chunks)}개 청크 생성:")
    for i, chunk in enumerate(chunks):
        print(f"\n청크 {i+1}:")
        print(f"길이: {len(chunk['text'])} 문자")
        print(f"내용: {chunk['text'][:100]}...")

async def test_vector_retriever():
    """벡터 검색 테스트"""
    print("\n=== 벡터 검색 테스트 ===")
    
    # OpenAI API 키 확인
    from app.config import settings
    if not settings.OPENAI_API_KEY:
        print("⚠️ OpenAI API 키가 설정되지 않음. 로컬 모델만 사용합니다.")
    
    retriever = VectorRetriever()
    
    # 테스트 문서 청크들
    sample_chunks = [
        {
            "text": "FastAPI는 현대적이고 빠른 웹 프레임워크입니다. Python 3.6+를 기반으로 합니다.",
            "document_id": "doc1",
            "chunk_index": 0,
            "metadata": {"length": 50, "position": 0}
        },
        {
            "text": "랭체인은 대화형 AI 애플리케이션 개발을 위한 프레임워크입니다.",
            "document_id": "doc1", 
            "chunk_index": 1,
            "metadata": {"length": 35, "position": 1}
        },
        {
            "text": "벡터 데이터베이스는 유사도 검색을 위해 사용됩니다.",
            "document_id": "doc2",
            "chunk_index": 0,
            "metadata": {"length": 30, "position": 0}
        }
    ]
    
    try:
        # 벡터 스토어에 문서 추가
        success = await retriever.add_documents_to_store("test_project", sample_chunks)
        if success:
            print("✅ 벡터 스토어 생성 성공")
            
            # 유사도 검색 테스트
            test_queries = [
                "FastAPI에 대해 알려주세요",
                "AI 개발 프레임워크",
                "벡터 검색이란"
            ]
            
            for query in test_queries:
                print(f"\n쿼리: '{query}'")
                results = await retriever.search_similar_documents(
                    "test_project", query, k=2
                )
                
                for i, result in enumerate(results):
                    print(f"  결과 {i+1}: 유사도 {result['similarity']:.3f}")
                    print(f"  내용: {result['content'][:60]}...")
        else:
            print("❌ 벡터 스토어 생성 실패")
            
    except Exception as e:
        print(f"❌ 벡터 검색 테스트 실패: {e}")

async def test_rag_service():
    """RAG 서비스 통합 테스트"""
    print("\n=== RAG 서비스 통합 테스트 ===")
    
    rag_service = RAGService()
    
    # 문서 검색 테스트
    try:
        results = await rag_service.search_documents(
            "test_project", 
            "FastAPI 프레임워크",
            max_results=2
        )
        
        print(f"검색 결과: {len(results)}개")
        for result in results:
            print(f"- 유사도: {result.get('similarity', 0):.3f}")
            print(f"  내용: {result['content'][:50]}...")
            
    except Exception as e:
        print(f"❌ RAG 서비스 테스트 실패: {e}")

async def main():
    """메인 테스트 실행"""
    print("🚀 RAG 시스템 테스트 시작\n")
    
    await test_document_chunker()
    await test_vector_retriever()
    await test_rag_service()
    
    print("\n✅ 모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())
