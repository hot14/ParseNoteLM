#!/usr/bin/env python3
"""
PDF 테스트 파일 생성 스크립트
ParseNoteLM의 RAG 시스템을 테스트하기 위한 샘플 PDF 문서를 생성합니다.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import os

def create_test_pdf():
    """테스트용 PDF 파일 생성"""
    filename = "test_rag_document.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    
    # 스타일 설정
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # 중앙 정렬
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor='darkblue'
    )
    
    content = []
    
    # 제목
    content.append(Paragraph("ParseNoteLM RAG 시스템 테스트 문서", title_style))
    content.append(Spacer(1, 20))
    
    # 소개
    content.append(Paragraph("개요", heading_style))
    intro_text = """
    이 문서는 ParseNoteLM의 RAG(Retrieval-Augmented Generation) 시스템을 종합적으로 테스트하기 위해 
    작성된 샘플 PDF 문서입니다. 다양한 주제와 정보를 포함하여 문서 검색 및 질의응답 기능의 
    정확성을 검증합니다.
    """
    content.append(Paragraph(intro_text, styles['Normal']))
    content.append(Spacer(1, 20))
    
    # 기술 스택
    content.append(Paragraph("기술 스택 및 아키텍처", heading_style))
    tech_text = """
    <b>백엔드 기술:</b><br/>
    • FastAPI - 고성능 Python 웹 프레임워크<br/>
    • SQLAlchemy 2.0 - 현대적인 ORM<br/>
    • SQLite (개발) / PostgreSQL (프로덕션)<br/>
    • JWT 기반 인증 시스템<br/><br/>
    
    <b>AI 및 ML 기술:</b><br/>
    • OpenAI GPT-4 - 대화형 AI 모델<br/>
    • OpenAI text-embedding-ada-002 - 임베딩 모델<br/>
    • FAISS - 벡터 유사도 검색<br/>
    • LangChain - AI 애플리케이션 프레임워크<br/><br/>
    
    <b>프론트엔드 기술:</b><br/>
    • React 18 - 사용자 인터페이스 라이브러리<br/>
    • TypeScript - 정적 타입 시스템<br/>
    • Tailwind CSS - 유틸리티 우선 CSS 프레임워크<br/>
    • React Router - 클라이언트 사이드 라우팅<br/>
    """
    content.append(Paragraph(tech_text, styles['Normal']))
    content.append(Spacer(1, 20))
    
    # 주요 기능
    content.append(Paragraph("주요 기능 및 특징", heading_style))
    features_text = """
    <b>1. 문서 관리 시스템</b><br/>
    • 다중 형식 문서 업로드 (PDF, TXT, DOCX)<br/>
    • 자동 문서 분석 및 메타데이터 추출<br/>
    • 프로젝트별 문서 조직화<br/>
    • 문서 버전 관리 및 이력 추적<br/><br/>
    
    <b>2. RAG 시스템</b><br/>
    • 지능형 문서 청킹 (Recursive Character Text Splitter)<br/>
    • 고차원 벡터 임베딩 (1536차원)<br/>
    • 의미론적 유사도 검색<br/>
    • 컨텍스트 인식 답변 생성<br/><br/>
    
    <b>3. 사용자 인터페이스</b><br/>
    • 직관적인 3컬럼 레이아웃<br/>
    • 실시간 채팅 인터페이스<br/>
    • 문서 미리보기 및 하이라이팅<br/>
    • 반응형 웹 디자인<br/>
    """
    content.append(Paragraph(features_text, styles['Normal']))
    content.append(Spacer(1, 20))
    
    # 사용 사례
    content.append(Paragraph("사용 사례 및 활용 분야", heading_style))
    use_cases_text = """
    <b>학술 연구:</b> 논문 검토, 문헌 조사, 연구 보고서 분석<br/>
    <b>비즈니스 분석:</b> 시장 조사 보고서, 재무 문서, 규정 검토<br/>
    <b>법률 서비스:</b> 계약서 분석, 판례 검색, 법령 해석<br/>
    <b>기술 문서:</b> API 문서, 매뉴얼, 기술 사양서 검토<br/>
    <b>교육:</b> 교과서 내용 검색, 학습 자료 질의응답<br/>
    """
    content.append(Paragraph(use_cases_text, styles['Normal']))
    content.append(Spacer(1, 20))
    
    # 성능 및 제한사항
    content.append(Paragraph("성능 특성 및 제한사항", heading_style))
    performance_text = """
    <b>성능 지표:</b><br/>
    • 문서 처리 속도: 1MB당 평균 2-3초<br/>
    • 검색 응답 시간: 평균 500ms 이내<br/>
    • 동시 사용자: 최대 100명 지원<br/>
    • 청크 크기: 512-1024 문자 (최적화)<br/><br/>
    
    <b>현재 제한사항:</b><br/>
    • 최대 파일 크기: 10MB<br/>
    • 프로젝트당 문서 수: 5개<br/>
    • 사용자당 프로젝트 수: 3개<br/>
    • 지원 언어: 한국어, 영어<br/>
    """
    content.append(Paragraph(performance_text, styles['Normal']))
    content.append(Spacer(1, 20))
    
    # 질문 예시
    content.append(Paragraph("테스트 질문 예시", heading_style))
    qa_text = """
    다음은 이 문서를 기반으로 한 질문-답변 예시입니다:<br/><br/>
    
    <b>Q:</b> ParseNoteLM에서 사용하는 주요 AI 모델은 무엇인가요?<br/>
    <b>A:</b> OpenAI GPT-4와 text-embedding-ada-002 임베딩 모델을 사용합니다.<br/><br/>
    
    <b>Q:</b> 문서 처리 성능은 어느 정도인가요?<br/>
    <b>A:</b> 1MB당 평균 2-3초의 처리 시간과 500ms 이내의 검색 응답 시간을 제공합니다.<br/><br/>
    
    <b>Q:</b> 어떤 파일 형식을 지원하나요?<br/>
    <b>A:</b> PDF, TXT, DOCX 형식의 문서를 지원하며, 최대 10MB 크기까지 업로드 가능합니다.<br/>
    """
    content.append(Paragraph(qa_text, styles['Normal']))
    
    # PDF 생성
    doc.build(content)
    
    print(f"✅ PDF 파일이 생성되었습니다: {filename}")
    print(f"   파일 크기: {os.path.getsize(filename):,} bytes")
    
    return filename

if __name__ == "__main__":
    create_test_pdf()
