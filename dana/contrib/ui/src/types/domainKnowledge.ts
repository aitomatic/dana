// Domain Knowledge Types

export interface DomainNode {
  topic: string;
  children: DomainNode[];
}

export interface DomainKnowledgeTree {
  root: DomainNode;
  last_updated?: string;
  version?: number;
}

export interface DomainKnowledgeResponse {
  root?: DomainNode;
  last_updated?: string;
  version?: number;
  message?: string; // For "No domain knowledge found" case
}

// UI specific types for the tree visualization
export interface TreeNode {
  id: string;
  label: string;
  children: TreeNode[];
  parentId?: string;
}

export interface FlowNode {
  id: string;
  type: string;
  data: { label: string };
  position: { x: number; y: number };
  targetPosition?: string;
  sourcePosition?: string;
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  markerEnd?: { type: string };
  type?: string;
}
