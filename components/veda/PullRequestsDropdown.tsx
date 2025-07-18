import React, { useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { GitPullRequest, ChevronDown } from "lucide-react";

interface PullRequest {
  id: number;
  title: string;
  state: string;
  repository: {
    name: string;
    full_name: string;
    owner: string;
  };
  created_at: string;
  updated_at: string;
  html_url: string;
  user: {
    login: string;
    avatar_url: string;
  };
  comments: number;
  labels: Array<{ name: string; color: string }>;
}

interface PullRequestsDropdownProps {
  pullRequests: PullRequest[];
  selectedPR: PullRequest | null;
  showDropdown: boolean;
  showDropdownContent: boolean;
  prError: string | null;
  dropdownTimeoutRef: React.MutableRefObject<NodeJS.Timeout | null>;
  toggleDropdown: () => void;
  setSelectedPR: (pr: PullRequest) => void;
  setShowDropdown: (show: boolean) => void;
  setShowDropdownContent: (show: boolean) => void;
  disabled?: boolean;
}

export default function PullRequestsDropdown({
  pullRequests,
  selectedPR,
  showDropdown,
  showDropdownContent,
  prError,
  dropdownTimeoutRef,
  toggleDropdown,
  setSelectedPR,
  setShowDropdown,
  setShowDropdownContent,
  disabled = false,
}: PullRequestsDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null);

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
  }, [showDropdown, dropdownTimeoutRef, setShowDropdown, setShowDropdownContent]);

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        onClick={disabled ? undefined : toggleDropdown}
        variant="outline"
        disabled={disabled}
        className={cn(
          "cursor-pointer flex items-center gap-2 px-3 py-2 rounded-xl text-sm transition-all duration-500 ease-in-out",
          "border border-border hover:border-border hover:bg-muted/50",
          "justify-between h-auto",
          // Dynamic width based on state
          showDropdown || !selectedPR ? "min-w-[300px]" : "w-auto min-w-0",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      >
        <div className="flex items-center gap-2 min-w-0">
          <GitPullRequest className="w-4 h-4 shrink-0" />
          <span
            className={cn(
              "transition-all duration-500 ease-in-out",
              selectedPR && !showDropdown ? "whitespace-nowrap" : "truncate"
            )}
          >
            {disabled ? "Select a repository first" : selectedPR ? selectedPR.title : "Select pull request"}
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
            {prError ? (
              <div className="px-3 py-2 text-sm text-red-600 text-center">
                {prError}
              </div>
            ) : pullRequests.length === 0 ? (
              <div className="px-3 py-2 text-sm text-muted-foreground text-center">
                No pull requests available
              </div>
            ) : (
              pullRequests.map((pr) => (
                <Button
                  key={pr.id}
                  onClick={() => {
                    setSelectedPR(pr);
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
                    "hover:bg-muted/50 flex flex-col items-start group",
                    selectedPR?.id === pr.id && "bg-primary/10 text-primary"
                  )}
                >
                  <div className="w-full">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium truncate flex-1">{pr.title}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>#{pr.id}</span>
                      <span>•</span>
                      <span>{pr.comments} comments</span>
                      <span>•</span>
                      <span>{new Date(pr.updated_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </Button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

