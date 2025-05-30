/**
 * 문서 관련 API 서비스
 */
import { apiClient } from './api';

export interface Document {
  id: number;
  name: string;
  content_type: string;
  size: number;
  upload_date: string;
  project_id: number;
  file_path: string;
  processed: boolean;
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
    await apiClient.post(`/api/documents/${documentId}/reprocess`);
  },
};
