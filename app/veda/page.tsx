"use client";
import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { LoadingSpinner } from "@/components/ui/loading";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import {
  Flower,
  MessageCircle,
  Plus,
  Pencil,
  Minus,
  ArrowRight,
  Circle,
  FolderOpen,
  GitPullRequest,
  ChevronRight,
  Ban,
} from "lucide-react";
import RepoDropdown from "@/components/cipher/RepoDropdown";
import PullRequestsDropdown from "@/components/veda/PullRequestsDropdown";
import { GitHubComment, GitHubFileChange, GitHubPullRequest, GitHubRepository } from "@/lib/interface/github-interface";
import { GitHubAPI } from "@/lib/api/github-api";
import Image from "next/image";

export default function Veda() {
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

  // Fetch user repositories on component mount
  useEffect(() => {
    fetchUserRepositories();
  }, []);

  // Fetch user repositories
  const fetchUserRepositories = async () => {
    try {
      setLoading(true);
      setRepoError(null);
      const response = await GitHubAPI.getRepositories();
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
    await fetchPullRequests(repo);
  };

  // Fetch pull requests for selected repository
  const fetchPullRequests = async (repo: GitHubRepository) => {
    try {
      setLoading(true);
      setPrError(null);
      const repoOwner = repo.full_name.split("/")[0];
      const response = await GitHubAPI.getPullRequests({
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
      const response = await GitHubAPI.getPullRequestFiles({
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

  // Fetch comments for selected pull request
  const fetchComments = async (pr: GitHubPullRequest) => {
    try {
      const response = await GitHubAPI.getPullRequestComments({
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
    if (!newComment.trim() || !selectedPR) return;

    try {
      setLoading(true);
      const response = await GitHubAPI.postPullRequestComment({
        pr_id: selectedPR.id,
        repo_owner: selectedPR.repository.owner,
        repo_name: selectedPR.repository.name,
        body: newComment,
      });
      setComments([...comments, response.comment]);
      setNewComment("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to post comment");
      console.error("Error posting comment:", err);
    } finally {
      setLoading(false);
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

  // Get language color for repository
  const getLanguageColor = (language: string | null) => {
    if (!language) return "bg-gray-400";

    const colors: Record<string, string> = {
      JavaScript: "bg-yellow-400",
      TypeScript: "bg-blue-400",
      Python: "bg-green-400",
      Java: "bg-orange-400",
      "C++": "bg-blue-600",
      C: "bg-gray-600",
      "C#": "bg-purple-400",
      Go: "bg-cyan-400",
      Rust: "bg-orange-600",
      PHP: "bg-indigo-400",
      Ruby: "bg-red-400",
      Swift: "bg-orange-500",
      Kotlin: "bg-purple-600",
      Dart: "bg-blue-500",
      HTML: "bg-orange-500",
      CSS: "bg-blue-500",
      Shell: "bg-gray-500",
    };

    return colors[language] || "bg-gray-400";
  };

  // File status utilities
  const getFileStatusColor = (status: string) => {
    switch (status) {
      case "added":
        return "bg-green-100 text-green-800 border-green-300";
      case "modified":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "removed":
        return "bg-red-100 text-red-800 border-red-300";
      case "renamed":
        return "bg-blue-100 text-blue-800 border-blue-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getFileCardBorder = (status: string) => {
    switch (status) {
      case "added":
        return "border-l-4 border-l-green-500";
      case "modified":
        return "border-l-4 border-l-yellow-500";
      case "removed":
        return "border-l-4 border-l-red-500";
      case "renamed":
        return "border-l-4 border-l-blue-500";
      default:
        return "border-l-4 border-l-gray-500";
    }
  };

  const getFileStatusIcon = (status: string) => {
    switch (status) {
      case "added":
        return <Plus className="w-3 h-3" />;
      case "modified":
        return <Pencil className="w-3 h-3" />;
      case "removed":
        return <Minus className="w-3 h-3" />;
      case "renamed":
        return <ArrowRight className="w-3 h-3" />;
      default:
        return <Circle className="w-3 h-3" />;
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
                getLanguageColor={getLanguageColor}
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
                    <p className="text-gray-700 font-medium">
                      Loading file changes...
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-6">
                  <div className="space-y-4">
                    {fileChanges.map((file, index) => (
                      <div
                        key={index}
                        className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow"
                      >
                        {/* File Header */}
                        <div
                          className={`px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors ${getFileCardBorder(
                            file.status
                          ).replace("border-l-4", "border-t-4")}`}
                          onClick={() => toggleFileExpansion(index)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <ChevronRight
                                className={`w-4 h-4 text-gray-500 transition-transform duration-200 ${
                                  expandedFiles.has(index) ? "rotate-90" : ""
                                }`}
                              />
                              <span
                                className={`inline-flex items-center justify-center w-7 h-7 rounded-md text-sm font-bold ${
                                  file.status === "added"
                                    ? "bg-green-600 text-white"
                                    : file.status === "modified"
                                    ? "bg-yellow-400 text-white"
                                    : file.status === "removed"
                                    ? "bg-red-600 text-white"
                                    : file.status === "renamed"
                                    ? "bg-blue-600 text-white"
                                    : "bg-gray-600 text-white"
                                }`}
                              >
                                {getFileStatusIcon(file.status)}
                              </span>
                              <div className="flex flex-col">
                                <span className="font-mono text-sm font-medium text-gray-900">
                                  {file.filename}
                                </span>
                                <span className="text-xs text-gray-500">
                                  {file.status === "renamed"
                                    ? "renamed"
                                    : `${file.changes} changes`}
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center space-x-3">
                              <div className="flex items-center space-x-2">
                                {file.additions > 0 && (
                                  <span className="text-green-600 text-sm font-medium">
                                    +{file.additions}
                                  </span>
                                )}
                                {file.deletions > 0 && (
                                  <span className="text-red-600 text-sm font-medium">
                                    -{file.deletions}
                                  </span>
                                )}
                              </div>
                              <Badge
                                variant="secondary"
                                className={`${getFileStatusColor(
                                  file.status
                                )} text-xs`}
                              >
                                {file.status}
                              </Badge>
                            </div>
                          </div>
                        </div>

                        {/* File Content */}
                        {file.patch && (
                          <div
                            className={`bg-white transition-all duration-300 ease-in-out overflow-hidden ${
                              expandedFiles.has(index)
                                ? "max-h-[1000px] opacity-100"
                                : "max-h-0 opacity-0"
                            }`}
                          >
                            <div className="border-t border-gray-200">
                              <table className="w-full text-xs font-mono">
                                <tbody>
                                  {file.patch.split("\n").map((line, idx) => {
                                    let lineClass = "";
                                    let bgClass = "";
                                    let borderClass = "";
                                    const isNoNewline = line.startsWith("\\");

                                    if (line.startsWith("+")) {
                                      bgClass = "bg-green-50";
                                      borderClass =
                                        "border-l-4 border-green-400";
                                      lineClass = "text-green-800";
                                    } else if (line.startsWith("-")) {
                                      bgClass = "bg-red-50";
                                      borderClass = "border-l-4 border-red-400";
                                      lineClass = "text-red-800";
                                    } else if (line.startsWith("@@")) {
                                      bgClass = "bg-blue-50";
                                      borderClass =
                                        "border-l-4 border-blue-400";
                                      lineClass = "text-blue-800 font-semibold";
                                    } else if (isNoNewline) {
                                      bgClass = "bg-gray-50";
                                      borderClass =
                                        "border-l-4 border-gray-300";
                                      lineClass =
                                        "text-gray-500 text-xs italic";
                                    } else {
                                      bgClass = "bg-white";
                                      lineClass = "text-gray-700";
                                    }

                                    return (
                                      <tr
                                        key={idx}
                                        className={`${bgClass} hover:bg-gray-50`}
                                      >
                                        <td
                                          className={`px-2 py-1 text-right text-gray-400 select-none w-12 ${borderClass}`}
                                        >
                                          {!isNoNewline && idx + 1}
                                        </td>
                                        <td
                                          className={`px-4 py-1 ${lineClass} whitespace-pre-wrap`}
                                        >
                                          {isNoNewline ? (
                                            <div className="flex items-center gap-2">
                                              <Ban className="w-3 h-3 text-gray-400" />
                                              <span className="text-gray-500 text-xs">
                                                No newline at end of file
                                              </span>
                                            </div>
                                          ) : (
                                            line
                                          )}
                                        </td>
                                      </tr>
                                    );
                                  })}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
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
            <div className="h-full flex flex-col bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="flex-1 overflow-y-auto p-6 rounded-t-xl">
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
                        No comments yet. Ask Veda questions about this pull
                        request using the chat below
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {comments.map((comment) => (
                      <div
                        key={comment.id}
                        className="bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-start space-x-3">
                          <Avatar className="w-9 h-9">
                            <Image
                              src={comment.user.avatar_url}
                              alt={comment.user.login}
                              className="rounded-full"
                              width="100"
                            />
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className="font-semibold text-gray-900">
                                {comment.user.login}
                              </span>
                              <span className="text-xs text-gray-500">
                                {new Date(
                                  comment.created_at
                                ).toLocaleDateString()}
                              </span>
                            </div>
                            <div className="text-gray-700 text-sm leading-relaxed">
                              <p className="whitespace-pre-wrap">
                                {comment.body}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Chat Interface */}
              <div className="border-t border-gray-100 p-4 bg-white rounded-b-xl">
                <div className="space-y-3">
                  <Textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder={
                      !selectedPR
                        ? "Select a pull request to ask Veda questions..."
                        : "Ask Veda anything about this pull request..."
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
                    <Flower className="w-4 h-4 mr-2" />
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
