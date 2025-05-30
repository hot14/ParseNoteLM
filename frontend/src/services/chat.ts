/**
 * 채팅 및 질의응답 관련 API 서비스
 */
import { apiClient } from './api';

export interface ChatMessage {
  id?: number;
  message: string;
  response: string;
  timestamp: string;
  sources?: string[];
}

export interface ChatSession {
  id: number;
  name: string;
  created_at: string;
  messages_count: number;
}

export interface AskQuestionRequest {
  question: string;
  project_id: number;
  document_id?: number;
  session_id?: number;
}

export interface AskQuestionResponse {
  message: string;
  sources: string[];
  tokens_used: number;
  session_id: number;
}

export const chatApi = {
  // 질문하기
  askQuestion: async (data: AskQuestionRequest): Promise<AskQuestionResponse> => {
    const response = await apiClient.post(`/api/rag/projects/${data.project_id}/chat`, {
      message: data.question
    });
    return {
      message: response.data.message,
      sources: response.data.sources || [],
      tokens_used: response.data.tokens_used || 0,
      session_id: response.data.session_id || Date.now()
    };
  },

  // 채팅 히스토리 조회
  getChatSessions: async (projectId: number): Promise<ChatMessage[]> => {
    const response = await apiClient.get(`/api/rag/projects/${projectId}/chat/history`);
    if (response.data.chats) {
      return response.data.chats.map((chat: any) => ({
        id: chat.id,
        message: chat.message,
        response: chat.response,
        timestamp: chat.created_at,
        sources: chat.sources || []
      }));
    }
    return [];
  },

  // 채팅 세션 생성 (더미 함수)
  createChatSession: async (projectId: number): Promise<ChatSession> => {
    return {
      id: Date.now(),
      name: "새 채팅",
      created_at: new Date().toISOString(),
      messages_count: 0
    };
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
