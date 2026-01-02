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
  DialogTrigger,
} from "@/components/ui/dialog";
import type { Playbook } from "@/lib/interface/playbook-interface";
import {
  MessageSquare,
  Workflow,
  Calendar,
  User,
  Play,
  Pencil,
  Trash,
  Loader2,
  ExternalLink,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import PlaybookDialog from "./PlaybookDialog";

interface PlaybookCardProps {
  playbook: Playbook;
  isLoading?: boolean;
  hasStartedTask?: boolean;
  onRun?: (playbook: Playbook) => void;
  onViewTask?: (playbook: Playbook) => void;
  onEdit?: (playbook: Playbook) => void;
  onDelete?: (playbook: Playbook) => void;
}

export function PlaybookCard({
  playbook,
  isLoading = false,
  hasStartedTask = false,
  onRun,
  onViewTask,
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
            {/* Edit Button */}
            {((playbook.type === "cipher" && playbook.cipher_config) ||
              (playbook.type === "waypoint" && playbook.waypoint_config)) && (
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="ghost" size="sm" title="Edit">
                    <Pencil className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </DialogTrigger>
                <PlaybookDialog
                  mode={
                    playbook.type === "cipher" ? "edit-cipher" : "edit-waypoint"
                  }
                  playbook={playbook}
                  onSuccess={() => onEdit?.(playbook)}
                />
              </Dialog>
            )}

            {/* Delete Dialog */}
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm">
                  <Trash className="h-4 w-4 text-muted-foreground" />
                </Button>
              </DialogTrigger>
              <PlaybookDialog
                mode="delete"
                playbook={playbook}
                onDelete={onDelete}
              />
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

        {/* Cipher Repository Display */}
        {playbook.type === "cipher" && playbook.cipher_config?.repository && (
          <div className="mb-3 p-2 bg-gray-50 rounded-md">
            <div className="text-xs text-muted-foreground">
              <span className="font-medium">Repository:</span>{" "}
              {playbook.cipher_config.repository}
            </div>
            {playbook.cipher_config.prompt && (
              <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                <span className="font-medium">Prompt:</span>{" "}
                {playbook.cipher_config.prompt}
              </div>
            )}
          </div>
        )}

        {/* Waypoint Workflow Summary */}
        {playbook.type === "waypoint" && playbook.waypoint_config && (
          <div className="mb-3 p-2 bg-gray-50 rounded-md">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
              <span>Workflow:</span>
              <span className="font-medium">
                {playbook.waypoint_config.nodes.length} nodes,{" "}
                {playbook.waypoint_config.connections.length} connections
              </span>
            </div>
            {playbook.waypoint_config.repository_url && (
              <div className="text-xs text-muted-foreground">
                <span className="font-medium">Repository:</span>{" "}
                {playbook.waypoint_config.repository_url}
              </div>
            )}
          </div>
        )}

        {playbook.type === "waypoint" && playbook.waypoint_config && (
          <div className="mb-3">
            {playbook.waypoint_config.nodes.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {playbook.waypoint_config.nodes.slice(0, 3).map((node) => (
                  <Badge key={node.id} variant="outline" className="text-xs">
                    {node.data.label}
                  </Badge>
                ))}
                {playbook.waypoint_config.nodes.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{playbook.waypoint_config.nodes.length - 3} more tools
                  </Badge>
                )}
              </div>
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
          {hasStartedTask ? (
            <Button
              size="sm"
              onClick={() => onViewTask?.(playbook)}
              className="flex-1 bg-blue-50 hover:bg-blue-100 border-blue-200"
              variant="outline"
            >
              <ExternalLink className="h-3 w-3 mr-1 text-blue-600" />
              <span className="text-blue-700">View Task</span>
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={() => onRun?.(playbook)}
              className="flex-1 bg-gray-50"
              variant="outline"
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              ) : (
                <Play className="h-3 w-3 mr-1" />
              )}
              {isLoading ? "Starting..." : "Run"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
