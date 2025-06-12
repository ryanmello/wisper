import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-muted border-t-primary',
        sizeClasses[size],
        className
      )}
    />
  );
}

interface LoadingDotProps {
  className?: string;
}

export function LoadingDots({ className }: LoadingDotProps) {
  return (
    <div className={cn('flex space-x-1', className)}>
      <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
      <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
      <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
    </div>
  );
}

interface LoadingSkeletonProps {
  className?: string;
  lines?: number;
}

export function LoadingSkeleton({ className, lines = 1 }: LoadingSkeletonProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'h-4 bg-muted rounded animate-pulse',
            i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full'
          )}
        />
      ))}
    </div>
  );
}

interface LoadingCardProps {
  title?: string;
  description?: string;
  className?: string;
}

export function LoadingCard({ title, description, className }: LoadingCardProps) {
  return (
    <div className={cn('bg-card border border-border rounded-xl shadow-lg p-6', className)}>
      <div className="flex items-center space-x-3 mb-4">
        <LoadingSpinner size="sm" />
        <div className="flex-1">
          <h3 className="font-medium text-foreground">
            {title || 'Loading...'}
          </h3>
          {description && (
            <p className="text-sm text-muted-foreground mt-1">
              {description}
            </p>
          )}
        </div>
      </div>
      <LoadingSkeleton lines={3} />
    </div>
  );
}

interface FullPageLoadingProps {
  title?: string;
  description?: string;
}

export function FullPageLoading({ title, description }: FullPageLoadingProps) {
  return (
    <div className="min-h-screen bg-background">
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-foreground mb-2">
            {title || 'Loading'}
          </h2>
          {description && (
            <p className="text-muted-foreground max-w-md mx-auto">
              {description}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

interface ProgressBarProps {
  value: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
  label?: string;
  variant?: 'default' | 'success' | 'warning' | 'error';
}

export function ProgressBar({
  value,
  max = 100,
  className,
  showLabel = true,
  label,
  variant = 'default'
}: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100);
  
  const variantClasses = {
    default: 'bg-primary',
    success: 'bg-green-500',
    warning: 'bg-amber-500',
    error: 'bg-red-500'
  };

  return (
    <div className={cn('space-y-2', className)}>
      {showLabel && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {label || 'Progress'}
          </span>
          <span className="text-foreground font-medium">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all duration-300 ease-out', variantClasses[variant])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
} 