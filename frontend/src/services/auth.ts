/**
 * 인증 관련 API 서비스
 */
import apiClient from './api';

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

class AuthService {
  /**
   * 사용자 회원가입
   */
  async register(data: RegisterData): Promise<User> {
    const response = await apiClient.post('/auth/register', data);
    return response.data;
  }

  /**
   * 사용자 로그인
   */
  async login(data: LoginData): Promise<void> {
    const response = await apiClient.post<AuthResponse>('/auth/login', data);
    const { access_token } = response.data;
    
    // 토큰을 로컬 스토리지에 저장
    localStorage.setItem('token', access_token);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    
    return;
  }

  /**
   * 현재 사용자 정보 조회
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/auth/me');
    return response.data;
  }

  /**
   * 로그아웃
   */
  logout(): void {
    localStorage.removeItem('token');
    // Authorization 헤더도 제거
    delete apiClient.defaults.headers.common['Authorization'];
  }

  /**
   * 토큰 존재 여부 확인
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('token');
  }
}

export const authService = new AuthService();