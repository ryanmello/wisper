import React, { useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { cn, getLanguageColor } from "@/lib/utils";
import { Github, ChevronDown } from "lucide-react";
import { GitHubRepository } from "@/lib/interface/github-interface";

interface RepoDropdownProps {
  repositories: GitHubRepository[];
  selectedRepo: GitHubRepository | null;
  showDropdown: boolean;
  showDropdownContent: boolean;
  repoError: string | null;
  dropdownTimeoutRef: React.MutableRefObject<NodeJS.Timeout | null>;
  toggleDropdown: () => void;
  setSelectedRepo: (repo: GitHubRepository) => void;
  setShowDropdown: (show: boolean) => void;
  setShowDropdownContent: (show: boolean) => void;
}

export default function RepoDropdown({
  repositories,
  selectedRepo,
  showDropdown,
  showDropdownContent,
  repoError,
  dropdownTimeoutRef,
  toggleDropdown,
  setSelectedRepo,
  setShowDropdown,
  setShowDropdownContent,
}: RepoDropdownProps) {
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
        onClick={toggleDropdown}
        variant="outline"
        className={cn(
          "cursor-pointer flex items-center gap-2 px-3 py-2 rounded-xl text-sm transition-all duration-500 ease-in-out",
          "border border-border hover:border-border hover:bg-muted/50",
          "justify-between h-auto",
          // Dynamic width based on state
          showDropdown || !selectedRepo ? "min-w-[300px]" : "w-auto min-w-0"
        )}
      >
        <div className="flex items-center gap-2 min-w-0">
          <Github className="w-4 h-4 shrink-0" />
          <span
            className={cn(
              "transition-all duration-500 ease-in-out",
              selectedRepo && !showDropdown ? "whitespace-nowrap" : "truncate"
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
                    selectedRepo?.id === repo.id && "bg-primary/10 text-primary"
                  )}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium truncate">{repo.name}</span>
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
  );
}
