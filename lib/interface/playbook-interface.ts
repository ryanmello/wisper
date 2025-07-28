export interface CipherPlaybook {
  id: string;
  name: string;
  description?: string;
  prompt: string;
  repository?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  author?: string;
}

export interface WaypointPlaybook {
  id: string;
  name: string;
  description?: string;
  nodes: Array<{
    id: string;
    tool_name: string;
    position: { x: number; y: number };
    data: {
      label: string;
      icon: string;
      iconColor: string;
      category: string;
    };
  }>;
  connections: Array<{
    id: string;
    source_id: string;
    target_id: string;
    source_tool_name: string;
    target_tool_name: string;
    sourceHandle: string;
    targetHandle: string;
  }>;
  tags: string[];
  created_at: string;
  updated_at: string;
  author?: string;
}

export interface Playbook {
  id: string;
  name: string;
  description?: string;
  type: 'cipher' | 'waypoint' | 'combined';
  cipher_config?: CipherPlaybook;
  waypoint_config?: WaypointPlaybook;
  tags: string[];
  created_at: string;
  updated_at: string;
  author?: string;
  is_public: boolean;
}

export interface PlaybookCollection {
  my_playbooks: Playbook[];
  public_playbooks: Playbook[];
  recent_playbooks: Playbook[];
} 
