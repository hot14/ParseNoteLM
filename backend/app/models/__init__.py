"""
모델 패키지 - 모든 데이터베이스 모델을 import
"""

# 기본 모델들
from .user import User, UserRole
from .project import Project
from .project_member import ProjectMember, MemberRole
from .document import Document, DocumentType, ProcessingStatus
from .embedding import Embedding
from .chat_history import ChatHistory, MessageRole, MessageType

# 모든 모델을 외부에서 사용할 수 있도록 export
__all__ = [
    # User 관련
    "User",
    "UserRole",
    
    # Project 관련
    "Project",
    "ProjectMember",
    "MemberRole",
    
    # Document 관련
    "Document",
    "DocumentType", 
    "ProcessingStatus",
    
    # Embedding 관련
    "Embedding",
    
    # ChatHistory 관련
    "ChatHistory",
    "MessageRole",
    "MessageType",
]