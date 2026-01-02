"use client";
import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Avatar } from "@/components/ui/avatar";
import { LoadingSpinner } from "@/components/ui/loading";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import {
  Flower,
  MessageCircle,
  FolderOpen,
  GitPullRequest,
} from "lucide-react";
import RepoDropdown from "@/components/cipher/RepoDropdown";
import PullRequestsDropdown from "@/components/veda/PullRequestsDropdown";
import File from "@/components/veda/File";
import {
  GitHubComment,
  GitHubFileChange,
  GitHubPullRequest,
  GitHubRepository,
} from "@/lib/interface/github-interface";
import { GitHubAPI } from "@/lib/api/github-api";
import { VedaAPI } from "@/lib/api/veda-api";
import { useAuth } from "@/context/auth-context";
import Image from "next/image";

export default function Veda() {
  // Auth context
  const { user, getToken } = useAuth();

  // Repository state
  const [repositories, setRepositories] = useState<GitHubRepository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<GitHubRepository | null>(
    null
  );
  const [showRepoDropdown, setShowRepoDropdown] = useState(false);
  const [showRepoDropdownContent, setShowRepoDropdownContent] = useState(false);
  const [repoError, setRepoError] = useState<string | null>(null);
  const repoDropdownTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Pull request state
  const [pullRequests, setPullRequests] = useState<GitHubPullRequest[]>([]);
  const [selectedPR, setSelectedPR] = useState<GitHubPullRequest | null>(null);
  const [showPRDropdown, setShowPRDropdown] = useState(false);
  const [showPRDropdownContent, setShowPRDropdownContent] = useState(false);
  const [prError, setPrError] = useState<string | null>(null);
  const prDropdownTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Analysis state
  const [fileChanges, setFileChanges] = useState<GitHubFileChange[]>([]);
  const [comments, setComments] = useState<GitHubComment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedFiles, setExpandedFiles] = useState<Set<number>>(new Set());

  // WebSocket state for Veda analysis
  const [vedaWebSocket, setVedaWebSocket] = useState<WebSocket | null>(null);
  const [vedaAnalysisProgress, setVedaAnalysisProgress] = useState<string>("");
  const [vedaAnalysisCompleted, setVedaAnalysisCompleted] = useState<boolean>(false);

  // Fetch user repositories on component mount
  useEffect(() => {
    fetchUserRepositories();
  }, []);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (vedaWebSocket) {
        vedaWebSocket.close();
      }
    };
  }, [vedaWebSocket]);

  // Fetch user repositories
  const fetchUserRepositories = async () => {
    try {
      setLoading(true);
      setRepoError(null);
      const token = getToken();
      if (!token) {
        throw new Error("No authentication token found");
      }
      const response = await GitHubAPI.getRepositories({ token });
      setRepositories(response.repositories || []);
    } catch (err) {
      setRepoError(
        err instanceof Error ? err.message : "Failed to fetch repositories"
      );
      console.error("Error fetching repositories:", err);
    } finally {
      setLoading(false);
    }
  };

  // Handle repository selection
  const handleRepoSelection = async (repo: GitHubRepository) => {
    setSelectedRepo(repo);
    setSelectedPR(null);
    setFileChanges([]);
    setComments([]);
    setPullRequests([]);
    setVedaAnalysisCompleted(false); // Reset analysis completion state
    setVedaAnalysisProgress(""); // Reset analysis progress
    
    // Close existing WebSocket connection
    if (vedaWebSocket) {
      vedaWebSocket.close();
      setVedaWebSocket(null);
    }
    
    await fetchPullRequests(repo);
  };

  // Fetch pull requests for selected repository
  const fetchPullRequests = async (repo: GitHubRepository) => {
    try {
      setLoading(true);
      setPrError(null);
      const token = getToken();
      if (!token) {
        throw new Error("No authentication token found");
      }
      const repoOwner = repo.full_name.split("/")[0];
      const response = await GitHubAPI.getPullRequests({
        token,
        repo_owner: repoOwner,
        repo_name: repo.name,
        state: "all",
      });
      setPullRequests(response.items || []);
    } catch (err) {
      setPrError(
        err instanceof Error ? err.message : "Failed to fetch pull requests"
      );
      console.error("Error fetching pull requests:", err);
    } finally {
      setLoading(false);
    }
  };

  // Handle pull request selection
  const handlePRSelection = async (pr: GitHubPullRequest) => {
    setSelectedPR(pr);
    setExpandedFiles(new Set()); // Reset expanded files when switching PRs
    setVedaAnalysisCompleted(false); // Reset analysis completion state
    setVedaAnalysisProgress(""); // Reset analysis progress
    
    // Close existing WebSocket connection
    if (vedaWebSocket) {
      vedaWebSocket.close();
      setVedaWebSocket(null);
    }
    
    setLoading(true);
    await Promise.all([fetchFileChanges(pr), fetchComments(pr)]);
    setLoading(false);
  };

  // Toggle file expansion
  const toggleFileExpansion = (index: number) => {
    const newExpandedFiles = new Set(expandedFiles);
    if (newExpandedFiles.has(index)) {
      newExpandedFiles.delete(index);
    } else {
      newExpandedFiles.add(index);
    }
    setExpandedFiles(newExpandedFiles);
  };

  // Fetch file changes for selected pull request
  const fetchFileChanges = async (pr: GitHubPullRequest) => {
    try {
      const token = getToken();
      if (!token) {
        throw new Error("No authentication token found");
      }
      const response = await GitHubAPI.getPullRequestFiles({
        token,
        pr_id: pr.id,
        repo_owner: pr.repository.owner,
        repo_name: pr.repository.name,
      });
      const files = response.files || [];
      setFileChanges(files);

      // Expand all files by default
      const allFileIndexes = new Set(
        Array.from({ length: files.length }, (_, index) => index)
      );
      setExpandedFiles(allFileIndexes);
    } catch (err) {
      console.error("Error fetching file changes:", err);
    }
  };

  // Refresh file changes after Veda analysis completion
  const refreshFileChanges = async () => {
    if (!selectedPR) return;
    
    setLoading(true);
    setVedaAnalysisCompleted(false);
    setVedaAnalysisProgress("");
    
    try {
      await fetchFileChanges(selectedPR);
      await fetchComments(selectedPR);
    } catch (err) {
      console.error("Error refreshing file changes:", err);
      setError("Failed to refresh file changes");
    } finally {
      setLoading(false);
    }
  };

  // Fetch comments for selected pull request
  const fetchComments = async (pr: GitHubPullRequest) => {
    try {
      const token = getToken();
      if (!token) {
        throw new Error("No authentication token found");
      }
      const response = await GitHubAPI.getPullRequestComments({
        token,
        pr_id: pr.id,
        repo_owner: pr.repository.owner,
        repo_name: pr.repository.name,
      });
      setComments(response.comments || []);
    } catch (err) {
      console.error("Error fetching comments:", err);
    }
  };

  // Post comment
  const postComment = async () => {
    if (!newComment.trim() || !selectedPR || !user) return;

    const tempId = Date.now(); // Use timestamp as temporary ID
    const skeletonComment: GitHubComment = {
      id: tempId,
      body: "",
      user: {
        login: "__SKELETON__",
        avatar_url: "",
        name: "",
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      html_url: "",
    };

    // Add skeleton placeholder to UI
    const currentCommentText = newComment;
    setComments([...comments, skeletonComment]);
    setNewComment("");
    
    // Reset analysis completion state when starting new analysis
    setVedaAnalysisCompleted(false);
    setError(null);

    try {
      // Make both API calls simultaneously
      const token = getToken();
      if (!token) {
        throw new Error("No authentication token found");
      }
      
      const [githubResponse, vedaResponse] = await Promise.all([
        GitHubAPI.postPullRequestComment({
          token,
          pr_id: selectedPR.id,
          repo_owner: selectedPR.repository.owner,
          repo_name: selectedPR.repository.name,
          body: currentCommentText,
        }),
        VedaAPI.analyzeComment({
          pr_id: selectedPR.id,
          repo_owner: selectedPR.repository.owner,
          repo_name: selectedPR.repository.name,
          user_comment: currentCommentText,
          user_login: user.login,
        })
      ]);

      // Replace skeleton comment with real comment
      setComments((prevComments) =>
        prevComments.map((comment) =>
          comment.id === tempId ? githubResponse.comment : comment
        )
      );

      // Connect to WebSocket for real-time updates if available
      if (vedaResponse.websocket_url) {
        connectToVedaWebSocket(vedaResponse.task_id, vedaResponse.websocket_url);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to post comment");
      console.error("Error posting comment:", err);

      // Remove skeleton comment on error
      setComments((prevComments) =>
        prevComments.filter((comment) => comment.id !== tempId)
      );

      // Restore the comment text so user can try again
      setNewComment(currentCommentText);
    } finally {
      setLoading(false);
    }
  };

  // Connect to Veda WebSocket for analysis updates
  const connectToVedaWebSocket = (taskId: string, websocketUrl: string) => {
    try {
      // Close existing connection if any
      if (vedaWebSocket) {
        vedaWebSocket.close();
      }

      const ws = new WebSocket(websocketUrl);

      ws.onopen = () => {
        console.log("Connected to Veda analysis WebSocket");
        setVedaAnalysisProgress("Connected to Veda analysis...");
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log("Veda analysis update:", message);

          if (message.type === "tool_started" && message.tool?.name) {
            setVedaAnalysisProgress(`Starting ${message.tool.name}...`);
          } else if (message.type === "tool_completed" && message.tool?.name) {
            setVedaAnalysisProgress(`Completed ${message.tool.name}`);
          } else if (message.type === "progress" && message.progress) {
            // Check if there's tool information in progress messages
            if (message.tool?.name) {
              setVedaAnalysisProgress(`${message.tool.name}: ${message.progress.current_step}`);
            } else {
              setVedaAnalysisProgress(message.progress.current_step);
            }
          } else if (message.type === "analysis_completed") {
            setVedaAnalysisProgress("Analysis completed!");
            setVedaAnalysisCompleted(true);
            // Optionally refresh comments to see any new ones from Veda
            if (selectedPR) {
              fetchComments(selectedPR);
            }
          } else if (message.type === "analysis_error") {
            setVedaAnalysisProgress("Analysis failed");
            setVedaAnalysisCompleted(false);
            setError("Veda analysis failed: " + (message.error?.message || "Unknown error"));
          }
        } catch (err) {
          console.error("Error parsing Veda WebSocket message:", err);
        }
      };

      ws.onclose = () => {
        console.log("Veda analysis WebSocket closed");
        // Only clear progress if analysis hasn't completed yet
        setVedaAnalysisCompleted(currentCompleted => {
          if (!currentCompleted) {
            setVedaAnalysisProgress("");
          }
          return currentCompleted;
        });
      };

      ws.onerror = (error) => {
        console.error("Veda WebSocket error:", error);
        setError("Connection to Veda analysis failed");
      };

      setVedaWebSocket(ws);
    } catch (err) {
      console.error("Failed to connect to Veda WebSocket:", err);
      setError("Failed to connect to analysis updates");
    }
  };

  // Toggle repository dropdown
  const toggleRepoDropdown = () => {
    if (showRepoDropdown) {
      if (repoDropdownTimeoutRef.current) {
        clearTimeout(repoDropdownTimeoutRef.current);
        repoDropdownTimeoutRef.current = null;
      }
      setShowRepoDropdown(false);
      setShowRepoDropdownContent(false);
    } else {
      setShowRepoDropdown(true);
      repoDropdownTimeoutRef.current = setTimeout(() => {
        setShowRepoDropdownContent(true);
      }, 150);
    }
  };

  // Toggle pull request dropdown
  const togglePRDropdown = () => {
    if (showPRDropdown) {
      if (prDropdownTimeoutRef.current) {
        clearTimeout(prDropdownTimeoutRef.current);
        prDropdownTimeoutRef.current = null;
      }
      setShowPRDropdown(false);
      setShowPRDropdownContent(false);
    } else {
      setShowPRDropdown(true);
      prDropdownTimeoutRef.current = setTimeout(() => {
        setShowPRDropdownContent(true);
      }, 150);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 p-4">
      <div className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1 font-semibold text-lg">
            <Flower /> Veda
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <RepoDropdown
                repositories={repositories}
                selectedRepo={selectedRepo}
                showDropdown={showRepoDropdown}
                showDropdownContent={showRepoDropdownContent}
                repoError={repoError}
                dropdownTimeoutRef={repoDropdownTimeoutRef}
                toggleDropdown={toggleRepoDropdown}
                setSelectedRepo={handleRepoSelection}
                setShowDropdown={setShowRepoDropdown}
                setShowDropdownContent={setShowRepoDropdownContent}
              />

              <PullRequestsDropdown
                pullRequests={pullRequests}
                selectedPR={selectedPR}
                showDropdown={showPRDropdown}
                showDropdownContent={showPRDropdownContent}
                prError={prError}
                dropdownTimeoutRef={prDropdownTimeoutRef}
                toggleDropdown={togglePRDropdown}
                setSelectedPR={handlePRSelection}
                setShowDropdown={setShowPRDropdown}
                setShowDropdownContent={setShowPRDropdownContent}
                disabled={!selectedRepo}
              />
            </div>
          </div>
        </div>
      </div>

      <ResizablePanelGroup direction="horizontal" className="flex-1 gap-2">
        {/* Left Side - File Changes */}
        <ResizablePanel defaultSize={75} minSize={50}>
          <div className="h-full bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="h-full overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
              {!selectedRepo ? (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center max-w-md mx-auto">
                    <div className="relative mb-8">
                      <div className="absolute inset-0 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full blur-2xl opacity-50 animate-pulse"></div>
                      <div className="relative bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-6 border border-blue-100/50">
                        <FolderOpen className="w-12 h-12 mx-auto text-blue-500" />
                      </div>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-3">
                      Choose your repository
                    </h3>
                    <p className="text-gray-600 leading-relaxed text-sm">
                      Select a repository from the dropdown above to start
                      exploring pull requests and analyzing code changes
                    </p>
                  </div>
                </div>
              ) : !selectedPR ? (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center max-w-md mx-auto">
                    <div className="relative mb-8">
                      <div className="absolute inset-0 bg-gradient-to-r from-green-100 to-teal-100 rounded-full blur-2xl opacity-50 animate-pulse"></div>
                      <div className="relative bg-gradient-to-r from-green-50 to-teal-50 rounded-2xl p-6 border border-green-100/50">
                        <GitPullRequest className="w-12 h-12 mx-auto text-green-500" />
                      </div>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-3">
                      Select a pull request
                    </h3>
                    <p className="text-gray-600 leading-relaxed text-sm">
                      Choose a pull request to view detailed file changes,
                      diffs, and start conversations with Veda
                    </p>
                  </div>
                </div>
              ) : loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="flex flex-col items-center justify-center">
                    <div className="relative mb-4">
                      <div className="absolute inset-0 bg-gradient-to-r from-violet-100 to-blue-100 rounded-full blur-xl opacity-50"></div>
                      <div className="relative">
                        <LoadingSpinner />
                      </div>
                    </div>
                    <p className="text-gray-500 font-medium">
                      Loading file changes...
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-4">
                  <div className="space-y-4">
                    {fileChanges.map((file, index) => (
                      <File
                        key={index}
                        file={file}
                        index={index}
                        expandedFiles={expandedFiles}
                        toggleFileExpansion={toggleFileExpansion}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle className="opacity-0 hover:opacity-0" />

        {/* Right Side - Comments and Chat */}
        <ResizablePanel defaultSize={25} minSize={25}>
          <div className="h-full">
            <div className="h-full flex flex-col rounded-xl shadow-sm border border-gray-200">
              <div className="flex-1 overflow-y-auto p-4 rounded-t-xl [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                {!selectedPR ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center max-w-sm mx-auto">
                      <div className="relative mb-6">
                        <div className="absolute inset-0 bg-gradient-to-r from-orange-100 to-pink-100 rounded-full blur-xl opacity-50 animate-pulse"></div>
                        <div className="relative bg-gradient-to-r from-orange-50 to-pink-50 rounded-xl p-5 border border-orange-100/50">
                          <MessageCircle className="w-10 h-10 mx-auto text-orange-500" />
                        </div>
                      </div>
                      <h4 className="text-lg font-semibold text-gray-900 mb-2">
                        Ready to chat
                      </h4>
                      <p className="text-gray-600 leading-relaxed text-sm">
                        Select a pull request and pull request to view comments
                        and a conversation with Veda
                      </p>
                    </div>
                  </div>
                ) : loading && comments.length === 0 ? (
                  <div className="space-y-3">
                    {/* Comment skeleton placeholders during initial load */}
                    {[1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className="bg-white border border-gray-200/60 rounded-2xl p-4"
                      >
                        <div className="flex items-start space-x-4">
                          <Skeleton className="w-11 h-11 rounded-full" />
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-3">
                              <Skeleton className="h-4 w-24" />
                              <Skeleton className="h-3 w-16" />
                            </div>
                            <div className="space-y-2">
                              <Skeleton className="h-3 w-full" />
                              <Skeleton className="h-3 w-3/4" />
                              <Skeleton className="h-3 w-1/2" />
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : comments.length === 0 ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center max-w-sm mx-auto">
                      <div className="relative mb-6">
                        <div className="absolute inset-0 bg-gradient-to-r from-indigo-100 to-purple-100 rounded-full blur-xl opacity-50 animate-pulse"></div>
                        <div className="relative bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-5 border border-indigo-100/50">
                          <MessageCircle className="w-10 h-10 mx-auto text-indigo-500" />
                        </div>
                      </div>
                      <h4 className="text-lg font-semibold text-gray-900 mb-2">
                        Start the conversation
                      </h4>
                      <p className="text-gray-600 text-sm leading-relaxed">
                        No comments yet. Interact with Veda to make changes to
                        this pull request
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {comments.map((comment) => {
                      const isSkeleton = comment.user.login === "__SKELETON__";

                      if (isSkeleton) {
                        // Render skeleton placeholder
                        return (
                          <div
                            key={comment.id}
                            className="bg-white border border-gray-200/60 rounded-2xl p-4"
                          >
                            <div className="flex items-start space-x-4">
                              <Skeleton className="w-11 h-11 rounded-full" />
                              <div className="flex-1">
                                <div className="flex items-center justify-between mb-3">
                                  <Skeleton className="h-4 w-24" />
                                  <Skeleton className="h-3 w-16" />
                                </div>
                                <div className="space-y-2">
                                  <Skeleton className="h-3 w-full" />
                                  <Skeleton className="h-3 w-3/4" />
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      }

                      // Render normal comment
                      return (
                        <div
                          key={comment.id}
                          className="group relative cursor-default bg-white border border-gray-200/60 rounded-2xl p-4 shadow-sm hover:shadow-md hover:border-gray-300/60 transition-all duration-300 ease-out"
                        >
                          {/* Subtle gradient overlay on hover */}
                          <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 to-purple-50/50 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

                          <div className="relative flex items-start space-x-4">
                            <div className="relative">
                              <Avatar className="w-11 h-11 ring-2 ring-white shadow-sm">
                                <Image
                                  src={comment.user.avatar_url}
                                  alt={comment.user.login}
                                  className="rounded-full object-cover"
                                  width="44"
                                  height="44"
                                />
                              </Avatar>
                              {/* Online indicator */}
                              <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-400 border-2 border-white rounded-full" />
                            </div>

                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between mb-1">
                                <div className="flex items-center space-x-3">
                                  <span className="font-semibold text-gray-900">
                                    {comment.user.login}
                                  </span>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <span className="text-xs text-gray-500 font-medium">
                                    {new Date(
                                      comment.created_at
                                    ).toLocaleDateString("en-US", {
                                      month: "short",
                                      day: "numeric",
                                      year: "numeric",
                                    })}
                                  </span>
                                  <span className="text-xs text-gray-400">
                                    {new Date(
                                      comment.created_at
                                    ).toLocaleTimeString("en-US", {
                                      hour: "numeric",
                                      minute: "2-digit",
                                      hour12: true,
                                    })}
                                  </span>
                                </div>
                              </div>

                              <div className="prose prose-sm max-w-none">
                                <div className="text-gray-700 leading-relaxed">
                                  <p className="whitespace-pre-wrap text-sm">
                                    {comment.body}
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Chat Interface */}
              <div className="border-t border-gray-100 p-4 bg-white rounded-b-xl">
                {/* Veda Analysis Progress */}
                {vedaAnalysisProgress && (
                  <div className={`mb-3 p-3 rounded-lg ${
                    vedaAnalysisCompleted 
                      ? 'bg-green-50 border border-green-200' 
                      : 'bg-blue-50 border border-blue-200'
                  }`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {!vedaAnalysisCompleted && (
                          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                        )}
                        {vedaAnalysisCompleted && (
                          <div className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                            <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </div>
                        )}
                        <span className={`text-sm font-medium ${
                          vedaAnalysisCompleted ? 'text-green-700' : 'text-blue-700'
                        }`}>
                          {vedaAnalysisProgress}
                        </span>
                      </div>
                      
                      {vedaAnalysisCompleted && (
                        <Button
                          onClick={refreshFileChanges}
                          disabled={loading}
                          size="sm"
                          className="bg-green-600 hover:bg-green-700 text-white text-xs px-3 py-1 h-7"
                        >
                          {loading ? "Refreshing..." : "Refresh Changes"}
                        </Button>
                      )}
                    </div>
                  </div>
                )}

                <div className="space-y-3">
                  <Textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder={
                      !selectedPR
                        ? "Select a repository and pull request to ask Veda for help..."
                        : "Ask Veda to help you make changes..."
                    }
                    disabled={!selectedPR}
                    className="min-h-[80px] rounded-xl border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 resize-none disabled:opacity-50 disabled:cursor-not-allowed"
                    data-gramm="false"
                    data-gramm_editor="false"
                    data-enable-grammarly="false"
                    autoCorrect="off"
                    autoComplete="off"
                    spellCheck="false"
                  />
                  <Button
                    onClick={postComment}
                    disabled={!selectedPR || !newComment.trim() || loading}
                    className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium py-3 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Flower className="w-4 h-4" />
                    {loading ? "Sending..." : "Ask Veda"}
                  </Button>
                  {error && (
                    <div className="text-red-500 text-sm bg-red-50 p-3 rounded-lg">
                      {error}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
