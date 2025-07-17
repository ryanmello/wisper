import {
  Fingerprint,
  Waypoints,
  Sparkles,
  Flower,
} from "lucide-react";

export const AuthLoadingScreen = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="flex items-center gap-2">
          <Fingerprint size={32} />
          <Waypoints size={32} />
          <Flower size={32} />
          <Sparkles size={32} />
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          <span>Verifying authentication...</span>
        </div>
      </div>
    </div>
  );
}; 
