import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectsApi, Project } from '../services/projects';
import { documentsApi, Document } from '../services/documents';
import { chatApi, ChatMessage, AskQuestionRequest } from '../services/chat';

// 프로젝트 상세 페이지에서 사용할 확장된 프로젝트 타입
interface ProjectDetail extends Project {
  title?: string;
  user_id?: number;
  document_count?: number;
}

// 파일 업로드 응답 타입은 Document 타입을 직접 사용

export const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [documentSummary, setDocumentSummary] = useState<string>('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isAsking, setIsAsking] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const loadProject = useCallback(async () => {
    if (!projectId) return;
    
    try {
      const projectData = await projectsApi.getProject(Number(projectId));
      setProject(projectData as ProjectDetail);
    } catch (error) {
      console.error('프로젝트 로드 실패:', error);
    }
  }, [projectId]);

  const loadDocuments = useCallback(async () => {
    if (!projectId) return;
    
    try {
      const documentsData = await documentsApi.getDocuments(Number(projectId));
      setDocuments(documentsData);
    } catch (error) {
      console.error('문서 로드 실패:', error);
      const mockDocument: Document = {
        id: 1,
        name: "sample.pdf",
        content_type: "application/pdf",
        size: 1024000,
        upload_date: new Date().toISOString(),
        project_id: Number(projectId),
        file_path: "/uploads/sample.pdf",
        processed: true
      };
      setDocuments([mockDocument]);
    }
  }, [projectId]);

  useEffect(() => {
    loadProject();
    loadDocuments();
    setIsLoading(false);
  }, [loadProject, loadDocuments]);

  const handleSendMessage = async () => {
    if (!currentQuestion.trim() || !projectId || isAsking) return;
    
    const userMessage: ChatMessage = {
      id: Date.now(),
      content: currentQuestion,
      sender: 'user',
      timestamp: new Date().toISOString(),
      project_id: Number(projectId)
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setCurrentQuestion('');
    setIsAsking(true);
    
    try {
      const request: AskQuestionRequest = {
        question: currentQuestion,
        project_id: Number(projectId)
      };
      
      const response = await chatApi.askQuestion(request);
      
      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        content: response.answer,
        sender: 'assistant',
        timestamp: new Date().toISOString(),
        project_id: Number(projectId)
      };
      
      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('질문 처리 실패:', error);
      const errorMessage: ChatMessage = {
        id: Date.now() + 2,
        content: '죄송합니다. 현재 서비스를 이용할 수 없습니다.',
        sender: 'assistant',
        timestamp: new Date().toISOString(),
        project_id: Number(projectId)
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAsking(false);
    }
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files || event.target.files.length === 0) return;
    
    setIsUploading(true);
    
    try {
      const file = event.target.files[0];
      const formData = new FormData();
      formData.append('file', file);
      
      const uploadResponse: Document = await documentsApi.uploadDocument(Number(projectId), file);
      
      const newDocument: Document = {
        id: uploadResponse.id,
        name: uploadResponse.name,
        content_type: uploadResponse.content_type,
        size: uploadResponse.size,
        upload_date: uploadResponse.upload_date,
        project_id: uploadResponse.project_id,
        file_path: uploadResponse.file_path,
        processed: uploadResponse.processed
      };
      
      setDocuments(prev => [...prev, newDocument]);
      setSelectedDocument(newDocument);
      setDocumentSummary('문서가 업로드되었습니다. 처리를 위해 "문서 처리" 버튼을 클릭하세요.');
    } catch (error) {
      console.error('파일 업로드 실패:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleProcessDocument = async () => {
    if (!selectedDocument || isProcessing) return;
    
    setIsProcessing(true);
    
    try {
      await documentsApi.processDocument(selectedDocument.id);
      
      // 문서 재처리 후 업데이트된 정보를 가져오기
      const updatedDocument = await documentsApi.getDocument(selectedDocument.project_id, selectedDocument.id);
      
      setDocuments(prev => prev.map(document => document.id === updatedDocument.id ? updatedDocument : document));
      setSelectedDocument(updatedDocument);
    } catch (error) {
      console.error('문서 처리 실패:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-gray-600 hover:text-gray-900"
            >
              ← ParseNoteLM
            </button>
            <span className="text-gray-400">&gt;</span>
            <h1 className="text-xl font-semibold text-gray-900">{project?.title}</h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-700">안녕하세요, {project?.user_id}님!</span>
            <button
              onClick={() => navigate('/login')}
              className="text-gray-600 hover:text-gray-900"
            >
              로그아웃
            </button>
          </div>
        </div>
      </header>

      {/* 3단 레이아웃 */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* 왼쪽: 소스 목록 */}
        <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                📁 소스
              </h2>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="bg-blue-600 text-white px-3 py-1 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-1"
              >
                {isUploading ? (
                  <>
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                    업로드 중...
                  </>
                ) : (
                  <>
                    ➕ 파일 추가
                  </>
                )}
              </button>
            </div>
            
            <div className="mb-4">
              <div className="text-sm text-gray-600 flex items-center">
                ✅ 모든 소스 • <span className="font-medium">{documents.length}</span>개 소스
              </div>
            </div>
            
            <div className="space-y-2">
              {documents.map((document) => (
                <div
                  key={document.id}
                  onClick={() => setSelectedDocument(document)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedDocument?.id === document.id
                      ? 'bg-blue-50 border border-blue-200'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-lg">📄</span>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 text-sm">{document.name}</div>
                      <div className="text-xs text-gray-500">
                        {new Date(document.upload_date).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 가운데: 메인 뷰어 */}
        <div className="flex-1 bg-white overflow-y-auto">
          <div className="p-6">
            {selectedDocument ? (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  {selectedDocument.name}
                </h2>
                <div className="bg-gray-50 p-6 rounded-lg">
                  <pre className="whitespace-pre-wrap text-gray-700">
                    문서: {selectedDocument.name}
                    파일명: {selectedDocument.name}
                    타입: {selectedDocument.content_type}
                    크기: {selectedDocument.size}
                    생성일: {selectedDocument.upload_date}
                  </pre>
                </div>
                <div className="mt-4">
                  <button
                    onClick={handleProcessDocument}
                    disabled={isProcessing || selectedDocument.processed}
                    className="bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    {isProcessing ? '처리 중...' : '문서 처리하기'}
                  </button>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">요약 내용</h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="whitespace-pre-wrap text-gray-700">{documentSummary}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-20 text-gray-500">
                왼쪽에서 문서를 선택하여 내용을 확인하세요.
              </div>
            )}
          </div>
        </div>

        {/* 오른쪽: 노트북 가이드 */}
        <div className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              🤖 노트북 가이드
            </h2>
          </div>
          
          <div className="p-4 space-y-6">
            {/* 문서 정보 */}
            {selectedDocument && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                  📄 문서 정보
                </h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-600">파일명:</span>
                    <div className="text-gray-900">{selectedDocument.name}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">크기:</span>
                    <div className="text-gray-900">{selectedDocument.size}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">업로드:</span>
                    <div className="text-gray-900">{selectedDocument.upload_date}</div>
                  </div>
                </div>
              </div>
            )}

            {/* AI 질문 섹션 */}
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                💬 이 문서에 질문하기
              </h3>
              
              <div className="space-y-3">
                <textarea
                  value={currentQuestion}
                  onChange={(e) => setCurrentQuestion(e.target.value)}
                  placeholder="예: 이 논문의 핵심 기술은?"
                  className="w-full p-3 border border-gray-300 rounded-lg text-sm resize-none"
                  rows={3}
                  disabled={documents.length === 0}
                />
                
                <button
                  onClick={handleSendMessage}
                  disabled={!currentQuestion.trim() || documents.length === 0 || isAsking}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {isAsking ? '답변 생성 중...' : '질문하기'}
                </button>
              </div>
            </div>

            {/* 채팅 기록 */}
            {chatMessages.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-900">채팅 기록</h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {chatMessages.map((message) => (
                    <div
                      key={message.id}
                      className={`p-3 rounded-lg ${
                        message.sender === 'user'
                          ? 'bg-blue-100 ml-4'
                          : 'bg-gray-100 mr-4'
                      }`}
                    >
                      <div className="text-xs text-gray-600 mb-1">
                        {message.sender === 'user' ? '나' : 'AI'}
                      </div>
                      <div className="text-sm text-gray-900">
                        {message.content}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
};
