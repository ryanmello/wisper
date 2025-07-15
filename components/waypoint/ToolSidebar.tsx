import {
  Search,
  BarChart3,
  Shield,
  ClipboardList,
  GitPullRequest,
  Binary,
  Bug,
  Bubbles,
  Hammer,
  ShieldAlert,
  Waypoints,
} from "lucide-react";

const TOOLS = [
  {
    id: "explore_codebase",
    label: "Explore Codebase",
    icon: Search,
    iconColor: "text-emerald-600",
    category: "Analysis",
    description: "Analyze codebase structure",
  },
  {
    id: "analyze_dependencies",
    label: "Analyze Dependencies",
    icon: BarChart3,
    iconColor: "text-violet-600",
    category: "Analysis",
    description: "Analyze project dependencies",
  },
  {
    id: "scan_vulnerabilities",
    label: "Scan Vulnerabilities",
    icon: Shield,
    iconColor: "text-rose-600",
    category: "Security",
    description: "Scan for security vulnerabilities",
  },
  {
    id: "generate_summary",
    label: "Generate Summary",
    icon: ClipboardList,
    iconColor: "text-amber-600",
    category: "Reporting",
    description: "Generate analysis summary",
  },
  {
    id: "apply_fixes",
    label: "Apply Fixes",
    icon: Hammer,
    iconColor: "text-slate-600",
    category: "Git Operations",
    description: "Create a pull request with fixes",
  },
  {
    id: "create_pull_request",
    label: "Create Pull Request",
    icon: GitPullRequest,
    iconColor: "text-slate-600",
    category: "Git Operations",
    description: "Create a pull request with fixes",
  },
  {
    id: "go_vulncheck",
    label: "govulncheck",
    icon: Bug,
    iconColor: "text-cyan-500",
    category: "Go",
    description: "Check project for vulnerabilities",
  },
  {
    id: "go_mod_tidy",
    label: "go mod tidy",
    icon: Bubbles,
    iconColor: "text-cyan-500",
    category: "Go",
    description: "Clean up go.mod and go.sum",
  },
  {
    id: "go_vet",
    label: "go vet",
    icon: ShieldAlert,
    iconColor: "text-cyan-500",
    category: "Go",
    description: "Static analysis check",
  },
  {
    id: "go_build",
    label: "go build",
    icon: Binary,
    iconColor: "text-cyan-500",
    category: "Go",
    description: "Compile go source code",
  },
];

interface ToolType {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  category: string;
  description: string;
}

const ToolSidebar: React.FC<{ onDragStart: (tool: ToolType) => void }> = ({
  onDragStart,
}) => {
  const categories = Array.from(new Set(TOOLS.map((tool) => tool.category)));

  return (
    <div className="h-full bg-gray-50 border-r border-gray-200 flex flex-col">
      <div className="flex items-center gap-2 p-4 border-b border-gray-200 flex-shrink-0">
        <Waypoints />
        <h2 className="text-lg font-semibold text-gray-800">Waypoint</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        {categories.map((category) => (
          <div key={category} className="mb-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2 top-0 bg-gray-50 py-1">
              {category}
            </h3>
            <div className="space-y-2">
              {TOOLS.filter((tool) => tool.category === category).map(
                (tool) => (
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
                )
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ToolSidebar;
