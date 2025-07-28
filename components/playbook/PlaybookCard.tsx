import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import type { Playbook } from "@/lib/interface/playbook-interface";
import {
  MessageSquare,
  Workflow,
  Calendar,
  User,
  Play,
  Copy,
  Share,
  MoreHorizontal,
  AlertTriangle,
  Pencil,
  Trash,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useState } from "react";
import DeletePlaybookDialogContent from "./DeletePlaybookDialogContent";
import EditPlaybookDialogContent from "./EditPlaybookDialogContent";

interface PlaybookCardProps {
  playbook: Playbook;
  onRun?: (playbook: Playbook) => void;
  onCopy?: (playbook: Playbook) => void;
  onShare?: (playbook: Playbook) => void;
  onEdit?: (playbook: Playbook) => void;
  onDelete?: (playbook: Playbook) => void;
}

export function PlaybookCard({
  playbook,
  onRun,
  onCopy,
  onShare,
  onEdit,
  onDelete,
}: PlaybookCardProps) {
  const getTypeIcon = () => {
    switch (playbook.type) {
      case "cipher":
        return <MessageSquare className="h-4 w-4" />;
      case "waypoint":
        return <Workflow className="h-4 w-4" />;
      case "combined":
        return (
          <div className="flex gap-1">
            <MessageSquare className="h-3 w-3" />
            <Workflow className="h-3 w-3" />
          </div>
        );
      default:
        return <MessageSquare className="h-4 w-4" />;
    }
  };

  const getTypeColor = () => {
    switch (playbook.type) {
      case "cipher":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300";
      case "waypoint":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300";
      case "combined":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300";
    }
  };

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {getTypeIcon()}
            <Badge variant="secondary" className={getTypeColor()}>
              {playbook.type}
            </Badge>
          </div>
          <div className="flex items-center">
            {/* Edit Dialog */}
            {playbook.type === "cipher" && playbook.cipher_config && (
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="ghost" size="sm" title="Edit">
                    <Pencil className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[500px]">
                  <EditPlaybookDialogContent
                    playbook={playbook}
                    onSuccess={() => onEdit?.(playbook)}
                  />
                </DialogContent>
              </Dialog>
            )}
            {/* Delete Dialog */}
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm">
                  <Trash className="h-4 w-4 text-muted-foreground" />
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[400px]">
                <DeletePlaybookDialogContent
                  playbook={playbook}
                  onDelete={onDelete}
                />
              </DialogContent>
            </Dialog>
          </div>
        </div>
        <CardTitle className="text-lg">{playbook.name}</CardTitle>
        {playbook.description && (
          <CardDescription className="line-clamp-2">
            {playbook.description}
          </CardDescription>
        )}
      </CardHeader>

      <CardContent className="pt-0">
        {/* Tags */}
        {playbook.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {playbook.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
            {playbook.tags.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{playbook.tags.length - 3} more
              </Badge>
            )}
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4">
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {formatDistanceToNow(new Date(playbook.created_at), {
              addSuffix: true,
            })}
          </div>
          {playbook.author && (
            <div className="flex items-center gap-1">
              <User className="h-3 w-3" />
              {playbook.author}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={() => onRun?.(playbook)}
            className="flex-1 bg-gray-50"
            variant="outline"
          >
            <Play className="h-3 w-3 mr-1" />
            Run
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
