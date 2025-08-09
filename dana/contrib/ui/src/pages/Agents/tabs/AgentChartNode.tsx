import React from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import { Brain, Book, Tools, OpenBook, MultiplePagesEmpty, NetworkReverse } from 'iconoir-react';
import { getAgentAvatarSync } from '@/utils/avatar';
import { Badge } from '@/components/ui/badge';

interface AgentChartNodeData {
  label: string;
  icon?: React.ReactNode;
  status?: 'active' | 'coming-soon' | 'empty' | 'loading';
  count?: number;
  description?: string;
  isMain?: boolean;
  agentId?: number;
}

interface AgentChartNodeProps extends NodeProps {
  data: AgentChartNodeData;
}

const AgentChartNode: React.FC<AgentChartNodeProps> = ({ data, selected }) => {
  const { label, icon, status, description, isMain, agentId } = data;

  const getNodeClasses = () => {
    const baseClasses = 'rounded-lg border-2 transition-all duration-200 shadow-sm';

    if (isMain) {
      return `${baseClasses} w-24 h-24 bg-white border-gray-200 shadow-lg`;
    }

    const statusClasses = {
      active: 'bg-white border-gray-100 shadow-md',
      'coming-soon': 'bg-gray-50 border-gray-200',
      empty: 'bg-white border-gray-200',
      loading: 'bg-blue-50 border-blue-200 animate-pulse',
    };

    return `${baseClasses} ${statusClasses[status || 'active']} ${selected ? 'ring-2 ring-blue-500 ring-offset-2' : ''}`;
  };

  const getIconComponent = () => {
    if (icon) return icon;

    // Check if this is a coming soon item or loading
    const isComingSoon = status === 'coming-soon';
    const isLoading = status === 'loading';

    // Default icons based on label with wrapping circles
    const iconMap: Record<string, React.ReactNode> = {
      'AI Model': (
        <div className="flex justify-center items-center w-12 h-12 bg-blue-100 rounded-full">
          <Brain className={`w-6 h-6 ${isComingSoon ? 'text-gray-400' : 'text-blue-600'}`} />
        </div>
      ),
      'Knowledge Base': (
        <div className="flex justify-center items-center w-12 h-12 bg-green-100 rounded-full">
          {isLoading ? (
            <div className="w-6 h-6 rounded-full border-2 border-green-300 animate-spin border-t-green-600"></div>
          ) : (
            <OpenBook className={`w-6 h-6 ${isComingSoon ? 'text-gray-400' : 'text-green-600'}`} />
          )}
        </div>
      ),
      'Domain Knowledge': (
        <div className="flex justify-center items-center w-12 h-12 bg-green-100 rounded-full">
          {isLoading ? (
            <div className="w-6 h-6 rounded-full border-2 border-green-300 animate-spin border-t-green-600"></div>
          ) : (
            <Book className={`w-6 h-6 ${isComingSoon ? 'text-gray-400' : 'text-green-600'}`} />
          )}
        </div>
      ),
      Documents: (
        <div className="flex justify-center items-center w-12 h-12 bg-blue-100 rounded-full">
          <MultiplePagesEmpty
            className={`w-6 h-6 ${isComingSoon ? 'text-gray-400' : 'text-blue-600'}`}
          />
        </div>
      ),
      Workflows: (
        <div className="flex justify-center items-center w-12 h-12 bg-gray-100 rounded-full">
          <NetworkReverse
            className={`w-6 h-6 ${isComingSoon ? 'text-gray-400' : 'text-purple-600'}`}
          />
        </div>
      ),
      Tools: (
        <div className="flex justify-center items-center w-8 h-8 bg-gray-100 rounded-full">
          <Tools className={`w-6 h-6 ${isComingSoon ? 'text-gray-400' : 'text-orange-600'}`} />
        </div>
      ),
    };

    return (
      iconMap[label] || (
        <div className="flex justify-center items-center w-6 h-6 bg-gray-100 rounded-full">
          <div className={`w-4 h-4 ${isComingSoon ? 'text-gray-400' : 'text-gray-600'}`} />
        </div>
      )
    );
  };

  if (isMain) {
    return (
      <div className={getNodeClasses()}>
        <Handle
          type="target"
          position={Position.Left}
          id="left"
          className="w-3 h-3 bg-white border-2 border-gray-300"
          style={{
            left: '-6px',
            top: '50%',
            transform: 'translateY(-50%)',
            position: 'absolute',
          }}
        />
        <Handle
          type="source"
          position={Position.Bottom}
          className="w-3 h-3 bg-white border-2 border-gray-300"
          style={{
            bottom: '-6px',
            left: '50%',
            transform: 'translateX(-50%)',
            position: 'absolute',
          }}
        />
        <Handle
          type="source"
          position={Position.Right}
          id="right"
          className="w-3 h-3 bg-white border-2 border-gray-300"
          style={{
            right: '-6px',
            top: '50%',
            transform: 'translateY(-50%)',
            position: 'absolute',
          }}
        />
        <div className="flex flex-col justify-center items-center h-full text-gray-900">
          {/* Agent Avatar */}
          <div className="flex overflow-hidden justify-center items-center mb-1 w-12 h-12 bg-gray-100 rounded-full">
            <img
              src={getAgentAvatarSync(agentId || 0)}
              alt={`${label} avatar`}
              className="object-cover w-full h-full rounded-full"
              onError={(e) => {
                // Fallback to colored circle if image fails to load
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                const parent = target.parentElement;
                if (parent) {
                  parent.className = `flex justify-center items-center w-12 h-12 text-lg font-bold text-gray-600 bg-gray-200 rounded-full`;
                  parent.innerHTML = `<span className="font-bold text-gray-600">${label[0] || 'A'}</span>`;
                }
              }}
            />
          </div>
          {/* Agent Name */}
          <div className="text-sm font-medium leading-tight text-center text-gray-900">{label}</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${getNodeClasses()} min-w-[200px] max-w-[250px]`}>
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-white border-2 border-gray-300"
        style={{
          top: '-6px',
          left: '50%',
          transform: 'translateX(-50%)',
          position: 'absolute',
        }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-white border-2 border-gray-300"
        style={{
          bottom: '-6px',
          left: '50%',
          transform: 'translateX(-50%)',
          position: 'absolute',
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        className="w-3 h-3 bg-white border-2 border-gray-300"
        style={{
          right: '-6px',
          top: '50%',
          transform: 'translateY(-50%)',
          position: 'absolute',
        }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        className="w-3 h-3 bg-white border-2 border-gray-300"
        style={{
          left: '-6px',
          top: '50%',
          transform: 'translateY(-50%)',
          position: 'absolute',
        }}
      />

      <div className="p-4">
        <div className="flex gap-3 items-center">
          {getIconComponent()}
          <div className="flex-1">
            <div className="font-semibold text-gray-900 text-md">{label}</div>
            {description && <div className="text-sm text-gray-500">{description}</div>}
            {/* Coming soon label underneath the name */}
            {status === 'coming-soon' && (
              <Badge variant="secondary" className="mt-1 bg-blue-50">
                Coming soon
              </Badge>
            )}
            {/* Loading label underneath the name */}
            {status === 'loading' && (
              <Badge variant="secondary" className="mt-1 bg-blue-100 text-blue-700 animate-pulse">
                <div className="flex gap-1 items-center">
                  <div className="w-2 h-2 rounded-full border border-blue-500 animate-spin border-t-transparent"></div>
                  New Item Adding...
                </div>
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentChartNode;
