/**
 * 대시보드 페이지
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { projectsApi, Project } from '../services/projects';
import { Plus, FolderPlus } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectStats, setProjectStats] = useState<Record<number, { document_count: number; member_count: number }>>({});
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [loading, setLoading] = useState(false);

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

  const createProject = async () => {
    if (!newProjectName.trim()) return;
    
    setLoading(true);
    try {
      const newProject = await projectsApi.createProject({
        title: newProjectName,
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
    navigate(`/projects/${project.id}`);
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
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                안녕하세요, {user?.username}님!
              </span>
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
          {/* 프로젝트 탭 */}
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
                        생성일: {project.created_at}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
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
    </div>
  );
};