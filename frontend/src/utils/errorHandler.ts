/**
 * 에러 처리 유틸리티
 */

import { AxiosError } from 'axios';

export interface ApiError {
  message: string;
  error_code?: string;
  details?: Record<string, any>;
}

export interface ErrorResponse {
  detail: ApiError | string;
}

/**
 * API 에러를 사용자 친화적 메시지로 변환
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const response = error.response?.data as ErrorResponse;
    
    if (response?.detail) {
      if (typeof response.detail === 'string') {
        return response.detail;
      }
      
      if (typeof response.detail === 'object' && response.detail.message) {
        return response.detail.message;
      }
    }
    
    // HTTP 상태 코드에 따른 기본 메시지
    switch (error.response?.status) {
      case 400:
        return '잘못된 요청입니다. 입력값을 확인해주세요.';
      case 401:
        return '인증이 필요합니다. 다시 로그인해주세요.';
      case 403:
        return '권한이 없습니다.';
      case 404:
        return '요청한 리소스를 찾을 수 없습니다.';
      case 500:
        return '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
      default:
        return '알 수 없는 오류가 발생했습니다.';
    }
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return '알 수 없는 오류가 발생했습니다.';
}

/**
 * 에러 코드에 따른 특별한 처리
 */
export function handleSpecialErrors(error: unknown): boolean {
  if (error instanceof AxiosError) {
    const response = error.response?.data as ErrorResponse;
    
    if (typeof response?.detail === 'object' && response.detail.error_code) {
      switch (response.detail.error_code) {
        case 'AUTHENTICATION_ERROR':
          // 인증 오류 시 로그인 페이지로 리다이렉트
          localStorage.removeItem('token');
          window.location.href = '/login';
          return true;
          
        case 'FILE_UPLOAD_ERROR':
          // 파일 업로드 오류는 이미 처리됨
          return false;
          
        default:
          return false;
      }
    }
  }
  
  return false;
}

/**
 * 에러 로깅
 */
export function logError(error: unknown, context?: string): void {
  const errorMessage = getErrorMessage(error);
  const logContext = context ? `[${context}] ` : '';
  
  console.error(`${logContext}${errorMessage}`, error);
  
  // 프로덕션에서는 에러 리포팅 서비스로 전송
  if (process.env.NODE_ENV === 'production') {
    // TODO: 에러 리포팅 서비스 연동 (예: Sentry)
  }
}
