"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { LoadingSpinner, LoadingCard } from "@/components/ui/loading";
import { StatusIndicator, StatusBadge } from "@/components/ui/status";
import { validateGitHubUrl } from "@/lib/api";
import { 
  Github, 
  Plus, 
  ExternalLink, 
  Star, 
  GitFork, 
  Clock, 
  Lock, 
  Globe,
  AlertCircle,
  CheckCircle,
  Settings,
  Link
} from "lucide-react";

interface RepositorySelectorProps {
  onRepoSelect: (repo: string) => void;
}

interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  updated_at: string;
  private: boolean;
}

interface GitHubUser {
  login: string;
  avatar_url: string;
  name: string | null;
}

export default function RepositorySelector({ onRepoSelect }: RepositorySelectorProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [repositories, setRepositories] = useState<GitHubRepo[]>([]);
  const [user, setUser] = useState<GitHubUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showTokenInput, setShowTokenInput] = useState(false);
  const [token, setToken] = useState("");
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [repoUrl, setRepoUrl] = useState("");

  const GITHUB_CLIENT_ID = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID;

  const handleTokenConnect = useCallback(async (providedToken?: string) => {
    const activeToken = providedToken || token;
    if (!activeToken.trim()) {
      setError("Please enter a GitHub token");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Verify token and get user info
      const userResponse = await fetch("https://api.github.com/user", {
        headers: {
          Authorization: `token ${activeToken}`,
          Accept: "application/vnd.github.v3+json",
        },
      });

      if (!userResponse.ok) {
        throw new Error("Invalid token or API error");
      }

      const userData = await userResponse.json();
      setUser(userData);

      // Fetch repositories
      const reposResponse = await fetch(
        "https://api.github.com/user/repos?sort=updated&per_page=50",
        {
          headers: {
            Authorization: `token ${activeToken}`,
            Accept: "application/vnd.github.v3+json",
          },
        }
      );

      if (!reposResponse.ok) {
        throw new Error("Failed to fetch repositories");
      }

      const reposData = await reposResponse.json();
      setRepositories(reposData);
      setIsConnected(true);
      localStorage.setItem("github_token", activeToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      // If there's an error, remove the invalid token
      localStorage.removeItem("github_token");
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  // Check for stored GitHub token on component mount
  useEffect(() => {
    const checkStoredAuth = async () => {
      setIsCheckingAuth(true);
      const storedToken = localStorage.getItem("github_token");
      
      if (storedToken) {
        setToken(storedToken);
        await handleTokenConnect(storedToken);
      }
      
      setIsCheckingAuth(false);
    };

    checkStoredAuth();
  }, [handleTokenConnect]);

  const handleGitHubAuth = () => {
    // Check if GitHub OAuth is properly configured
    if (!GITHUB_CLIENT_ID || GITHUB_CLIENT_ID.trim() === '') {
      setError("GitHub OAuth not configured. Please use the token option below.");
      setShowTokenInput(true);
      return;
    }

    const REDIRECT_URI = "http://localhost:3000/auth/callback";
    const SCOPES = "repo user";
    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&scope=${encodeURIComponent(SCOPES)}`;
    
    console.log('Redirecting to GitHub OAuth:', githubAuthUrl);
    window.location.href = githubAuthUrl;
  };

  const handleDisconnect = () => {
    setIsConnected(false);
    setToken("");
    setRepositories([]);
    setUser(null);
    setError(null);
    setShowTokenInput(false);
    setShowUrlInput(false);
    setRepoUrl("");
    localStorage.removeItem("github_token");
  };

  const handleUrlSubmit = () => {
    if (!repoUrl.trim()) {
      setError("Please enter a repository URL");
      return;
    }

    if (!validateGitHubUrl(repoUrl)) {
      setError("Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)");
      return;
    }

    onRepoSelect(repoUrl);
  };

  const getLanguageColor = (language: string | null) => {
    if (!language) return "bg-gray-500";
    const colors: Record<string, string> = {
      TypeScript: "bg-blue-500",
      JavaScript: "bg-yellow-500",
      Python: "bg-green-500",
      Java: "bg-red-500",
      "C++": "bg-purple-500",
      Go: "bg-cyan-500",
      Rust: "bg-orange-500",
      PHP: "bg-indigo-500",
      Ruby: "bg-red-400",
      Swift: "bg-orange-400",
    };
    return colors[language] || "bg-gray-500";
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffInDays === 0) return "today";
    if (diffInDays === 1) return "yesterday";
    if (diffInDays < 7) return `${diffInDays} days ago`;
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
    return `${Math.floor(diffInDays / 30)} months ago`;
  };

  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  // Show loading state while checking authentication
  if (isCheckingAuth) {
    return (
      <div className="space-y-6">
        <div className="text-center space-y-4">
          <div className="w-20 h-20 bg-gradient-to-br from-black to-gray-800 rounded-2xl flex items-center justify-center mx-auto shadow-xl">
            <Github className="w-10 h-10 text-white" />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-foreground mb-2">
              Whisper AI Assistant
            </h2>
            <div className="flex items-center justify-center space-x-2">
              <LoadingSpinner size="sm" />
              <p className="text-lg text-muted-foreground">
                Checking authentication status...
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Welcome screen for non-connected users (only shown after auth check is complete)
  if (!isConnected && !showTokenInput && !showUrlInput) {
    return (
      <div className="space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-4">
          <div className="w-20 h-20 bg-gradient-to-br from-black to-gray-800 rounded-2xl flex items-center justify-center mx-auto shadow-xl">
            <Github className="w-10 h-10 text-white" />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-foreground mb-2">
              Connect Your Repository
            </h2>
            <p className="text-lg text-muted-foreground max-w-4xl mx-auto">
              Get started by connecting your GitHub repository or providing a direct URL to begin AI-powered code analysis
            </p>
          </div>
        </div>

        {/* Connection Options */}
        <div className="grid md:grid-cols-2 gap-6 max-w-6xl mx-auto">
          {/* GitHub OAuth */}
          <Card className="bg-card border border-border rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 cursor-pointer group">
            <CardHeader className="text-center pb-4">
              <div className="w-12 h-12 bg-black rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                <Github className="w-6 h-6 text-white" />
              </div>
              <CardTitle className="flex items-center justify-center space-x-2">
                <span>GitHub Account</span>
                <StatusBadge status="info" showIcon={false}>Recommended</StatusBadge>
              </CardTitle>
              <CardDescription>
                Connect with your GitHub account to access all your repositories
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
                    <span>Automatic authentication</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Secure OAuth flow</span>
                  </li>
                </ul>
                <Button onClick={handleGitHubAuth} className="w-full bg-gradient-to-r from-black to-gray-800 hover:from-gray-900 hover:to-gray-700 text-white">
                  <Github className="w-4 h-4 mr-2" />
                  Connect GitHub
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowTokenInput(true)}
                  className="w-full"
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Use Personal Token
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Direct URL */}
          <Card className="bg-card border border-border rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 cursor-pointer group">
            <CardHeader className="text-center pb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                <Link className="w-6 h-6 text-white" />
              </div>
              <CardTitle>Direct URL</CardTitle>
              <CardDescription>
                Provide a direct link to any public GitHub repository
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-4">
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>No authentication required</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Works with public repos</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Quick and simple</span>
                  </li>
                </ul>
                <Button
                  variant="outline"
                  onClick={() => setShowUrlInput(true)}
                  className="w-full"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Enter Repository URL
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
    );
  }

  // Token input screen
  if (showTokenInput && !isConnected) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-foreground mb-2">GitHub Personal Access Token</h2>
          <p className="text-muted-foreground">
            Enter your GitHub personal access token to connect your repositories
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="w-5 h-5" />
              <span>Token Configuration</span>
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
              />
              <p className="text-xs text-muted-foreground">
                Required scopes: <code className="bg-muted px-1 rounded">repo</code>, <code className="bg-muted px-1 rounded">user</code>
              </p>
            </div>

            <div className="flex space-x-3">
              <Button
                onClick={() => handleTokenConnect()}
                disabled={isLoading || !token.trim()}
                className="flex-1"
              >
                {isLoading ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Github className="w-4 h-4 mr-2" />
                    Connect
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowTokenInput(false);
                  setToken("");
                  setError(null);
                }}
              >
                Cancel
              </Button>
            </div>

            <div className="pt-4 border-t">
              <a
                href="https://github.com/settings/tokens/new?scopes=repo,user&description=Whisper%20AI%20Assistant"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-1 text-sm text-primary hover:underline"
              >
                <ExternalLink className="w-4 h-4" />
                <span>Create a new token on GitHub</span>
              </a>
            </div>
          </CardContent>
        </Card>

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
    );
  }

  // URL input screen
  if (showUrlInput) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-foreground mb-2">Repository URL</h2>
          <p className="text-muted-foreground">
            Enter the URL of the GitHub repository you want to analyze
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Link className="w-5 h-5" />
              <span>Repository URL</span>
            </CardTitle>
            <CardDescription>
              Paste the GitHub repository URL here
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                GitHub Repository URL
              </label>
              <input
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repository"
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-ring focus:border-transparent"
              />
              <p className="text-xs text-muted-foreground">
                Example: https://github.com/facebook/react
              </p>
            </div>

            <div className="flex space-x-3">
              <Button
                onClick={handleUrlSubmit}
                disabled={!repoUrl.trim()}
                className="flex-1"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Analyze Repository
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowUrlInput(false);
                  setRepoUrl("");
                  setError(null);
                }}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>

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
    );
  }

  // Connected state - show repositories
  if (isConnected && user) {
    return (
      <div className="space-y-6">
        {/* User Info Header */}
        <Card className="border-border bg-card/50 backdrop-blur-sm">
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-5">
                <Avatar className="w-14 h-14 ring-2 ring-border shadow-sm">
                  <AvatarImage src={user.avatar_url} alt={user.login} className="object-cover" />
                  <AvatarFallback className="bg-primary/10 text-primary font-semibold text-lg">
                    {user.login.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-semibold text-foreground">
                      {user.name || user.login}
                    </h3>
                    <StatusIndicator status="online" label="Connected" />
                  </div>
                  <p className="text-sm text-muted-foreground font-medium">@{user.login}</p>
                  <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                    <Github className="w-3 h-3" />
                    <span>GitHub Account</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowUrlInput(true)}
                  className="hover:bg-muted/50 transition-colors"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add URL
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleDisconnect}
                  className="hover:bg-destructive/10 hover:text-destructive hover:border-destructive/20 transition-colors"
                >
                  Disconnect
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Loading State */}
        {isLoading && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <LoadingCard key={i} title="Loading repository..." />
            ))}
          </div>
        )}

        {/* Repositories Grid */}
        {!isLoading && repositories.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-foreground">
                Your Repositories ({repositories.length})
              </h3>
            </div>
            
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {repositories.map((repo) => (
                <Card 
                  key={repo.id} 
                  className="bg-card border border-border rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 cursor-pointer group"
                  onClick={() => onRepoSelect(`https://github.com/${repo.full_name}`)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1 min-w-0 flex-1">
                        <CardTitle className="text-base group-hover:text-primary transition-colors flex items-center space-x-2">
                          <span className="truncate">{repo.name}</span>
                          {repo.private && <Lock className="w-3 h-3 text-muted-foreground shrink-0" />}
                          {!repo.private && <Globe className="w-3 h-3 text-muted-foreground shrink-0" />}
                        </CardTitle>
                        <p className="text-xs text-muted-foreground">@{repo.full_name.split('/')[0]}</p>
                      </div>
                      <ExternalLink className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                    </div>
                  </CardHeader>
                  
                  <CardContent className="space-y-3">
                    {repo.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {repo.description}
                      </p>
                    )}
                    
                    <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                      {repo.language && (
                        <div className="flex items-center space-x-1">
                          <div className={`w-2 h-2 rounded-full ${getLanguageColor(repo.language)}`} />
                          <span>{repo.language}</span>
                        </div>
                      )}
                      
                      <div className="flex items-center space-x-1">
                        <Star className="w-3 h-3" />
                        <span>{formatNumber(repo.stargazers_count)}</span>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <GitFork className="w-3 h-3" />
                        <span>{formatNumber(repo.forks_count)}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>Updated {formatDate(repo.updated_at)}</span>
                      </div>
                      <StatusBadge 
                        status={repo.private ? "warning" : "success"} 
                        showIcon={false}
                      >
                        {repo.private ? "Private" : "Public"}
                      </StatusBadge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && repositories.length === 0 && (
          <Card>
            <CardContent className="pt-6 text-center">
              <div className="space-y-3">
                <Github className="w-12 h-12 text-muted-foreground mx-auto" />
                <div>
                  <h3 className="font-medium text-foreground">No repositories found</h3>
                  <p className="text-sm text-muted-foreground">
                    You don't have any repositories in your GitHub account
                  </p>
                </div>
                <Button
                  variant="outline"
                  onClick={() => setShowUrlInput(true)}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Repository URL
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

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
    );
  }

  // Default loading state
  return (
    <div className="space-y-6">
      <LoadingCard title="Connecting to GitHub..." description="Please wait while we establish the connection" />
    </div>
  );
}
