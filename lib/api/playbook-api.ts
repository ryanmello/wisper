import type { Playbook, CipherPlaybook, WaypointPlaybook } from "@/lib/interface/playbook-interface";

const PLAYBOOKS_STORAGE_KEY = 'wisper_playbooks';

export class PlaybookAPI {
  private static getPlaybooks(): Playbook[] {
    if (typeof window === 'undefined') return [];
    
    try {
      const stored = localStorage.getItem(PLAYBOOKS_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('Error reading playbook from localStorage:', error);
      return [];
    }
  }

  private static savePlaybooks(playbooks: Playbook[]): void {
    if (typeof window === 'undefined') return;
    
    try {
      localStorage.setItem(PLAYBOOKS_STORAGE_KEY, JSON.stringify(playbooks));
    } catch (error) {
      console.error('Error saving playbook to localStorage:', error);
      throw new Error('Failed to save playbook');
    }
  }

  static async saveCipherPlaybook(data: {
    name: string;
    description: string;
    prompt: string;
    repository?: string;
    tags: string[];
  }): Promise<{ success: boolean; playbook_id: string; message: string }> {
    try {
      // Validate required fields
      if (!data.name.trim()) {
        return {
          success: false,
          playbook_id: '',
          message: 'Name is required',
        };
      }
      
      if (!data.description.trim()) {
        return {
          success: false,
          playbook_id: '',
          message: 'Description is required',
        };
      }
      
      if (!data.tags || data.tags.length === 0) {
        return {
          success: false,
          playbook_id: '',
          message: 'At least one tag is required',
        };
      }

      const playbooks = this.getPlaybooks();
      const now = new Date().toISOString();
      const playbook_id = `cipher_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      const cipherConfig: CipherPlaybook = {
        id: playbook_id,
        name: data.name,
        description: data.description,
        prompt: data.prompt,
        repository: data.repository,
        tags: data.tags,
        created_at: now,
        updated_at: now,
        author: 'me',
      };

      const playbook: Playbook = {
        id: playbook_id,
        name: data.name,
        description: data.description,
        type: 'cipher',
        cipher_config: cipherConfig,
        tags: data.tags,
        created_at: now,
        updated_at: now,
        author: 'me',
        is_public: false,
      };

      playbooks.push(playbook);
      this.savePlaybooks(playbooks);

      return {
        success: true,
        playbook_id,
        message: 'Cipher playbook saved successfully',
      };
    } catch (error) {
      console.error('Error saving cipher playbook:', error);
      return {
        success: false,
        playbook_id: '',
        message: 'Failed to save cipher playbook',
      };
    }
  }

  static async saveWaypointPlaybook(data: {
    name: string;
    description?: string;
    nodes: any[];
    connections: any[];
    tags?: string[];
  }): Promise<{ success: boolean; playbook_id: string; message: string }> {
    try {
      const playbooks = this.getPlaybooks();
      const now = new Date().toISOString();
      const playbook_id = `waypoint_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      const waypointConfig: WaypointPlaybook = {
        id: playbook_id,
        name: data.name,
        description: data.description,
        nodes: data.nodes,
        connections: data.connections,
        tags: data.tags || [],
        created_at: now,
        updated_at: now,
        author: 'me',
      };

      const playbook: Playbook = {
        id: playbook_id,
        name: data.name,
        description: data.description,
        type: 'waypoint',
        waypoint_config: waypointConfig,
        tags: data.tags || [],
        created_at: now,
        updated_at: now,
        author: 'me',
        is_public: false,
      };

      playbooks.push(playbook);
      this.savePlaybooks(playbooks);

      return {
        success: true,
        playbook_id,
        message: 'Waypoint playbook saved successfully',
      };
    } catch (error) {
      console.error('Error saving waypoint playbook:', error);
      return {
        success: false,
        playbook_id: '',
        message: 'Failed to save waypoint playbook',
      };
    }
  }

  static getAllPlaybooks(): {
    cipher_playbooks: Playbook[];
    waypoint_playbooks: Playbook[];
    total_count: number;
  } {
    try {
      const playbooks = this.getPlaybooks();
      const cipher_playbooks = playbooks.filter(p => p.type === 'cipher');
      const waypoint_playbooks = playbooks.filter(p => p.type === 'waypoint');

      return {
        cipher_playbooks,
        waypoint_playbooks,
        total_count: playbooks.length,
      };
    } catch (error) {
      console.error('Error getting playbooks:', error);
      return {
        cipher_playbooks: [],
        waypoint_playbooks: [],
        total_count: 0,
      };
    }
  }

  static async deletePlaybook(playbook_id: string): Promise<{ success: boolean; message: string }> {
    try {
      const playbooks = this.getPlaybooks();
      const filteredPlaybooks = playbooks.filter(p => p.id !== playbook_id);
      
      if (filteredPlaybooks.length === playbooks.length) {
        return {
          success: false,
          message: 'Playbook not found',
        };
      }

      this.savePlaybooks(filteredPlaybooks);

      return {
        success: true,
        message: 'Playbook deleted successfully',
      };
    } catch (error) {
      console.error('Error deleting playbook:', error);
      return {
        success: false,
        message: 'Failed to delete playbook',
      };
    }
  }

  static async updatePlaybook(playbook_id: string, updates: Partial<Playbook>): Promise<{ success: boolean; message: string }> {
    try {
      const playbooks = this.getPlaybooks();
      const index = playbooks.findIndex(p => p.id === playbook_id);
      
      if (index === -1) {
        return {
          success: false,
          message: 'Playbook not found',
        };
      }

      playbooks[index] = {
        ...playbooks[index],
        ...updates,
        updated_at: new Date().toISOString(),
      };

      this.savePlaybooks(playbooks);

      return {
        success: true,
        message: 'Playbook updated successfully',
      };
    } catch (error) {
      console.error('Error updating playbook:', error);
      return {
        success: false,
        message: 'Failed to update playbook',
      };
    }
  }
} 
