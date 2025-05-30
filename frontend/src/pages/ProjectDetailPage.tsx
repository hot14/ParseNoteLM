import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectsApi, Project } from '../services/projects';
import { documentsApi, Document } from '../services/documents';
import { chatApi, ChatMessage, AskQuestionRequest } from '../services/chat';
import { getErrorMessage, handleSpecialErrors, logError } from '../utils/errorHandler';

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
    } catch (projectError) {
      logError(projectError, 'loadProject');
      
      if (!handleSpecialErrors(projectError)) {
        console.error('프로젝트 로드 실패:', projectError);
      }
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  const loadDocuments = useCallback(async () => {
    if (!projectId) return;
    
    try {
      const documentsData = await documentsApi.getDocuments(Number(projectId));
      setDocuments(documentsData || []);
      
      if (documentsData && documentsData.length > 0) {
        setSelectedDocument(documentsData[0]);
      }
    } catch (documentsError) {
      logError(documentsError, 'loadDocuments');
      
      if (!handleSpecialErrors(documentsError)) {
        console.error('문서 로드 실패:', documentsError);
      }
      
      const mockDocument: Document = {
        id: 0,
        filename: "sample.pdf",
        original_filename: "sample.pdf",
        file_size: 0,
        file_size_mb: 0,
        file_type: "pdf",
        processing_status: "pending",
        content_length: 0,
        chunk_count: 0,
        project_id: Number(projectId),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      setDocuments([mockDocument]);
      setSelectedDocument(mockDocument);
    }
  }, [projectId]);

  useEffect(() => {
    loadProject();
    loadDocuments();
    setChatMessages([]); // 채팅 메시지 초기화
    setIsLoading(false);
  }, [loadProject, loadDocuments]);

  const handleSendMessage = async () => {
    if (!currentQuestion.trim() || !projectId || isAsking) return;
    
    const userMessage: ChatMessage = {
      id: Date.now(),
      message: currentQuestion,
      response: '',
      timestamp: new Date().toISOString()
    };
    
    setChatMessages(prev => [...(prev || []), userMessage]);
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
        message: '',
        response: response.message || '응답을 받을 수 없습니다.',
        timestamp: new Date().toISOString()
      };
      
      setChatMessages(prev => [...(prev || []), assistantMessage]);
    } catch (chatError) {
      logError(chatError, 'handleSendMessage');
      
      if (!handleSpecialErrors(chatError)) {
        console.error('질문 처리 실패:', chatError);
      }
      
      const errorMessage: ChatMessage = {
        id: Date.now() + 2,
        message: '',
        response: 'AI 응답 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        timestamp: new Date().toISOString()
      };
      
      setChatMessages(prev => [...(prev || []), errorMessage]);
    } finally {
      setIsAsking(false);
    }
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files || event.target.files.length === 0) return;
    
    const file = event.target.files[0];
    
    // 파일 크기 검증 (10MB 제한)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      alert('파일 크기는 10MB를 초과할 수 없습니다.');
      event.target.value = ''; // 파일 입력 초기화
      return;
    }
    
    // 파일 타입 검증
    const allowedTypes = [
      'application/pdf',
      'text/plain',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/markdown'
    ];
    
    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.md') && !file.name.endsWith('.txt')) {
      alert('지원되는 파일 형식: PDF, Word, 텍스트, 마크다운 파일만 업로드 가능합니다.');
      event.target.value = ''; // 파일 입력 초기화
      return;
    }
    
    setIsUploading(true);
    
    try {
      const uploadResponse: Document = await documentsApi.uploadDocument(Number(projectId), file);
      
      const newDocument: Document = {
        id: uploadResponse.id,
        filename: uploadResponse.filename,
        original_filename: uploadResponse.original_filename,
        file_size: uploadResponse.file_size,
        file_size_mb: uploadResponse.file_size_mb,
        file_type: uploadResponse.file_type,
        processing_status: uploadResponse.processing_status,
        content_length: uploadResponse.content_length,
        chunk_count: uploadResponse.chunk_count,
        project_id: uploadResponse.project_id,
        created_at: uploadResponse.created_at,
        updated_at: uploadResponse.updated_at
      };
      
      setDocuments(prev => Array.isArray(prev) ? [...prev, newDocument] : [newDocument]);
      setSelectedDocument(newDocument);
      setDocumentSummary('문서가 업로드되었습니다. 처리를 위해 "문서 처리" 버튼을 클릭하세요.');
    } catch (uploadError) {
      const uploadErrorMessage = getErrorMessage(uploadError);
      logError(uploadError, 'handleFileChange');
      
      if (!handleSpecialErrors(uploadError)) {
        console.error('파일 업로드 실패:', uploadError);
      }
      
      alert(uploadErrorMessage || '파일 업로드에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsUploading(false);
      event.target.value = ''; // 파일 입력 초기화
    }
  };

  const handleProcessDocument = async () => {
    if (!selectedDocument || isProcessing) return;
    
    setIsProcessing(true);
    
    try {
      await documentsApi.reprocessDocument(selectedDocument.project_id, selectedDocument.id);
      
      // 문서 재처리 후 업데이트된 정보를 가져오기
      const updatedDocument = await documentsApi.getDocument(selectedDocument.project_id, selectedDocument.id);
      
      setDocuments(prev => (prev || []).map(document => document.id === updatedDocument.id ? updatedDocument : document));
      setSelectedDocument(updatedDocument);
      
      // 문서 요약 내용 설정 (실제로는 API에서 가져와야 하지만 임시로)
      setDocumentSummary(`이 문서(${updatedDocument.filename})가 성공적으로 처리되었습니다.\n\n주요 내용:\n- 파일 크기: ${updatedDocument.file_size_mb} MB\n- 처리 상태: ${updatedDocument.processing_status}\n- 청크 수: ${updatedDocument.chunk_count}\n\n문서 처리가 완료되어 AI 질의응답이 가능합니다.`);
    } catch (processError) {
      const processErrorMessage = getErrorMessage(processError);
      logError(processError, 'handleProcessDocument');
      
      if (!handleSpecialErrors(processError)) {
        console.error('문서 처리 실패:', processError);
      }
      
      // 에러 발생 시에도 임시 요약 내용 설정
      setDocumentSummary(`문서 처리 중 오류가 발생했습니다.\n\n오류 내용: ${processErrorMessage}\n\n다시 시도해주세요.`);
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
              aria-label="ParseNoteLM으로 돌아가기"
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
              aria-label="로그아웃"
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
                aria-label={isUploading ? "파일 업로드 중" : "새 파일 추가"}
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
              {Array.isArray(documents) ? documents.map((document) => (
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
                      <div className="font-medium text-gray-900 text-sm">{document.filename}</div>
                      <div className="text-xs text-gray-500">
                        {new Date(document.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              )) : null}
            </div>
          </div>
        </div>

        {/* 가운데: 메인 뷰어 */}
        <div className="flex-1 bg-white overflow-y-auto">
          <div className="p-6">
            {selectedDocument ? (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  {selectedDocument.filename}
                </h2>
                <div className="bg-gray-50 p-6 rounded-lg">
                  <pre className="whitespace-pre-wrap text-gray-700">
                    문서: {selectedDocument.filename}
                    파일명: {selectedDocument.filename}
                    타입: {selectedDocument.file_type}
                    크기: {selectedDocument.file_size_mb}
                    생성일: {selectedDocument.created_at}
                  </pre>
                </div>
                <div className="mt-4">
                  <button
                    onClick={handleProcessDocument}
                    disabled={isProcessing || !selectedDocument}
                    aria-label={isProcessing ? "문서 처리 중" : selectedDocument?.processing_status === "completed" ? "문서 재처리하기" : "문서 처리하기"}
                    className="bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    {isProcessing ? '처리 중...' : 
                     selectedDocument?.processing_status === "completed" ? '문서 재처리하기' : '문서 처리하기'}
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
                    <div className="text-gray-900">{selectedDocument.filename}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">크기:</span>
                    <div className="text-gray-900">{selectedDocument.file_size_mb}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">업로드:</span>
                    <div className="text-gray-900">{selectedDocument.created_at}</div>
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
                  aria-label="질문 입력란"
                  className="w-full p-3 border border-gray-300 rounded-lg text-sm resize-none"
                  rows={3}
                  disabled={documents.length === 0}
                />
                
                <button
                  onClick={handleSendMessage}
                  disabled={!currentQuestion.trim() || documents.length === 0 || isAsking}
                  aria-label={isAsking ? "질문 전송 중" : "질문 전송"}
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
                  {(chatMessages || [])
                    .filter(msg => (msg.message && msg.message.trim()) || (msg.response && msg.response.trim()))
                    .map((msg) => (
                    <div key={msg.id || Math.random()}>
                      {/* 사용자 메시지 */}
                      {msg.message && msg.message.trim() && (
                        <div className="p-3 rounded-lg bg-blue-100 ml-4 mb-2">
                          <div className="text-sm text-gray-900">{msg.message}</div>
                        </div>
                      )}
                      {/* AI 응답 */}
                      {msg.response && msg.response.trim() && (
                        <div className="p-3 rounded-lg bg-gray-100 mr-4 mb-2">
                          <div className="text-sm text-gray-900">{msg.response}</div>
                        </div>
                      )}
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
