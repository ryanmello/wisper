"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, AlertTriangle } from "lucide-react";
import {
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "../ui/dialog";
import { toast } from "sonner";
import { PlaybookAPI } from "@/lib/api/playbook-api";
import {
  WaypointNode,
  WaypointConnection,
} from "@/lib/interface/waypoint-interface";
import type { Playbook } from "@/lib/interface/playbook-interface";
import PlaybookForm from "./PlaybookForm";

type PlaybookDialogMode =
  | "save-cipher"
  | "save-waypoint"
  | "edit-cipher"
  | "edit-waypoint"
  | "delete";

interface PlaybookDialogProps {
  mode: PlaybookDialogMode;
  // For save modes
  prompt?: string;
  repository?: string;
  nodes?: WaypointNode[];
  connections?: WaypointConnection[];
  // For edit/delete modes
  playbook?: Playbook;
  // Callbacks
  onSuccess?: (playbookId: string) => void;
  onDelete?: (playbook: Playbook) => void;
}

export default function PlaybookDialog({
  mode,
  prompt = "",
  repository,
  nodes = [],
  connections = [],
  playbook,
  onSuccess,
  onDelete,
}: PlaybookDialogProps) {
  const [isLoading, setIsLoading] = useState(false);

  const isDeleteMode = mode === "delete";

  // Delete mode - render delete confirmation
  if (isDeleteMode && playbook) {
    const handleDelete = async () => {
      setIsLoading(true);
      try {
        const result = await PlaybookAPI.deletePlaybook(playbook.id);
        if (result.success) {
          toast.success("Playbook deleted successfully");
          onDelete?.(playbook);
        } else {
          toast.error("Failed to delete playbook", {
            description: result.message,
          });
        }
      } catch (error) {
        console.error("Error deleting playbook:", error);
        toast.error("Failed to delete playbook", {
          description: "An unexpected error occurred.",
        });
      } finally {
        setIsLoading(false);
      }
    };

    return (
      <DialogContent className="sm:max-w-[400px]">
        <div className="flex flex-col items-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mb-4" />
          <DialogHeader className="w-full">
            <DialogTitle className="text-lg font-semibold">
              Are you sure?
            </DialogTitle>
            <DialogDescription></DialogDescription>
          </DialogHeader>
          <div className="w-full mb-4">
            <p className="text-sm text-zinc-700 dark:text-zinc-300 text-left">
              Do you want to delete{" "}
              <span className="font-semibold text-red-700 underline underline-offset-2">
                {playbook.name}
              </span>
              ?
            </p>
          </div>
          <div className="w-full flex flex-col sm:flex-row gap-2 mt-2">
            <DialogTrigger asChild>
              <Button variant="outline" className="flex-1" disabled={isLoading}>
                Cancel
              </Button>
            </DialogTrigger>
            <DialogTrigger asChild>
              <Button
                className="flex-1 bg-red-500 hover:bg-red-600 text-white font-semibold shadow-sm"
                onClick={handleDelete}
                disabled={isLoading}
              >
                {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Delete
              </Button>
            </DialogTrigger>
          </div>
        </div>
      </DialogContent>
    );
  }

  // For save/edit modes, use PlaybookForm
  const isCipherType = mode.includes("cipher");
  const isWaypointType = mode.includes("waypoint");
  const isSaveMode = mode.startsWith("save");
  
  const getDialogContent = () => {
    if (isSaveMode) {
      return {
        title: `Save ${isCipherType ? "Cipher" : "Waypoint"} Playbook`,
        description: `Save your ${
          isCipherType ? "prompt" : "workflow"
        } as a reusable playbook.`,
      };
    } else {
      return {
        title: `Edit ${isCipherType ? "Cipher" : "Waypoint"} Playbook`,
        description: `Update your playbook details.${
          isWaypointType ? " The workflow structure cannot be modified." : ""
        }`,
      };
    }
  };

  const { title, description } = getDialogContent();

  return (
    <DialogContent className="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription>{description}</DialogDescription>
      </DialogHeader>
      <PlaybookForm
        mode={mode as any}
        prompt={prompt}
        repository={repository}
        nodes={nodes}
        connections={connections}
        playbook={playbook}
        onSuccess={onSuccess}
      />
    </DialogContent>
  );
}
