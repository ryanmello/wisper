import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, AlertCircle, XCircle, Clock, Info } from "lucide-react";

interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'pending' | 'info' | 'neutral';
  children: React.ReactNode;
  className?: string;
  showIcon?: boolean;
}

export function StatusBadge({ 
  status, 
  children, 
  className,
  showIcon = true 
}: StatusBadgeProps) {
  const statusConfig = {
    success: {
      className: 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800',
      icon: CheckCircle
    },
    warning: {
      className: 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800',
      icon: AlertCircle
    },
    error: {
      className: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800',
      icon: XCircle
    },
    pending: {
      className: 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-900/30 dark:text-gray-400 dark:border-gray-800',
      icon: Clock
    },
    info: {
      className: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800',
      icon: Info
    },
    neutral: {
      className: 'bg-muted text-muted-foreground border-border',
      icon: Info
    }
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <Badge 
      className={cn(
        'flex items-center space-x-1 text-xs border',
        config.className,
        className
      )}
    >
      {showIcon && <Icon className="w-3 h-3" />}
      <span>{children}</span>
    </Badge>
  );
}

interface StatusIndicatorProps {
  status: 'online' | 'offline' | 'connecting' | 'error';
  label?: string;
  className?: string;
}

export function StatusIndicator({ status, label, className }: StatusIndicatorProps) {
  const statusConfig = {
    online: {
      color: 'bg-green-500',
      label: 'Online'
    },
    offline: {
      color: 'bg-gray-400',
      label: 'Offline'
    },
    connecting: {
      color: 'bg-yellow-500 animate-pulse',
      label: 'Connecting'
    },
    error: {
      color: 'bg-red-500',
      label: 'Error'
    }
  };

  const config = statusConfig[status];

  return (
    <div className={cn('flex items-center space-x-2', className)}>
      <div 
        className={cn('w-2 h-2 rounded-full', config.color)}
      />
      <span className="text-sm text-muted-foreground">
        {label || config.label}
      </span>
    </div>
  );
}

interface TaskStatusProps {
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  startTime?: Date;
  endTime?: Date;
  className?: string;
}

export function TaskStatus({ 
  status, 
  startTime, 
  endTime, 
  className 
}: TaskStatusProps) {
  const statusConfig = {
    queued: {
      badge: 'pending',
      label: 'Queued'
    },
    running: {
      badge: 'info',
      label: 'Running'
    },
    completed: {
      badge: 'success',
      label: 'Completed'
    },
    failed: {
      badge: 'error',
      label: 'Failed'
    },
    cancelled: {
      badge: 'neutral',
      label: 'Cancelled'
    }
  } as const;

  const config = statusConfig[status];
  
  const getDuration = () => {
    if (!startTime) return null;
    const end = endTime || new Date();
    const diff = end.getTime() - startTime.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  return (
    <div className={cn('flex items-center space-x-3', className)}>
      <StatusBadge status={config.badge}>
        {config.label}
      </StatusBadge>
      
      {startTime && (
        <div className="text-xs text-muted-foreground">
          {status === 'running' ? (
            <span>Started {getDuration()} ago</span>
          ) : endTime ? (
            <span>Duration: {getDuration()}</span>
          ) : (
            <span>Started {getDuration()} ago</span>
          )}
        </div>
      )}
    </div>
  );
}

interface HealthStatusProps {
  services: {
    name: string;
    status: 'healthy' | 'unhealthy' | 'degraded' | 'unknown';
    lastCheck?: Date;
    message?: string;
  }[];
  className?: string;
}

export function HealthStatus({ services, className }: HealthStatusProps) {
  const overallStatus = services.every(s => s.status === 'healthy') 
    ? 'healthy' 
    : services.some(s => s.status === 'unhealthy') 
    ? 'unhealthy' 
    : 'degraded';

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-foreground">System Health</h4>
        <StatusBadge 
          status={overallStatus === 'healthy' ? 'success' : overallStatus === 'unhealthy' ? 'error' : 'warning'}
        >
          {overallStatus === 'healthy' ? 'All Systems Operational' : 
           overallStatus === 'unhealthy' ? 'Service Issues' : 'Degraded Performance'}
        </StatusBadge>
      </div>
      
      <div className="space-y-2">
        {services.map((service, index) => (
          <div key={index} className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
            <div className="flex items-center space-x-2">
              <StatusIndicator 
                status={service.status === 'healthy' ? 'online' : 
                        service.status === 'unhealthy' ? 'error' : 
                        service.status === 'degraded' ? 'connecting' : 'offline'}
              />
              <span className="text-sm font-medium">{service.name}</span>
            </div>
            
            <div className="text-right">
              <StatusBadge
                status={service.status === 'healthy' ? 'success' :
                        service.status === 'unhealthy' ? 'error' :
                        service.status === 'degraded' ? 'warning' : 'neutral'}
                showIcon={false}
              >
                {service.status}
              </StatusBadge>
              {service.lastCheck && (
                <div className="text-xs text-muted-foreground mt-1">
                  Last checked: {service.lastCheck.toLocaleTimeString()}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 