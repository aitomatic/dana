import React from 'react';
import DomainKnowledgeTree from './DomainKnowledgeTree';
import { useParams } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';

const DomainKnowledgeTab: React.FC = () => {
  const { agent_id } = useParams<{ agent_id: string }>();
  const agent = useAgentStore((s) => s.selectedAgent);

  // Use agent_id from URL params or fall back to selected agent's id
  const agentId = agent_id || agent?.id;

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <DomainKnowledgeTree agentId={agentId} />
    </div>
  );
};

export default DomainKnowledgeTab;
