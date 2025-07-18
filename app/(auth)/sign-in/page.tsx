"use client";

import { useState, useEffect, useCallback } from "react";
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
import { StatusBadge } from "@/components/ui/status";
import {
  Github,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  Settings,
  Fingerprint,
  ArrowRight,
} from "lucide-react";



export default function SignInPage() {
  const router = useRouter();
  const { login, user, isLoading: isAuthLoading } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showTokenInput, setShowTokenInput] = useState(false);
  const [token, setToken] = useState("");

  const GITHUB_CLIENT_ID = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID;

  const handleTokenConnect = useCallback(
    async (providedToken?: string) => {
      const activeToken = providedToken || token;
      if (!activeToken.trim()) {
        setError("Please enter a GitHub token");
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        await login(activeToken);
        
        // Redirect to main application
        setTimeout(() => {
          router.push("/cipher");
        }, 1500);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setIsLoading(false);
      }
    },
    [token, router, login]
  );

  // Check for stored GitHub token on component mount
  useEffect(() => {
    const storedToken = localStorage.getItem("github_token");

    if (storedToken) {
      setToken(storedToken);
      handleTokenConnect(storedToken);
    }
  }, [handleTokenConnect]);

  const handleGitHubAuth = () => {
    if (!GITHUB_CLIENT_ID || GITHUB_CLIENT_ID.trim() === "") {
      setError(
        "GitHub OAuth not configured. Please use the token option below."
      );
      setShowTokenInput(true);
      return;
    }

    const REDIRECT_URI = `${process.env.NEXT_PUBLIC_FRONTEND_URL}/auth/callback`;
    const SCOPES = "repo user admin:repo_hook";
    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${encodeURIComponent(
      REDIRECT_URI
    )}&scope=${encodeURIComponent(SCOPES)}`;

    window.location.href = githubAuthUrl;
  };

  const handleBackToOptions = () => {
    setShowTokenInput(false);
    setToken("");
    setError(null);
  };

  // Show loading state while checking authentication
  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
        <div className="w-full max-w-md mx-auto">
          <div className="text-center space-y-4">
            <div className="w-20 h-20 bg-gradient-to-br from-black to-gray-800 rounded-2xl flex items-center justify-center mx-auto shadow-xl">
              <Fingerprint className="w-10 h-10 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">
                Cipher
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
  if (user && !isLoading) {
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

  // Token input screen
  if (showTokenInput) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
        <div className="w-full max-w-md mx-auto space-y-6">
          {/* Header */}
          <div className="text-center space-y-4">
            <div className="w-20 h-20 bg-gradient-to-br from-black to-gray-800 rounded-2xl flex items-center justify-center mx-auto shadow-xl">
              <Fingerprint className="w-10 h-10 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">
                Personal Access Token
              </h1>
              <p className="text-muted-foreground">
                Enter your GitHub personal access token to sign in
              </p>
            </div>
          </div>

          <Card className="border border-border shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Settings className="w-5 h-5" />
                <span>Token Authentication</span>
              </CardTitle>
              <CardDescription>
                You can create a personal access token in your GitHub settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Personal Access Token
                </label>
                <input
                  type="password"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-ring focus:border-transparent"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && token.trim()) {
                      handleTokenConnect();
                    }
                  }}
                />
                <p className="text-xs text-muted-foreground">
                  Required scopes:{" "}
                  <code className="bg-muted px-1 rounded">repo</code>,{" "}
                  <code className="bg-muted px-1 rounded">user</code>
                </p>
              </div>

              <div className="space-y-3">
                <Button
                  onClick={() => handleTokenConnect()}
                  disabled={isLoading || !token.trim()}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Signing in...
                    </>
                  ) : (
                    <>
                      <Github className="w-4 h-4 mr-2" />
                      Sign In
                    </>
                  )}
                </Button>

                <Button
                  variant="outline"
                  onClick={handleBackToOptions}
                  disabled={isLoading}
                  className="w-full"
                >
                  Back to Options
                </Button>
              </div>
            </CardContent>
          </Card>

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

  // Main sign-in screen
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
      <div className="w-full max-w-md mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="w-20 h-20 bg-gradient-to-br from-black to-gray-800 rounded-2xl flex items-center justify-center mx-auto shadow-xl">
            <Fingerprint className="w-10 h-10 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Sign in to Cipher
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
                  disabled={isLoading}
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
