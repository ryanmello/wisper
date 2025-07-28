import { WaypointNode, WaypointConnection } from "./waypoint-interface";

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
  repository_url?: string;
  nodes: WaypointNode[];
  connections: WaypointConnection[];
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
