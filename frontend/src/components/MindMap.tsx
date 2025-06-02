import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { 
  Node, 
  Edge, 
  Controls, 
  Background, 
  BackgroundVariant
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Document, documentsApi } from '../services/documents';

// 마인드맵 데이터 타입 정의
interface MindmapBranch {
  title: string;
  color: 'purple' | 'orange' | 'blue';
  items: string[];
}

interface MindmapData {
  mainTopic: string;
  branches: MindmapBranch[];
}

// 색상 매핑
const COLOR_SCHEMES = {
  purple: {
    background: 'linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)',
    text: '#FFFFFF',
    border: '#8B5CF6',
    shadow: 'rgba(139, 92, 246, 0.3)'
  },
  orange: {
    background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
    text: '#FFFFFF', 
    border: '#F59E0B',
    shadow: 'rgba(245, 158, 11, 0.3)'
  },
  blue: {
    background: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
    text: '#FFFFFF',
    border: '#3B82F6', 
    shadow: 'rgba(59, 130, 246, 0.3)'
  },
  center: {
    background: 'linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%)',
    text: '#FFFFFF',
    border: '#4F46E5',
    shadow: 'rgba(79, 70, 229, 0.3)'
  },
  info: {
    background: 'linear-gradient(135deg, #6B7280 0%, #4B5563 100%)',
    text: '#FFFFFF',
    border: '#6B7280',
    shadow: 'rgba(107, 114, 128, 0.3)'
  }
};

interface MindMapProps {
  document?: Document;
  summary?: string;
}

