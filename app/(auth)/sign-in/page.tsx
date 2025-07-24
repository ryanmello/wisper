"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoadingSpinner } from "@/components/ui/loading";
import {
  Github,
  AlertCircle,
  CheckCircle,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { getBackendUrl } from "@/lib/config";

export default function SignInPage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const handleGitHubAuth = () => {
    // Redirect to backend OAuth endpoint
    window.location.href = `${getBackendUrl()}/auth/github/authorize`;
  };

  // Show loading state while checking authentication
  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
        <div className="w-full max-w-md mx-auto">
          <div className="text-center space-y-4">
            <div className="w-20 h-20 bg-gradient-to-br from-black to-gray-800 rounded-2xl flex items-center justify-center mx-auto shadow-xl">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">
                Conscience
              </h1>
              <div className="flex items-center justify-center space-x-2">
                <LoadingSpinner size="sm" />
                <p className="text-lg text-muted-foreground">
                  Checking authentication...
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Success state - user authenticated
  if (user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
        <div className="w-full max-w-md mx-auto">
          <div className="text-center space-y-6">
            <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto shadow-xl">
              <CheckCircle className="w-10 h-10 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">
                Welcome back!
              </h1>
              <p className="text-lg text-muted-foreground mb-4">
                Successfully signed in as <strong>@{user.login}</strong>
              </p>
              <div className="flex items-center justify-center space-x-2 text-sm text-muted-foreground">
                <LoadingSpinner size="sm" />
                <span>Redirecting to dashboard...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main sign-in screen
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
      <div className="w-full max-w-md mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="w-20 h-20 bg-gradient-to-br from-black to-gray-800 rounded-2xl flex items-center justify-center mx-auto shadow-xl">
            <Sparkles className="w-10 h-10 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Sign in to Conscience
            </h1>
            <p className="text-lg text-muted-foreground">
              Connect your GitHub account to get started
            </p>
          </div>
        </div>

        {/* Sign-in Options */}
        <div className="space-y-4">
          {/* GitHub OAuth */}
          <Card className="bg-card border border-border shadow-lg hover:shadow-xl transition-all duration-200 cursor-pointer group">
            <CardHeader className="text-center pb-4">
              <CardTitle className="flex items-center justify-center space-x-2">
                <Github size={18} />
                <span>GitHub Account</span>
              </CardTitle>
              <CardDescription>
                Sign in with your GitHub account for full access
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-4">
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Access all your repositories</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Secure OAuth authentication</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>One-click setup</span>
                  </li>
                </ul>
                <Button
                  onClick={handleGitHubAuth}
                  className="w-full bg-gradient-to-r from-black to-gray-800 hover:from-gray-900 hover:to-gray-700 text-white"
                >
                  <Github className="w-4 h-4 mr-2" />
                  Continue with GitHub
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Error Display */}
        {error && (
          <Card className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
                <AlertCircle className="w-5 h-5" />
                <span className="font-medium">{error}</span>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
