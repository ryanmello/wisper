"use client";

import { useState } from "react";
import {
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { AlertTriangle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { PlaybookAPI } from "@/lib/api/playbook-api";
import type { Playbook } from "@/lib/interface/playbook-interface";

export default function DeletePlaybookDialogContent({
  playbook,
  onDelete,
}: {
  playbook: Playbook;
  onDelete?: (playbook: Playbook) => void;
}) {
  const [isLoading, setIsLoading] = useState(false);

  const handleDelete = async () => {
    setIsLoading(true);
    try {
      const result = await PlaybookAPI.deletePlaybook(playbook.id);
      if (result.success) {
        toast.success("Playbook deleted successfully");
        onDelete?.(playbook); // Call parent refresh handler
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
  );
}