const MindMap: React.FC<MindMapProps> = ({ document, summary }) => {
  const [mindmapData, setMindmapData] = useState<MindmapData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMindmapData = useCallback(async () => {
    if (!document?.id) return;
    
    console.log('🚀 MindMap: 마인드맵 데이터 로드 시작', { documentId: document.id });
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('📡 MindMap: API 호출 시작 - generateMindmap');
      const response = await documentsApi.generateMindmap(String(document.id));
      console.log('✅ MindMap: API 응답 성공', response);
      setMindmapData(response.mindmap);
    } catch (err) {
      console.error('❌ MindMap: API 호출 실패:', err);
      setError('마인드맵을 생성할 수 없습니다');
      console.log('🔄 MindMap: 기본 구조 표시 중');
      // 기본 마인드맵 데이터 설정
      setMindmapData({
        mainTopic: document?.original_filename || '문서 분석',
        branches: [
          {
            title: '주요 내용',
            color: 'purple',
            items: ['문서 분석 중', '내용 추출 중', '구조화 진행']
          },
          {
            title: '세부 정보', 
            color: 'orange',
            items: ['추가 분석 필요', '내용 정리 중']
          }
        ]
      });
    } finally {
      setIsLoading(false);
    }
  }, [document?.id, document?.original_filename]);

  // 마인드맵 데이터 로드
  useEffect(() => {
    console.log('🚀 MindMap useEffect 실행:', { documentId: document?.id, summary });
    if (document?.id) {
      console.log('📋 MindMap: 문서 ID 존재, 마인드맵 로드 시작');
      loadMindmapData();
    } else {
      console.log('❌ MindMap: 문서 ID 없음, 마인드맵 로드 건너뜀');
    }
  }, [document?.id, loadMindmapData]);

  // 노드와 엣지 생성
  const createMindmapNodes = (): { nodes: Node[], edges: Edge[] } => {
    if (!mindmapData) {
      return { nodes: [], edges: [] };
    }

    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // 중앙 노드 생성
    const centerNode: Node = {
      id: 'center',
      type: 'default',
      position: { x: 400, y: 300 },
      data: { label: mindmapData.mainTopic },
      style: {
        background: COLOR_SCHEMES.center.background,
        color: COLOR_SCHEMES.center.text,
        border: 'none',
        borderRadius: '25px',
        fontSize: '16px',
        fontWeight: 'bold',
        padding: '20px 30px',
        minWidth: '200px',
        textAlign: 'center',
        boxShadow: `0 4px 12px ${COLOR_SCHEMES.center.shadow}`,
        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
      },
    };
    nodes.push(centerNode);

    let nodeIdCounter = 1;

    // 좌우 분기로 브랜치 배치
    mindmapData.branches.forEach((branch, branchIndex) => {
      const colorScheme = COLOR_SCHEMES[branch.color];
      
      // 좌측/우측 교대로 배치 (간격 더 넓게)
      const isLeft = branchIndex % 2 === 0;
      const xPosition = isLeft ? 180 : 620;
      const yBasePosition = 150 + (Math.floor(branchIndex / 2) * 160); // 간격 넓힘
      
      // 브랜치 노드 생성
      const branchNode: Node = {
        id: `branch-${branchIndex}`,
        type: 'default',
        position: { x: xPosition, y: yBasePosition },
        data: { label: branch.title },
        style: {
          background: colorScheme.background,
          color: colorScheme.text,
          border: 'none',
          borderRadius: '20px',
          fontSize: '14px',
          fontWeight: '600',
          padding: '12px 20px',
          minWidth: '140px',
          textAlign: 'center',
          boxShadow: `0 4px 10px ${colorScheme.shadow}`,
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
        },
      };
      nodes.push(branchNode);

      // 중앙에서 브랜치로 곡선 연결
      edges.push({
        id: `center-branch-${branchIndex}`,
        source: 'center',
        target: `branch-${branchIndex}`,
        type: 'smoothstep',
        style: { 
          stroke: colorScheme.border, 
          strokeWidth: 3,
        },
        sourceHandle: isLeft ? 'left' : 'right',
        targetHandle: isLeft ? 'right' : 'left',
      });

      // 브랜치 아이템들을 세로로 배치 (겹침 방지)
      branch.items.forEach((item, itemIndex) => {
        const itemXPosition = isLeft ? 
          xPosition - 250 : // 좌측은 더 왼쪽으로
          xPosition + 250;  // 우측은 더 오른쪽으로
        
        const itemNode: Node = {
          id: `item-${nodeIdCounter}`,
          type: 'default',
          position: { 
            x: itemXPosition, 
            y: yBasePosition - 60 + (itemIndex * 55) // 간격 더 넓게
          },
          data: { 
            label: item.length > 20 ? item.substring(0, 20) + '...' : item 
          },
          style: {
            background: 'white',
            color: colorScheme.border,
            border: `2px solid ${colorScheme.border}`,
            borderRadius: '15px',
            fontSize: '11px',
            fontWeight: '500',
            padding: '8px 12px',
            minWidth: '150px',
            maxWidth: '180px',
            textAlign: 'center',
            boxShadow: `0 2px 6px rgba(0,0,0,0.1)`,
            fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
          },
        };
        nodes.push(itemNode);

        // 브랜치에서 아이템으로 연결
        edges.push({
          id: `branch-${branchIndex}-item-${nodeIdCounter}`,
          source: `branch-${branchIndex}`,
          target: `item-${nodeIdCounter}`,
          type: 'smoothstep',
          style: { 
            stroke: colorScheme.border, 
            strokeWidth: 2,
          },
          sourceHandle: isLeft ? 'left' : 'right',
          targetHandle: isLeft ? 'right' : 'left',
        });

        nodeIdCounter++;
      });
    });

    return { nodes, edges };
  };

  const { nodes, edges } = createMindmapNodes();

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[768px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">마인드맵 생성 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error && !mindmapData) {
    return (
      <div className="flex items-center justify-center h-[768px]">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button 
            onClick={loadMindmapData}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-[600px] bg-gray-50 rounded-lg overflow-hidden border border-gray-200">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        attributionPosition="bottom-left"
        className="bg-white"
        style={{ background: 'linear-gradient(45deg, #f8fafc 0%, #f1f5f9 100%)' }}
      >
        <Controls 
          position="top-right"
          style={{ 
            background: 'white',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
        />
        <Background 
          variant={BackgroundVariant.Dots} 
          gap={20} 
          size={1}
          color="#e2e8f0"
        />
      </ReactFlow>
      {error && (
        <div className="absolute top-2 left-2 bg-yellow-100 border border-yellow-400 text-yellow-700 px-3 py-2 rounded text-sm">
          ⚠️ AI 생성 실패 - 기본 구조 표시 중
        </div>
      )}
    </div>
  );
};

export default MindMap;
