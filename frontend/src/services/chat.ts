/**
 * 채팅 및 질의응답 관련 API 서비스
 */
import { apiClient } from './api';

export interface ChatMessage {
  id?: number;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  project_id: number;
}

export interface ChatSession {
  id: number;
  project_id: number;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface AskQuestionRequest {
  question: string;
  project_id: number;
  session_id?: number;
}

export interface AskQuestionResponse {
  answer: string;
  sources: Array<{
    document_name: string;
    page_number?: number;
    relevance_score: number;
    content_snippet: string;
  }>;
  session_id: number;
}

export const chatApi = {
  // 질문하기
  askQuestion: async (data: AskQuestionRequest): Promise<AskQuestionResponse> => {
    const response = await apiClient.post('/api/chat/ask', data);
    return response.data;
  },

  // 채팅 세션 목록 조회
  getChatSessions: async (projectId: number): Promise<ChatSession[]> => {
    const response = await apiClient.get(`/api/projects/${projectId}/chat/sessions`);
    return response.data;
  },

  // 채팅 세션 생성
  createChatSession: async (projectId: number): Promise<ChatSession> => {
    const response = await apiClient.post(`/api/projects/${projectId}/chat/sessions`);
    return response.data;
  },

  // 채팅 메시지 조회
  getChatMessages: async (projectId: number, sessionId: number): Promise<ChatMessage[]> => {
    const response = await apiClient.get(
      `/api/projects/${projectId}/chat/sessions/${sessionId}/messages`
    );
    return response.data;
  },

  // 채팅 세션 삭제
  deleteChatSession: async (projectId: number, sessionId: number): Promise<void> => {
    await apiClient.delete(`/api/projects/${projectId}/chat/sessions/${sessionId}`);
  },
};
