"use client";

import { AuthLoadingScreen } from "@/components/AuthLoadingScreen";
import { useAuth } from "@/context/auth-context";
import { Fingerprint, Flower, Layers, Sparkles, Waypoints } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

const Conscience = () => {
  const { isLoading: isAuthLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      router.push('/sign-in');
    }
  }, [isAuthLoading, isAuthenticated, router]);

  if (isAuthLoading) return <AuthLoadingScreen />;
  if (!isAuthenticated) return <AuthLoadingScreen />;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="flex items-center gap-2">
          <Sparkles size={32} />
          <Fingerprint size={32} />
          <Flower size={32} />
          <Waypoints size={32} />
          <Layers size={32} />
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <span
            className="font-medium"
            style={{
              background:
                "linear-gradient(45deg, #dc2626, #0891b2, #1d4ed8, #059669, #d97706, #7c3aed, #dc2626)",
              backgroundSize: "400% 400%",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
              animation: "rainbow 4s ease-in-out infinite",
            }}
          >
            Tapping into your conscience...
          </span>
        </div>
      </div>

      <style
        dangerouslySetInnerHTML={{
          __html: `
          @keyframes rainbow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
          }
        `,
        }}
      />
    </div>
  );
};

export default Conscience;
