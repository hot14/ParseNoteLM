/**
 * 인증 페이지 (로그인/회원가입)
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoginForm } from '../components/auth/LoginForm';
import { RegisterForm } from '../components/auth/RegisterForm';

export const AuthPage: React.FC = () => {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const navigate = useNavigate();

  const handleAuthSuccess = () => {
    navigate('/dashboard');
  };

  const switchToRegister = () => {
    setIsLoginMode(false);
  };

  const switchToLogin = () => {
    setIsLoginMode(true);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            ParseNoteLM
          </h1>
          <p className="text-lg text-gray-600">
            AI 기반 문서 분석 및 질의응답 서비스
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        {isLoginMode ? (
          <LoginForm 
            onSuccess={handleAuthSuccess}
            onSwitchToRegister={switchToRegister}
          />
        ) : (
          <RegisterForm 
            onSuccess={handleAuthSuccess}
            onSwitchToLogin={switchToLogin}
          />
        )}
      </div>
    </div>
  );
};