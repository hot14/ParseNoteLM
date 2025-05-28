/**
 * 대시보드 페이지
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { projectsApi, Project } from '../services/projects';
import { documentsApi, Document } from '../services/documents';
import { chatApi, ChatMessage, AskQuestionResponse } from '../services/chat';
import { 
  FolderPlus, 
  Upload, 
  MessageSquare, 
  FileText,
  Plus,
  Trash2,
  Download,
  Send,
  Loader2
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectStats, setProjectStats] = useState<Record<number, { document_count: number; member_count: number }>>({});
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [activeTab, setActiveTab] = useState<'projects' | 'documents' | 'chat'>('projects');
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
  
  // 채팅 관련 상태
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);

  // 프로젝트 로드
  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      const projectsData = await projectsApi.getProjects();
      setProjects(projectsData);
      
      // 각 프로젝트의 통계를 목 데이터로 설정 (실제로는 API 호출)
      const mockStats: Record<number, { document_count: number; member_count: number }> = {};
      projectsData.forEach(project => {
        mockStats[project.id] = { document_count: Math.floor(Math.random() * 20), member_count: Math.floor(Math.random() * 5) + 1 };
      });
      setProjectStats(mockStats);
    } catch (error) {
      console.error('프로젝트 로드 실패:', error);
      // 에러 발생 시 목 데이터 사용
      const mockProjects: Project[] = [
        {
          id: 1,
          name: "AI 연구 프로젝트",
          description: "최신 AI 기술 연구 및 문서화",
          created_at: "2024-01-15T10:30:00Z",
          updated_at: "2024-01-15T10:30:00Z",
          owner_id: user?.id || 1
        },
        {
          id: 2,
          name: "제품 매뉴얼",
          description: "제품 사용법 및 기술 문서",
          created_at: "2024-01-10T14:20:00Z",
          updated_at: "2024-01-10T14:20:00Z",
          owner_id: user?.id || 1
        }
      ];
      setProjects(mockProjects);
      setProjectStats({
        1: { document_count: 12, member_count: 3 },
        2: { document_count: 8, member_count: 2 }
      });
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const loadDocuments = async (projectId: number) => {
    setLoading(true);
    try {
      const documentsData = await documentsApi.getDocuments(projectId);
      setDocuments(documentsData);
    } catch (error) {
      console.error('문서 로드 실패:', error);
      // 에러 발생 시 목 데이터 사용
      const mockDocuments: Document[] = [
        {
          id: 1,
          name: "introduction.pdf",
          content_type: "application/pdf",
          size: 1024000,
          upload_date: "2024-01-15T10:30:00Z",
          project_id: projectId,
          file_path: "/uploads/introduction.pdf",
          processed: true
        },
        {
          id: 2,
          name: "research_notes.docx",
          content_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          size: 2048000,
          upload_date: "2024-01-14T15:45:00Z",
          project_id: projectId,
          file_path: "/uploads/research_notes.docx",
          processed: true
        }
      ];
      setDocuments(mockDocuments);
    } finally {
      setLoading(false);
    }
  };

  const createProject = async () => {
    if (!newProjectName.trim()) return;
    
    setLoading(true);
    try {
      const newProject = await projectsApi.createProject({
        name: newProjectName,
        description: newProjectDescription
      });
      setProjects(prev => [...prev, newProject]);
      setShowNewProjectModal(false);
      setNewProjectName('');
      setNewProjectDescription('');
    } catch (error) {
      console.error('프로젝트 생성 실패:', error);
      alert('프로젝트 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const selectProject = (project: Project) => {
    setSelectedProject(project);
    setActiveTab('documents');
    loadDocuments(project.id);
    setChatMessages([]);
    setCurrentSessionId(null);
  };

  const handleFileUpload = async (files: FileList) => {
    if (!selectedProject) return;
    
    const fileArray = Array.from(files);
    setUploadingFiles(fileArray);
    
    try {
      for (const file of fileArray) {
        await documentsApi.uploadDocument(selectedProject.id, file);
      }
      loadDocuments(selectedProject.id);
      setShowUploadModal(false);
    } catch (error) {
      console.error('파일 업로드 실패:', error);
      alert('파일 업로드에 실패했습니다.');
    } finally {
      setUploadingFiles([]);
    }
  };

  const handleDownloadDocument = async (document: Document) => {
    if (!selectedProject) return;
    
    try {
      const blob = await documentsApi.downloadDocument(selectedProject.id, document.id);
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = document.name;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('파일 다운로드 실패:', error);
      alert('파일 다운로드에 실패했습니다.');
    }
  };

  const handleDeleteDocument = async (document: Document) => {
    if (!selectedProject || !window.confirm('이 문서를 삭제하시겠습니까?')) return;
    
    try {
      await documentsApi.deleteDocument(selectedProject.id, document.id);
      setDocuments(prev => prev.filter(d => d.id !== document.id));
    } catch (error) {
      console.error('문서 삭제 실패:', error);
      alert('문서 삭제에 실패했습니다.');
    }
  };

  const handleSendMessage = async () => {
    if (!currentMessage.trim() || !selectedProject || isAsking) return;
    
    const userMessage: ChatMessage = {
      content: currentMessage,
      sender: 'user',
      timestamp: new Date().toISOString(),
      project_id: selectedProject.id
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsAsking(true);
    
    try {
      const response: AskQuestionResponse = await chatApi.askQuestion({
        question: currentMessage,
        project_id: selectedProject.id,
        session_id: currentSessionId || undefined
      });
      
      const assistantMessage: ChatMessage = {
        content: response.answer,
        sender: 'assistant',
        timestamp: new Date().toISOString(),
        project_id: selectedProject.id
      };
      
      setChatMessages(prev => [...prev, assistantMessage]);
      setCurrentSessionId(response.session_id);
    } catch (error) {
      console.error('질문 처리 실패:', error);
      const errorMessage: ChatMessage = {
        content: '죄송합니다. 현재 서비스를 이용할 수 없습니다.',
        sender: 'assistant',
        timestamp: new Date().toISOString(),
        project_id: selectedProject.id
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAsking(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-blue-600">
                ParseNoteLM
              </h1>
              {selectedProject && (
                <div className="ml-4 flex items-center">
                  <span className="text-gray-400">/</span>
                  <span className="ml-2 text-lg font-medium text-gray-700">
                    {selectedProject.name}
                  </span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                안녕하세요, {user?.username}님!
              </span>
              <button
                onClick={() => setActiveTab('chat')}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center"
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                AI 채팅
              </button>
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                로그아웃
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* 탭 네비게이션 */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('projects')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'projects'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <FolderPlus className="w-4 h-4 inline mr-2" />
                프로젝트
              </button>
              {selectedProject && (
                <button
                  onClick={() => setActiveTab('documents')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'documents'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <FileText className="w-4 h-4 inline mr-2" />
                  문서
                </button>
              )}
              <button
                onClick={() => setActiveTab('chat')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'chat'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <MessageSquare className="w-4 h-4 inline mr-2" />
                AI 채팅
              </button>
            </nav>
          </div>

          {/* 프로젝트 탭 */}
          {activeTab === 'projects' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">프로젝트</h2>
                <button
                  onClick={() => setShowNewProjectModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  새 프로젝트
                </button>
              </div>

              {loading ? (
                <div className="flex justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {projects.map((project) => (
                    <div
                      key={project.id}
                      className="bg-white overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() => selectProject(project)}
                    >
                      <div className="p-6">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <FolderPlus className="w-8 h-8 text-blue-600" />
                            <div className="ml-3">
                              <h3 className="text-lg font-medium text-gray-900">
                                {project.name}
                              </h3>
                            </div>
                          </div>
                        </div>
                        <div className="mt-4">
                          <p className="text-sm text-gray-600">
                            {project.description}
                          </p>
                        </div>
                        <div className="mt-4 flex justify-between text-sm text-gray-500">
                          <span>{projectStats[project.id]?.document_count || 0}개 문서</span>
                          <span>{projectStats[project.id]?.member_count || 0}명 멤버</span>
                        </div>
                        <div className="mt-2 text-xs text-gray-400">
                          생성일: {formatDate(project.created_at)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 문서 탭 */}
          {activeTab === 'documents' && selectedProject && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  {selectedProject.name} - 문서
                </h2>
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 flex items-center"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  문서 업로드
                </button>
              </div>

              {loading ? (
                <div className="flex justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200">
                    {documents.map((document) => (
                      <li key={document.id}>
                        <div className="px-4 py-4 flex items-center justify-between hover:bg-gray-50">
                          <div className="flex items-center">
                            <FileText className="w-6 h-6 text-gray-400" />
                            <div className="ml-3">
                              <p className="text-sm font-medium text-gray-900">
                                {document.name}
                              </p>
                              <p className="text-sm text-gray-500">
                                {formatFileSize(document.size)} • {formatDate(document.upload_date)}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleDownloadDocument(document)}
                              className="text-gray-400 hover:text-blue-600"
                            >
                              <Download className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteDocument(document)}
                              className="text-gray-400 hover:text-red-600"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* 채팅 탭 */}
          {activeTab === 'chat' && (
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">AI 채팅</h2>
              <div className="bg-white shadow rounded-lg">
                <div className="h-96 p-4 overflow-y-auto border-b">
                  <div className="space-y-4">
                    {chatMessages.map((message, index) => (
                      <div key={index} className="flex justify-start">
                        <div
                          className={`bg-gray-100 rounded-lg px-4 py-2 max-w-xs ${
                            message.sender === 'assistant'
                              ? 'bg-blue-100 text-blue-600'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          <p className="text-sm">{message.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="p-4">
                  <div className="flex">
                    <input
                      type="text"
                      value={currentMessage}
                      onChange={(e) => setCurrentMessage(e.target.value)}
                      placeholder="메시지를 입력하세요..."
                      className="flex-1 border border-gray-300 rounded-l-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      onClick={handleSendMessage}
                      disabled={isAsking}
                      className="bg-blue-600 text-white px-6 py-2 rounded-r-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {isAsking ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 새 프로젝트 모달 */}
      {showNewProjectModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">새 프로젝트 생성</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">프로젝트 이름</label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="프로젝트 이름을 입력하세요"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">설명 (선택사항)</label>
                <textarea
                  value={newProjectDescription}
                  onChange={(e) => setNewProjectDescription(e.target.value)}
                  rows={3}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="프로젝트 설명을 입력하세요"
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowNewProjectModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={createProject}
                disabled={!newProjectName.trim() || loading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                생성
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 파일 업로드 모달 */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">문서 업로드</h3>
            <div 
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-gray-400"
              onClick={() => {
                const input = window.document.createElement('input');
                input.type = 'file';
                input.multiple = true;
                input.accept = '.pdf,.docx,.txt';
                input.onchange = (e) => {
                  const files = (e.target as HTMLInputElement).files;
                  if (files) handleFileUpload(files);
                };
                input.click();
              }}
            >
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <p className="text-sm text-gray-600">
                  클릭하거나 파일을 여기로 드래그하세요
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  PDF, DOCX, TXT 파일 (최대 10MB)
                </p>
              </div>
            </div>
            
            {uploadingFiles.length > 0 && (
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-2">업로드 중:</p>
                {uploadingFiles.map((file, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm text-gray-500">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>{file.name}</span>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};