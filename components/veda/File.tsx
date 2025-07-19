import { Ban, ChevronRight, Plus, Pencil, Minus, ArrowRight, Circle } from "lucide-react";
import React from "react";
import { Badge } from "@/components/ui/badge";
import { GitHubFileChange } from "@/lib/interface/github-interface";

interface FileProps {
  file: GitHubFileChange;
  index: number;
  expandedFiles: Set<number>;
  toggleFileExpansion: (index: number) => void;
}

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

export default function File({ file, index, expandedFiles, toggleFileExpansion }: FileProps) {
  return (
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
              className={`${getFileStatusColor(file.status)} text-xs`}
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
                    borderClass = "border-l-4 border-green-400";
                    lineClass = "text-green-800";
                  } else if (line.startsWith("-")) {
                    bgClass = "bg-red-50";
                    borderClass = "border-l-4 border-red-400";
                    lineClass = "text-red-800";
                  } else if (line.startsWith("@@")) {
                    bgClass = "bg-blue-50";
                    borderClass = "border-l-4 border-blue-400";
                    lineClass = "text-blue-800 font-semibold";
                  } else if (isNoNewline) {
                    bgClass = "bg-gray-50";
                    borderClass = "border-l-4 border-gray-300";
                    lineClass = "text-gray-500 text-xs italic";
                  } else {
                    bgClass = "bg-white";
                    lineClass = "text-gray-700";
                  }

                  return (
                    <tr key={idx} className={`${bgClass} hover:bg-gray-50`}>
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
  );
}
