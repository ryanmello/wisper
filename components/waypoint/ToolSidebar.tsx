import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { WaypointAPI } from "@/lib/api/waypoint-api";
import { AvailableToolInfo } from "@/lib/interface/waypoint-interface";
import {
  Search,
  BarChart3,
  Shield,
  ClipboardList,
  GitPullRequest,
  Binary,
  Bug,
  Hammer,
  ShieldAlert,
  Trash2,
  FolderGit2,
  Settings,
  Terminal,
  type LucideIcon,
  Waypoints,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import LoadingToolsSkeleton from "./LoadingToolsSkeleton";

interface ToolType {
  id: string;
  label: string;
  icon: LucideIcon;
  iconColor: string;
  category: string;
  description: string;
}

interface ToolSidebarProps {
  onDragStart: (tool: ToolType) => void;
}

// Icon mapping by category
const CATEGORY_ICONS: { [key: string]: { icon: LucideIcon; color: string } } = {
  analysis: { icon: Search, color: "text-emerald-600" },
  security: { icon: Shield, color: "text-rose-600" },
  reporting: { icon: ClipboardList, color: "text-amber-600" },
  git_operations: { icon: GitPullRequest, color: "text-slate-600" },
  repository: { icon: FolderGit2, color: "text-purple-600" },
  general: { icon: Settings, color: "text-gray-600" },
};

// Specific tool name mappings (overrides category defaults)
const TOOL_SPECIFIC_ICONS: {
  [key: string]: { icon: LucideIcon; color: string };
} = {
  explore_codebase: { icon: Search, color: "text-emerald-600" },
  analyze_dependencies: { icon: BarChart3, color: "text-violet-600" },
  scan_go_vulnerabilities: { icon: Bug, color: "text-cyan-500" },
  scan_vulnerabilities: { icon: Shield, color: "text-rose-600" },
  generate_summary: { icon: ClipboardList, color: "text-amber-600" },
  apply_fixes: { icon: Hammer, color: "text-slate-600" },
  create_pull_request: { icon: GitPullRequest, color: "text-slate-600" },
  update_pull_request: { icon: GitPullRequest, color: "text-blue-600" },
  cleanup_repository: { icon: Trash2, color: "text-red-500" },
  clone_repository: { icon: FolderGit2, color: "text-green-600" },
  go_build: { icon: Binary, color: "text-cyan-500" },
  go_vet: { icon: ShieldAlert, color: "text-cyan-500" },
  go_mod_tidy: { icon: Settings, color: "text-cyan-500" },
  go_vulncheck: { icon: Bug, color: "text-cyan-500" },
};

export function getToolIcon(tool: AvailableToolInfo): {
  icon: LucideIcon;
  color: string;
} {
  // First check for tool-specific mapping
  if (TOOL_SPECIFIC_ICONS[tool.name]) {
    return TOOL_SPECIFIC_ICONS[tool.name];
  }

  // Fall back to category mapping
  if (CATEGORY_ICONS[tool.category]) {
    return CATEGORY_ICONS[tool.category];
  }

  // Default fallback
  return { icon: Terminal, color: "text-gray-500" };
}

// Helper function to get icon by tool name only (for playbook restoration)
export function getToolIconByName(toolName: string, category?: string): {
  icon: LucideIcon;
  color: string;
} {
  // First check for tool-specific mapping
  if (TOOL_SPECIFIC_ICONS[toolName]) {
    return TOOL_SPECIFIC_ICONS[toolName];
  }

  // Fall back to category mapping if provided
  if (category && CATEGORY_ICONS[category]) {
    return CATEGORY_ICONS[category];
  }

  // Default fallback
  return { icon: Terminal, color: "text-gray-500" };
}

export function formatToolLabel(toolName: string): string {
  // Convert snake_case to Title Case
  return toolName
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function formatCategory(category: string): string {
  // Convert category names to readable format
  const categoryMap: { [key: string]: string } = {
    git_operations: "Git Operations",
    analysis: "Analysis",
    security: "Security",
    reporting: "Reporting",
    repository: "Repository",
    general: "General",
  };

  return (
    categoryMap[category] ||
    category.charAt(0).toUpperCase() + category.slice(1)
  );
}

const ToolSidebar: React.FC<ToolSidebarProps> = ({ onDragStart }) => {
  const [tools, setTools] = useState<ToolType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTools = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await WaypointAPI.getTools();

      // Transform backend tools to frontend format
      const transformedTools: ToolType[] = response.tools.map(
        (tool: AvailableToolInfo) => {
          const { icon, color } = getToolIcon(tool);

          return {
            id: tool.name,
            label: formatToolLabel(tool.name),
            icon: icon,
            iconColor: color,
            category: formatCategory(tool.category),
            description: tool.description,
          };
        }
      );

      setTools(transformedTools);
    } catch (err) {
      console.error("Failed to fetch tools:", err);
      setError("Failed to load tools. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTools();
  }, []);

  const handleRetry = () => {
    fetchTools();
  };

  // Group tools by category
  const categories = Array.from(new Set(tools.map((tool) => tool.category)));

  if (loading) {
    return <LoadingToolsSkeleton />;
  }

  if (error) {
    return (
      <div className="h-full bg-gray-50 border-r border-gray-200 flex flex-col">
        <div className="flex items-center gap-2 p-4 border-b border-gray-200 flex-shrink-0">
          <Waypoints />
          <h2 className="text-lg font-semibold text-gray-800">Waypoint</h2>
        </div>
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="text-center">
            <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-3">{error}</p>
            <Button
              onClick={handleRetry}
              variant="outline"
              size="sm"
              className="text-xs"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-50 border-r border-gray-200 flex flex-col">
      <div className="flex items-center gap-2 p-4 border-b border-gray-200 flex-shrink-0">
        <Waypoints />
        <h2 className="text-lg font-semibold text-gray-800">Waypoint</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        {categories.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm text-gray-500">No tools available</p>
          </div>
        ) : (
          categories.map((category) => (
            <div key={category} className="mb-6">
              <h3 className="text-sm font-medium text-gray-600 mb-2 top-0 bg-gray-50 py-1">
                {category}
              </h3>
              <div className="space-y-2">
                {tools
                  .filter((tool) => tool.category === category)
                  .map((tool) => (
                    <div
                      key={tool.id}
                      className="flex p-2 bg-white rounded-lg border border-gray-200 cursor-move hover:shadow-md transition-shadow"
                      draggable
                      onDragStart={() => onDragStart(tool)}
                    >
                      <div className="mr-3 mt-1">
                        <tool.icon className={`w-5 h-5 ${tool.iconColor}`} />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-800">
                          {tool.label}
                        </div>
                        <div className="text-xs text-gray-500">
                          {tool.description}
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ToolSidebar;
