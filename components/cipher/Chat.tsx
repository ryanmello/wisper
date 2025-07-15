"use client";

import React, { useState, useRef, useEffect } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useTask } from "@/context/task-context";
import { ChevronDown, Github, AlertCircle, ArrowUpRight } from "lucide-react";

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

interface ChatProps {
  isAuthenticated: boolean;
}

export function Chat({ isAuthenticated }: ChatProps) {
  const { 
    createTask, 
    isLoading: isTaskLoading, 
    error: taskError,
    clearError
  } = useTask();
  
  const [message, setMessage] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [selectedRepo, setSelectedRepo] = useState<GitHubRepo | null>(null);
  const [repositories, setRepositories] = useState<GitHubRepo[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showDropdownContent, setShowDropdownContent] = useState(false);
  const [repoError, setRepoError] = useState<string | null>(null);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const dropdownTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      const textarea = textareaRef.current;
      textarea.style.height = "auto";
      const maxHeight = 320;
      const newHeight = Math.min(textarea.scrollHeight, maxHeight);
      textarea.style.height = `${newHeight}px`;

      // Enable scrolling when content exceeds max height
      if (textarea.scrollHeight > maxHeight) {
        textarea.style.overflow = "auto";
      } else {
        textarea.style.overflow = "hidden";
      }
    }
  }, [message]);

  // Fetch repositories from GitHub
  useEffect(() => {
    const fetchRepositories = async () => {
      if (!isAuthenticated) return;
      
      const storedToken = localStorage.getItem("github_token");
      if (!storedToken) return;

      try {
        setRepoError(null);
        const reposResponse = await fetch(
          "https://api.github.com/user/repos?sort=updated&per_page=50",
          {
            headers: {
              Authorization: `token ${storedToken}`,
              Accept: "application/vnd.github.v3+json",
            },
          }
        );

        if (reposResponse.ok) {
          const repos = await reposResponse.json();
          setRepositories(repos);
        } else {
          setRepoError("Failed to fetch repositories from GitHub");
        }
      } catch (error) {
        console.error("Failed to fetch repositories:", error);
        setRepoError("Unable to connect to GitHub. Please check your connection.");
      }
    };

    fetchRepositories();
  }, [isAuthenticated]);

  // Handle dropdown toggle with delay
  const toggleDropdown = () => {
    if (showDropdown) {
      // Close immediately
      if (dropdownTimeoutRef.current) {
        clearTimeout(dropdownTimeoutRef.current);
        dropdownTimeoutRef.current = null;
      }
      setShowDropdown(false);
      setShowDropdownContent(false);
    } else {
      // Open with delay for content
      setShowDropdown(true);
      dropdownTimeoutRef.current = setTimeout(() => {
        setShowDropdownContent(true);
      }, 200);
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        if (dropdownTimeoutRef.current) {
          clearTimeout(dropdownTimeoutRef.current);
          dropdownTimeoutRef.current = null;
        }
        setShowDropdown(false);
        setShowDropdownContent(false);
      }
    };

    if (showDropdown) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showDropdown]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (dropdownTimeoutRef.current) {
        clearTimeout(dropdownTimeoutRef.current);
      }
    };
  }, []);

  // Clear task error when user starts typing
  useEffect(() => {
    if (taskError && message.trim()) {
      clearError();
    }
  }, [message, taskError, clearError]);

  const handleSend = async () => {
    if (
      !message.trim() ||
      message.trim().length < 20 ||
      isTaskLoading ||
      !selectedRepo
    )
      return;

    try {
      const task = await createTask({
        repository_url: `https://github.com/${selectedRepo.full_name}`,
        prompt: message.trim()
      });

      if (task) {
        setMessage("");
      }
    } catch (error) {
      console.error("Error creating task:", error);
    }
  };

  const getLanguageColor = (language: string | null) => {
    if (!language) return "bg-gray-500";
    const colors: Record<string, string> = {
      TypeScript: "bg-blue-500",
      JavaScript: "bg-purple-500",
      Python: "bg-yellow-500",
      Java: "bg-orange-500",
      Go: "bg-cyan-500",
      Rust: "bg-red-500",
      "C++": "bg-green-500",
      "C#": "bg-purple-600",
      PHP: "bg-indigo-500",
      Ruby: "bg-red-600",
    };
    return colors[language] || "bg-gray-500";
  };

  const hasContent = message.trim().length >= 20;

  return (
    <div>
      {/* Error Display */}
      {taskError && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700">{taskError}</span>
          <Button
            onClick={clearError}
            variant="ghost"
            size="sm"
            className="ml-auto text-red-500 hover:text-red-700 p-1"
          >
            ✕
          </Button>
        </div>
      )}

      {/* Main Chat Input */}
      <div className="relative group">
        {/* Input Container with improved styling */}
        <div
          className={cn(
            "relative transition-all duration-300 ease-out",
            "bg-card/80 backdrop-blur-sm border-2 rounded-2xl shadow-lg",
            "hover:shadow-xl hover:shadow-primary/5",
            isFocused || hasContent
              ? "border-primary/20 shadow-xl shadow-primary/5 bg-card"
              : "border-border/60 hover:border-border"
          )}
        >
          {/* Text input area - full width */}
          <div className="p-5 pb-2">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Describe what you want to do with your repository..."
              className={cn(
                "min-h-[60px] max-h-[320px] resize-none border-0 shadow-none focus-visible:ring-0",
                "bg-transparent placeholder:text-muted-foreground/50 text-base leading-relaxed w-full",
                "selection:bg-primary/20",
                "focus:placeholder:text-muted-foreground/30 transition-colors",
                "scrollbar-thin scrollbar-thumb-muted/30 scrollbar-track-transparent hover:scrollbar-thumb-muted/50"
              )}
              data-gramm="false"
              data-gramm_editor="false"
              data-enable-grammarly="false"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
          </div>

          {/* Bottom controls section */}
          <div className="px-5 pb-2 pt-2 border-t border-border/20">
            <div className="flex items-center justify-between">
              {/* Repository Dropdown */}
              <div className="relative" ref={dropdownRef}>
                <Button
                  onClick={toggleDropdown}
                  variant="outline"
                  className={cn(
                    "cursor-pointer flex items-center gap-2 px-3 py-2 rounded-xl text-sm transition-all duration-500 ease-in-out",
                    "border border-border hover:border-border hover:bg-muted/50",
                    "justify-between h-auto",
                    // Dynamic width based on state
                    showDropdown || !selectedRepo
                      ? "min-w-[300px]"
                      : "w-auto min-w-0"
                  )}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <Github className="w-4 h-4 shrink-0" />
                    <span
                      className={cn(
                        "transition-all duration-500 ease-in-out",
                        selectedRepo && !showDropdown
                          ? "whitespace-nowrap"
                          : "truncate"
                      )}
                    >
                      {selectedRepo ? selectedRepo.name : "Select repository"}
                    </span>
                  </div>
                  <ChevronDown
                    className={cn(
                      "w-4 h-4 transition-transform duration-500 ease-in-out shrink-0",
                      showDropdown && "rotate-180"
                    )}
                  />
                </Button>

                {/* Dropdown Menu */}
                {showDropdownContent && (
                  <div className="absolute top-full left-0 mt-2 w-full max-h-60 overflow-y-auto bg-card border border-border rounded-xl shadow-lg z-50 animate-in fade-in-0 slide-in-from-top-2 duration-200">
                    <div className="p-2">
                      {repoError ? (
                        <div className="px-3 py-2 text-sm text-red-600 text-center">
                          {repoError}
                        </div>
                      ) : repositories.length === 0 ? (
                        <div className="px-3 py-2 text-sm text-muted-foreground text-center">
                          No repositories available
                        </div>
                      ) : (
                        repositories.map((repo) => (
                                                      <Button
                              key={repo.id}
                              onClick={() => {
                                setSelectedRepo(repo);
                                if (dropdownTimeoutRef.current) {
                                  clearTimeout(dropdownTimeoutRef.current);
                                  dropdownTimeoutRef.current = null;
                                }
                                setShowDropdown(false);
                                setShowDropdownContent(false);
                              }}
                              variant="ghost"
                              className={cn(
                                "cursor-pointer w-full text-left px-3 py-2 rounded-lg text-sm transition-colors h-auto",
                                "hover:bg-muted/50 flex items-center justify-between group",
                                selectedRepo?.id === repo.id &&
                                  "bg-primary/10 text-primary"
                              )}
                            >
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium truncate">
                                  {repo.name}
                                </span>
                                {repo.language && (
                                  <div className="flex items-center gap-1">
                                    <div
                                      className={cn(
                                        "w-2 h-2 rounded-full",
                                        getLanguageColor(repo.language)
                                      )}
                                    />
                                    <span className="text-xs text-muted-foreground">
                                      {repo.language}
                                    </span>
                                  </div>
                                )}
                              </div>
                              {repo.description && (
                                <p className="text-xs text-muted-foreground truncate">
                                  {repo.description}
                                </p>
                              )}
                            </div>
                          </Button>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Send Button */}
              <Button
                onClick={handleSend}
                disabled={!hasContent || isTaskLoading || !selectedRepo}
                size="icon"
                className={cn(
                  "h-10 w-10 rounded-xl transition-all duration-300 ease-out",
                  "shadow-md hover:shadow-lg border-0",
                  hasContent && !isTaskLoading && selectedRepo
                    ? "bg-primary hover:bg-primary/90 text-primary-foreground scale-100 opacity-100 hover:scale-105"
                    : "bg-muted/70 text-muted-foreground/60 scale-95 opacity-50 cursor-not-allowed hover:bg-muted/70 hover:scale-95",
                  isTaskLoading && "animate-pulse scale-100"
                )}
              >
                {isTaskLoading ? (
                  <div className="relative">
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  </div>
                ) : (
                  <ArrowUpRight className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Enhanced character count and hints */}
        <div className="flex justify-between items-center mt-3 px-1">
          <div className="flex items-center gap-3 text-xs text-muted-foreground/70">
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 text-xs bg-muted/60 rounded border border-border/40">
                ⌘ + Enter
              </kbd>
              to send
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 text-xs bg-muted/60 rounded border border-border/40">
                Enter
              </kbd>
              for new line
            </span>
          </div>
          <span
            className={cn(
              "text-xs transition-colors duration-200",
              message.length > 0
                ? "text-muted-foreground"
                : "text-muted-foreground/50"
            )}
          >
            {message.length} characters
          </span>
        </div>
      </div>
    </div>
  );
}
