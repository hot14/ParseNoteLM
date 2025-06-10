import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectsApi, Project } from '../services/projects';
import { documentsApi, Document } from '../services/documents';
import { chatApi, ChatMessage, AskQuestionRequest } from '../services/chat';
import { getErrorMessage, handleSpecialErrors, logError } from '../utils/errorHandler';
import { useAuth } from '../contexts/AuthContext';
import MindMap from '../components/MindMap';

// 프로젝트 상세 페이지에서 사용할 확장된 프로젝트 타입
interface ProjectDetail extends Project {
  title?: string;
  user_id?: number;
  document_count?: number;
}

// 탭 타입 정의
type TabType = 'document' | 'notes' | 'summary' | 'mindmap' | 'video';

// 파일 업로드 응답 타입은 Document 타입을 직접 사용

export const ProjectDetailPage: React.FC = () => {
  console.log('🚀 ProjectDetailPage 렌더링 시작!');
  
  const { projectId } = useParams<{ projectId: string }>();
  console.log('📌 프로젝트 ID:', projectId);
  
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
  const [activeTab, setActiveTab] = useState<TabType>('mindmap'); // 기본 탭을 마인드맵으로 변경
  const [notes, setNotes] = useState<string>(''); // 노트 상태 추가
  const [videoTranscript, setVideoTranscript] = useState<string>('');
  const [videoSummary, setVideoSummary] = useState<string>('');
  const [isVideoUploading, setIsVideoUploading] = useState(false);

  const { user, logout } = useAuth();

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
    
    console.log('🔍 문서 로딩 시작, projectId:', projectId);
    
    try {
      const documentsData = await documentsApi.getDocuments(Number(projectId));
      console.log('📄 로드된 문서 데이터:', documentsData);
      
      // API 응답 구조: {documents: Array, total: number, project_can_add_more: boolean}
      const documents = documentsData.documents || [];
      console.log('📄 추출된 문서 배열:', documents);
      
      setDocuments(documents);
      
      if (documents && documents.length > 0) {
        setSelectedDocument(documents[0]);
        console.log('✅ 선택된 문서:', documents[0]);
      } else {
        console.log('📭 문서가 없습니다');
      }
    } catch (documentsError) {
      console.error('❌ 문서 로드 실패:', documentsError);
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
      console.log('🔧 목업 문서로 대체됨');
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
    
    setChatMessages(prev => [userMessage, ...(prev || [])]);
    setCurrentQuestion('');
    setIsAsking(true);
    
    try {
      const request: AskQuestionRequest = {
        question: currentQuestion,
        project_id: Number(projectId)
      };
      
      const response = await chatApi.askQuestion(request);
      
      // 질문 메시지를 찾아서 응답을 업데이트
      setChatMessages(prev => {
        const updated = [...(prev || [])];
        const questionIndex = updated.findIndex(msg => msg.id === userMessage.id);
        if (questionIndex !== -1) {
          updated[questionIndex] = {
            ...updated[questionIndex],
            response: response.message || '응답을 받을 수 없습니다.'
          };
        }
        return updated;
      });
    } catch (chatError) {
      logError(chatError, 'handleSendMessage');
      
      if (!handleSpecialErrors(chatError)) {
        console.error('질문 처리 실패:', chatError);
      }
      
      // 질문 메시지를 찾아서 에러 메시지를 업데이트
      setChatMessages(prev => {
        const updated = [...(prev || [])];
        const questionIndex = updated.findIndex(msg => msg.id === userMessage.id);
        if (questionIndex !== -1) {
          updated[questionIndex] = {
            ...updated[questionIndex],
            response: 'AI 응답 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
          };
        }
        return updated;
      });
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
      
      // 실제 문서 요약 생성
      await loadDocumentSummary(updatedDocument.id);
      
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

  const handleVideoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files || event.target.files.length === 0) return;
    const file = event.target.files[0];
    setIsVideoUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await fetch('/api/videos/summary', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setVideoTranscript(data.transcript || '');
      setVideoSummary(data.summary || '');
    } catch (e) {
      console.error(e);
    } finally {
      setIsVideoUploading(false);
      event.target.value = '';
    }
  };

  // 문서 요약 로드 함수 추가
  const loadDocumentSummary = useCallback(async (documentId?: number) => {
    if (!projectId) return;
    
    try {
      console.log('📄 문서 요약 생성 중...');
      const summaryResponse = await documentsApi.generateSummary(Number(projectId), documentId);
      
      console.log('✅ 문서 요약 생성 완료:', summaryResponse);
      setDocumentSummary(summaryResponse.summary);
      
    } catch (summaryError) {
      const summaryErrorMessage = getErrorMessage(summaryError);
      logError(summaryError, 'loadDocumentSummary');
      
      console.error('문서 요약 생성 실패:', summaryError);
      
      // 요약 생성 실패 시 기본 메시지 설정
      if (documentId && selectedDocument) {
        setDocumentSummary(`${selectedDocument.original_filename} 문서의 요약을 생성할 수 없습니다.\n\n오류: ${summaryErrorMessage}\n\n문서가 올바르게 처리되었는지 확인해주세요.`);
      } else {
        setDocumentSummary(`문서 요약을 생성할 수 없습니다.\n\n오류: ${summaryErrorMessage}`);
      }
    }
  }, [projectId, selectedDocument]);

  // 문서 선택 시 요약 자동 로드
  useEffect(() => {
    if (selectedDocument && selectedDocument.processing_status === 'completed') {
      loadDocumentSummary(selectedDocument.id);
    }
  }, [selectedDocument, loadDocumentSummary]);

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
            <span className="text-gray-700">안녕하세요, {user?.username}님!</span>
            <button
              onClick={() => {
                logout();
                navigate('/login');
              }}
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
                  
                  {/* 선택된 문서인 경우 재처리 버튼 표시 */}
                  {selectedDocument?.id === document.id && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <button
                        onClick={(e) => {
                          e.stopPropagation(); // 문서 선택 이벤트 방지
                          handleProcessDocument();
                        }}
                        disabled={isProcessing}
                        className="w-full bg-green-600 text-white py-1.5 px-3 rounded text-xs font-medium hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                      >
                        {isProcessing ? '처리 중...' : 
                         document.processing_status === "completed" ? '🔄 재처리' : '⚡ 처리하기'}
                      </button>
                    </div>
                  )}
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
                
                {/* 탭 네비게이션 */}
                <div className="border-b border-gray-200 mb-6">
                  <nav className="-mb-px flex space-x-8">
                    <button
                      onClick={() => setActiveTab('mindmap')}
                      className={`py-2 px-1 border-b-2 font-medium text-sm ${
                        activeTab === 'mindmap'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      🗺️ 마인드맵
                    </button>
                    <button
                      onClick={() => setActiveTab('document')}
                      className={`py-2 px-1 border-b-2 font-medium text-sm ${
                        activeTab === 'document'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      📄 문서 보기
                    </button>
                    <button
                      onClick={() => setActiveTab('notes')}
                      className={`py-2 px-1 border-b-2 font-medium text-sm ${
                        activeTab === 'notes'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      📝 노트
                    </button>
                    <button
                      onClick={() => setActiveTab('summary')}
                      className={`py-2 px-1 border-b-2 font-medium text-sm ${
                        activeTab === 'summary'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      📊 요약
                    </button>
                    <button
                      onClick={() => setActiveTab('video')}
                      className={`py-2 px-1 border-b-2 font-medium text-sm ${
                        activeTab === 'video'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      🎥 영상 요약
                    </button>
                  </nav>
                </div>

                {/* 탭 내용 */}
                {activeTab === 'mindmap' && (
                  <div className="bg-gray-50 p-6 rounded-lg h-[48rem]">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">🗺️ 마인드맵</h3>
                    <div className="h-[40rem]">
                      <MindMap document={selectedDocument} summary={documentSummary} />
                    </div>
                  </div>
                )}
                {activeTab === 'document' && (
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div><span className="font-medium">파일명:</span> {selectedDocument.filename}</div>
                      <div><span className="font-medium">타입:</span> {selectedDocument.file_type}</div>
                      <div><span className="font-medium">크기:</span> {selectedDocument.file_size_mb} MB</div>
                      <div><span className="font-medium">상태:</span> 
                        <span className={`ml-2 px-2 py-1 rounded text-xs ${
                          selectedDocument.processing_status === 'completed' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {selectedDocument.processing_status === 'completed' ? '처리 완료' : '처리 대기'}
                        </span>
                      </div>
                      <div><span className="font-medium">청크 수:</span> {selectedDocument.chunk_count || '0'}</div>
                      <div><span className="font-medium">생성일:</span> {new Date(selectedDocument.created_at).toLocaleString()}</div>
                    </div>
                  </div>
                )}
                {activeTab === 'notes' && (
                  <div className="space-y-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h3 className="text-sm font-semibold text-gray-900 mb-2">📝 개인 노트</h3>
                      <p className="text-xs text-gray-600 mb-3">이 문서에 대한 개인적인 메모나 생각을 적어보세요.</p>
                    </div>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="예: 이 논문의 핵심 아이디어는..."
                      className="w-full h-96 p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <div className="flex justify-end">
                      <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
                        💾 노트 저장
                      </button>
                    </div>
                  </div>
                )}
                {activeTab === 'summary' && (
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">📊 AI 요약 결과</h3>
                      {selectedDocument && (
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-gray-600">
                            현재 문서: <strong>{selectedDocument.original_filename}</strong>
                          </span>
                          <button
                            onClick={() => loadDocumentSummary(selectedDocument.id)}
                            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                          >
                            요약 재생성
                          </button>
                        </div>
                      )}
                    </div>
                    <div className="prose prose-sm max-w-none">
                      <p className="whitespace-pre-wrap text-gray-700">
                        {selectedDocument 
                          ? (documentSummary || `${selectedDocument.original_filename} 문서의 요약을 생성하려면 "요약 재생성" 버튼을 클릭하세요.`)
                          : "먼저 왼쪽에서 문서를 선택해주세요."
                        }
                      </p>
                    </div>
                  </div>
                )}
                {activeTab === 'video' && (
                  <div className="bg-gray-50 p-6 rounded-lg space-y-4">
                    <div>
                      <button
                        onClick={() => document.getElementById('videoInput')?.click()}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                        {isVideoUploading ? '업로드 중...' : '영상 업로드'}
                      </button>
                    </div>
                    {videoSummary && (
                      <div>
                        <h3 className="font-semibold mb-2">요약</h3>
                        <pre className="whitespace-pre-wrap text-sm">{videoSummary}</pre>
                      </div>
                    )}
                    {videoTranscript && (
                      <div>
                        <h3 className="font-semibold mb-2">스크립트</h3>
                        <pre className="whitespace-pre-wrap text-sm max-h-64 overflow-y-auto">{videoTranscript}</pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-20 text-gray-500">
                <div className="mb-4">
                  <span className="text-6xl">📄</span>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">문서를 선택해주세요</h3>
                <p className="text-sm text-gray-500">왼쪽에서 문서를 선택하여 내용을 확인하고 노트를 작성하세요.</p>
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
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {(chatMessages || [])
                    .filter(msg => (msg.message && msg.message.trim()) || (msg.response && msg.response.trim()))
                    .map((msg) => (
                    <div key={msg.id || Math.random()} className="space-y-2">
                      {/* 사용자 메시지 */}
                      {msg.message && msg.message.trim() && (
                        <div className="p-3 rounded-lg bg-blue-100 ml-4">
                          <div className="text-sm text-gray-900">{msg.message}</div>
                        </div>
                      )}
                      {/* AI 응답 */}
                      {msg.response && msg.response.trim() && (
                        <div className="p-3 rounded-lg bg-gray-100 mr-4">
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
      <input
        type="file"
        accept="video/*"
        onChange={handleVideoUpload}
        className="hidden"
        id="videoInput"
      />
    </div>
  );
};
