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
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

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
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[400px] bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xl rounded-xl p-0">
              <div className="flex flex-col items-center p-6">
                <AlertTriangle className="h-8 w-8 text-red-500 mb-4" />
                <DialogHeader className="w-full">
                  <DialogTitle className="text-lg font-semibold">
                    Are you sure?
                  </DialogTitle>
                </DialogHeader>
                <div className="w-full mb-4">
                  <p className="text-sm text-zinc-700 dark:text-zinc-300">
                    Do you want to delete{" "}
                    <span className="font-semibold text-red-500 underline underline-offset-2">
                      {playbook.name}
                    </span>
                    ?
                  </p>
                </div>
                <div className="w-full flex flex-col sm:flex-row gap-2 mt-2">
                  <DialogTrigger asChild>
                    <Button variant="outline" className="flex-1">
                      Cancel
                    </Button>
                  </DialogTrigger>
                  <DialogTrigger asChild>
                    <Button
                      className="flex-1 bg-red-500 hover:bg-red-600 text-white font-semibold shadow-sm"
                      onClick={() => onDelete?.(playbook)}
                    >
                      Delete
                    </Button>
                  </DialogTrigger>
                </div>
              </div>
            </DialogContent>
          </Dialog>
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
            className="flex-1"
          >
            <Play className="h-3 w-3 mr-1" />
            Run
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onCopy?.(playbook)}
          >
            <Copy className="h-3 w-3" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onShare?.(playbook)}
          >
            <Share className="h-3 w-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
