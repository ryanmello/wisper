import { LucideIcon } from "lucide-react";

export interface WaypointNode {
  id: string;
  tool_name: string;
  position: { x: number; y: number };
  data: {
    label: string;
    icon: LucideIcon;
    iconColor: string;
    category: string;
  };
}

export interface WaypointConnection {
  id: string;
  source_id: string;
  source_tool_name: string;
  target_id: string;
  target_tool_name: string;
  sourceHandle?: string;
  targetHandle?: string;
}
