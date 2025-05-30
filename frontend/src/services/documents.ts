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

export interface UploadDocumentRequest {
  project_id: number;
  file: File;
}

export const documentsApi = {
  // 프로젝트의 문서 목록 조회
  getDocuments: async (projectId: number): Promise<Document[]> => {
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
    console.log('🚀 documentsApi.reprocessDocument 호출');
    console.log('📊 파라미터:', { projectId, documentId });
    console.log('🌐 요청 URL:', `/api/documents/${documentId}/reprocess`);
    
    try {
      const response = await apiClient.post(`/api/documents/${documentId}/reprocess`);
      console.log('✅ API 응답 성공:', response);
      return response.data;
    } catch (error: any) {
      console.error('❌ API 요청 실패:', error);
      console.error('❌ 에러 상세:', {
        status: error?.response?.status,
        data: error?.response?.data,
        message: error?.message || '알 수 없는 오류'
      });
      throw error;
    }
  },
};
