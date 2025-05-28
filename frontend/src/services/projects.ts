/**
 * 프로젝트 관련 API 서비스
 */
import { apiClient } from './api';

export interface Project {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  owner_id: number;
}

export interface CreateProjectRequest {
  title: string;
  description?: string;
}

export interface UpdateProjectRequest {
  title?: string;
  description?: string;
}

export const projectsApi = {
  // 프로젝트 목록 조회
  getProjects: async (): Promise<Project[]> => {
    const response = await apiClient.get('/api/projects/');
    return response.data;
  },

  // 프로젝트 상세 조회
  getProject: async (projectId: number): Promise<Project> => {
    const response = await apiClient.get(`/api/projects/${projectId}`);
    return response.data;
  },

  // 프로젝트 생성
  createProject: async (data: CreateProjectRequest): Promise<Project> => {
    const response = await apiClient.post('/api/projects/', data);
    return response.data;
  },

  // 프로젝트 수정
  updateProject: async (projectId: number, data: UpdateProjectRequest): Promise<Project> => {
    const response = await apiClient.put(`/api/projects/${projectId}`, data);
    return response.data;
  },

  // 프로젝트 삭제
  deleteProject: async (projectId: number): Promise<void> => {
    await apiClient.delete(`/api/projects/${projectId}`);
  },

  // 프로젝트 통계
  getProjectStats: async (projectId: number): Promise<{
    document_count: number;
    member_count: number;
    total_size: number;
    last_activity: string;
  }> => {
    const response = await apiClient.get(`/api/projects/${projectId}/stats`);
    return response.data;
  },
};
