import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft } from "lucide-react";

interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
}

interface NavigationHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  onBack?: () => void;
  actions?: React.ReactNode;
  progress?: {
    current: number;
    total: number;
    label?: string;
  };
}

export function NavigationHeader({
  title,
  subtitle,
  breadcrumbs,
  onBack,
  actions,
  progress,
}: NavigationHeaderProps) {
  return (
    <div className="border-b bg-card/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center justify-between py-2">
          <div className="flex items-center space-x-4">
            {onBack && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
                className="shrink-0"
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Back
              </Button>
            )}
            
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-black to-gray-800 rounded-lg flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-sm">W</span>
              </div>
              
              <div className="min-w-0 flex-1">
                <div className="flex items-center space-x-2">
                  <h1 className="text-xl font-bold text-foreground">{title}</h1>
                  {progress && (
                    <Badge variant="secondary" className="text-xs">
                      {progress.current}/{progress.total}
                      {progress.label && ` ${progress.label}`}
                    </Badge>
                  )}
                </div>
                
                {subtitle && (
                  <p className="text-muted-foreground text-sm mt-1">{subtitle}</p>
                )}
                
                {breadcrumbs && breadcrumbs.length > 0 && (
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground mt-1">
                    {breadcrumbs.map((item, index) => (
                      <span key={index} className="flex items-center">
                        {index > 0 && <span className="mx-2 text-border">/</span>}
                        <span
                          className={
                            item.current
                              ? "text-foreground font-medium"
                              : "text-muted-foreground hover:text-foreground"
                          }
                        >
                          {item.href ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => item.href && console.log('Navigate to:', item.href)}
                              className="hover:underline h-auto p-0 text-inherit font-inherit"
                            >
                              {item.label}
                            </Button>
                          ) : (
                            item.label
                          )}
                        </span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {actions && (
            <div className="flex items-center space-x-2">
              {actions}
            </div>
          )}
        </div>
        
        {progress && (
          <div className="pb-3">
            <div className="flex items-center justify-between text-sm text-muted-foreground mb-2">
              <span>Progress</span>
              <span>{Math.round((progress.current / progress.total) * 100)}%</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-300 ease-out"
                style={{
                  width: `${(progress.current / progress.total) * 100}%`,
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface StepIndicatorProps {
  steps: {
    id: string;
    label: string;
    description?: string;
    status: 'completed' | 'current' | 'upcoming';
  }[];
}

export function StepIndicator({ steps }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-between w-full">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center">
          <div className="flex flex-col items-center">
            <div
              className={`
                w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium border-2 transition-colors
                ${
                  step.status === 'completed'
                    ? 'bg-primary border-primary text-primary-foreground'
                    : step.status === 'current'
                    ? 'bg-background border-primary text-primary'
                    : 'bg-background border-muted text-muted-foreground'
                }
              `}
            >
              {step.status === 'completed' ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                index + 1
              )}
            </div>
            
            <div className="mt-2 text-center">
              <div
                className={`text-sm font-medium ${
                  step.status === 'current'
                    ? 'text-foreground'
                    : step.status === 'completed'
                    ? 'text-primary'
                    : 'text-muted-foreground'
                }`}
              >
                {step.label}
              </div>
              {step.description && (
                <div className="text-xs text-muted-foreground mt-1 max-w-32">
                  {step.description}
                </div>
              )}
            </div>
          </div>
          
          {index < steps.length - 1 && (
            <div
              className={`flex-1 h-0.5 mx-4 ${
                steps[index + 1].status === 'completed' || step.status === 'completed'
                  ? 'bg-primary'
                  : 'bg-border'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

interface QuickActionsProps {
  actions: {
    label: string;
    icon?: React.ReactNode;
    onClick: () => void;
    variant?: 'default' | 'secondary' | 'outline';
  }[];
}

export function QuickActions({ actions }: QuickActionsProps) {
  return (
    <div className="flex items-center space-x-2">
      {actions.map((action, index) => (
        <Button
          key={index}
          variant={action.variant || 'outline'}
          size="sm"
          onClick={action.onClick}
          className="flex items-center space-x-1"
        >
          {action.icon}
          <span>{action.label}</span>
        </Button>
      ))}
    </div>
  );
} 