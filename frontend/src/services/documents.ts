/**
 * 문서 관련 API 서비스
 */
import { apiClient } from './api';

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  file_size_mb: number;
  file_type: string;
  processing_status: string;
  content_length: number;
  chunk_count: number;
  project_id: number;
  created_at: string;
  updated_at: string;
  processed_at?: string;
  processing_error?: string;
}

// API 응답 타입 정의
interface DocumentsResponse {
  documents: Document[];
  total: number;
  project_can_add_more: boolean;
}

export interface UploadDocumentRequest {
  project_id: number;
  file: File;
}

// 문서 요약 응답 타입 정의
export interface DocumentSummaryResponse {
  summary: string;
  document_titles: string[];
  tokens_used: number;
}

export const documentsApi = {
  // 프로젝트의 문서 목록 조회
  getDocuments: async (projectId: number): Promise<DocumentsResponse> => {
    const response = await apiClient.get(`/api/documents/?project_id=${projectId}`);
    return response.data;
  },

  // 문서 상세 조회
  getDocument: async (projectId: number, documentId: number): Promise<Document> => {
    const response = await apiClient.get(`/api/documents/${documentId}`);
    return response.data;
  },

  // 문서 업로드
  uploadDocument: async (projectId: number, file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', projectId.toString());

    const response = await apiClient.post(
      `/api/documents/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // 문서 삭제
  deleteDocument: async (projectId: number, documentId: number): Promise<void> => {
    await apiClient.delete(`/api/documents/${documentId}`);
  },

  // 문서 다운로드
  downloadDocument: async (projectId: number, documentId: number): Promise<Blob> => {
    const response = await apiClient.get(
      `/api/documents/${documentId}/download`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },

  // 문서 처리 상태 확인
  getProcessingStatus: async (projectId: number, documentId: number): Promise<{
    processed: boolean;
    processing_error?: string;
    chunks_count?: number;
  }> => {
    const response = await apiClient.get(
      `/api/documents/${documentId}/status`
    );
    return response.data;
  },

  // 문서 재처리
  reprocessDocument: async (projectId: number, documentId: number): Promise<void> => {
    try {
      const response = await apiClient.post(`/api/documents/${documentId}/reprocess`);
      return response.data;
    } catch (error: any) {
      console.error('문서 재처리 API 호출 실패:', error);
      console.error('에러 상세:', {
        message: error instanceof Error ? error.message : '알 수 없는 오류',
        response: error && typeof error === 'object' && 'response' in error ? error.response : undefined
      });
      throw error;
    }
  },

  // 문서 요약 생성 (특정 문서 또는 전체 프로젝트)
  generateSummary: async (projectId: number, documentId?: number): Promise<DocumentSummaryResponse> => {
    try {
      const url = documentId 
        ? `/api/rag/projects/${projectId}/summary?document_id=${documentId}`
        : `/api/rag/projects/${projectId}/summary`;
      
      const response = await apiClient.post(url);
      return response.data;
    } catch (error: any) {
      console.error('문서 요약 생성 API 호출 실패:', error);
      console.error('에러 상세:', {
        message: error instanceof Error ? error.message : '알 수 없는 오류',
        response: error && typeof error === 'object' && 'response' in error ? error.response : undefined
      });
      throw error;
    }
  },

  // 마인드맵 데이터 생성
  generateMindmap: async (documentId: string) => {
    try {
      const response = await apiClient.post(`/api/rag/documents/${documentId}/mindmap`);
      return response.data;
    } catch (error) {
      console.error('마인드맵 생성 실패:', error);
      throw error;
    }
  },
};
