import React from 'react';

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            ParseNoteLM에 오신 것을 환영합니다!
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            AI 기반 문서 분석 및 질의응답 서비스
          </p>
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-md mx-auto">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              🚀 개발 환경 준비 완료
            </h2>
            <p className="text-gray-600">
              프론트엔드와 백엔드 환경이 성공적으로 설정되었습니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;