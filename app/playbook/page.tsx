"use client";

import { AuthLoadingScreen } from "@/components/AuthLoadingScreen";
import { useAuth } from "@/context/auth-context";

export default function Playbook() {
  const { isLoading: isAuthLoading, isAuthenticated } = useAuth();

  if (isAuthLoading) return <AuthLoadingScreen />;
  if (!isAuthenticated) return null;

  return (
    <div>
      <h1>Playbook</h1>
    </div>
  );
}
