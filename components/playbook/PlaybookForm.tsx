"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, X, Plus, Waypoints, Fingerprint } from "lucide-react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { DialogTrigger } from "../ui/dialog";
import { toast } from "sonner";
import { PlaybookAPI } from "@/lib/api/playbook-api";
import {
  WaypointNode,
  WaypointConnection,
} from "@/lib/interface/waypoint-interface";
import type { Playbook } from "@/lib/interface/playbook-interface";

const createFormSchema = (mode: string, type: string) => {
  const baseSchema = {
    name: z.string().min(1, "Name is required").max(100),
    description: z.string().min(1, "Description is required").max(500),
    tags: z.array(z.string()).min(1, "At least one tag is required").max(10),
  };

  if (type === "cipher") {
    return z.object({
      ...baseSchema,
      prompt: z
        .string()
        .min(10, "Prompt must be at least 10 characters")
        .max(1000),
    });
  }

  return z.object(baseSchema);
};

type PlaybookDialogMode =
  | "save-cipher"
  | "save-waypoint"
  | "edit-cipher"
  | "edit-waypoint";

interface PlaybookFormProps {
  mode: PlaybookDialogMode;
  // For save modes
  prompt?: string;
  repository?: string;
  nodes?: WaypointNode[];
  connections?: WaypointConnection[];
  // For edit modes
  playbook?: Playbook;
  // Callbacks
  onSuccess?: (playbookId: string) => void;
}

export default function PlaybookForm({
  mode,
  prompt = "",
  repository,
  nodes = [],
  connections = [],
  playbook,
  onSuccess,
}: PlaybookFormProps) {
  const [newTag, setNewTag] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const isSaveMode = mode.startsWith("save");
  const isEditMode = mode.startsWith("edit");
  const isCipherType = mode.includes("cipher");
  const isWaypointType = mode.includes("waypoint");

  // Determine repository URL for display
  const repositoryUrl =
    repository ||
    playbook?.cipher_config?.repository ||
    playbook?.waypoint_config?.repository_url;

  // Create schema based on type
  const formSchema = createFormSchema(
    mode,
    isCipherType ? "cipher" : "waypoint"
  );
  type FormData = z.infer<typeof formSchema>;

  // Get initial values based on mode
  const getInitialValues = () => {
    if (isSaveMode) {
      return {
        name: "",
        description: "",
        tags: [],
        ...(isCipherType && { prompt: prompt }),
      };
    } else if (isEditMode && playbook) {
      if (isCipherType && playbook.cipher_config) {
        return {
          name: playbook.cipher_config.name,
          description: playbook.cipher_config.description || "",
          prompt: playbook.cipher_config.prompt,
          tags: playbook.cipher_config.tags || [],
        };
      } else if (isWaypointType && playbook.waypoint_config) {
        return {
          name: playbook.waypoint_config.name,
          description: playbook.waypoint_config.description || "",
          tags: playbook.waypoint_config.tags || [],
        };
      }
    }
    return { name: "", description: "", tags: [], prompt: "" };
  };

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: getInitialValues(),
  });

  const tags = form.watch("tags") || [];

  // Reset form when mode/data changes
  useEffect(() => {
    form.reset(getInitialValues());
    setNewTag("");
  }, [mode, prompt, playbook, form]);

  const handleAddTag = () => {
    const tag = newTag.trim().toLowerCase();
    if (tag && !tags.includes(tag) && tags.length < 10) {
      form.setValue("tags", [...tags, tag]);
      setNewTag("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    form.setValue(
      "tags",
      tags.filter((tag) => tag !== tagToRemove)
    );
  };

  const onSubmit = async (values: FormData) => {
    setIsLoading(true);
    try {
      let result;

      if (isSaveMode) {
        if (isCipherType) {
          result = await PlaybookAPI.saveCipherPlaybook({
            name: values.name.trim(),
            description: values.description.trim(),
            prompt: (values as any).prompt.trim(),
            repository,
            tags: values.tags,
          });
        } else {
          result = await PlaybookAPI.saveWaypointPlaybook({
            name: values.name.trim(),
            description: values.description.trim(),
            nodes,
            connections,
            repository_url: repository,
            tags: values.tags,
          });
        }
      } else if (isEditMode && playbook) {
        if (isCipherType && playbook.cipher_config) {
          const updatedCipherConfig = {
            ...playbook.cipher_config,
            name: values.name.trim(),
            description: values.description.trim(),
            prompt: (values as any).prompt.trim(),
            tags: values.tags,
            updated_at: new Date().toISOString(),
          };

          result = await PlaybookAPI.updatePlaybook(playbook.id, {
            name: values.name.trim(),
            description: values.description.trim(),
            tags: values.tags,
            cipher_config: updatedCipherConfig,
          });
        } else if (isWaypointType && playbook.waypoint_config) {
          const updatedWaypointConfig = {
            ...playbook.waypoint_config,
            name: values.name.trim(),
            description: values.description.trim(),
            tags: values.tags,
            updated_at: new Date().toISOString(),
          };

          result = await PlaybookAPI.updatePlaybook(playbook.id, {
            name: values.name.trim(),
            description: values.description.trim(),
            tags: values.tags,
            waypoint_config: updatedWaypointConfig,
          });
        }
      }

      if (result?.success) {
        onSuccess?.(result.playbook_id);
        toast.success(isSaveMode ? "Playbook Saved!" : "Playbook Updated!", {
          description: `Your ${
            isCipherType ? "cipher" : "waypoint"
          } playbook has been ${
            isSaveMode ? "saved" : "updated"
          } successfully.`,
        });
        form.reset();
        setNewTag("");
      } else {
        toast.error(`Failed to ${isSaveMode ? "save" : "update"} playbook`, {
          description: result?.message,
        });
      }
    } catch (err) {
      toast.error(`Failed to ${isSaveMode ? "save" : "update"} playbook`, {
        description: "An unexpected error occurred.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && newTag.trim()) {
      e.preventDefault();
      handleAddTag();
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 pt-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name *</FormLabel>
              <FormControl>
                <Input
                  placeholder="Enter playbook name..."
                  disabled={isLoading}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description *</FormLabel>
              <FormControl>
                <Textarea
                  placeholder={`Describe what this ${
                    isCipherType ? "prompt" : "workflow"
                  } does...`}
                  disabled={isLoading}
                  rows={3}
                  className="min-h-[100px] max-h-[200px]"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Prompt field for cipher types */}
        {isCipherType && (
          <FormField
            control={form.control}
            name={"prompt" as any}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Prompt *</FormLabel>
                <FormControl>
                  <Textarea
                    placeholder="Enter your cipher prompt..."
                    disabled={isLoading}
                    rows={4}
                    className="min-h-[120px] max-h-[300px]"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        )}

        <FormField
          control={form.control}
          name="tags"
          render={() => (
            <FormItem>
              <FormLabel>Tags *</FormLabel>
              <FormControl>
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a tag..."
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyDown={handleKeyDown}
                      disabled={isLoading || tags.length >= 10}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={handleAddTag}
                      disabled={
                        !newTag.trim() || tags.length >= 10 || isLoading
                      }
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  {tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {tags.map((tag) => (
                        <Badge
                          key={tag}
                          variant="secondary"
                          className="text-xs"
                        >
                          {tag}
                          <button
                            type="button"
                            onClick={() => handleRemoveTag(tag)}
                            className="ml-1 hover:text-destructive"
                            disabled={isLoading}
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {tags.length}/10 tags (minimum 1 required)
                  </p>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Repository display for cipher, or workflow summary for waypoint */}
        {isCipherType && repositoryUrl && (
          <div className="space-y-2">
            <FormLabel>Repository</FormLabel>
            <div className="p-2 bg-muted rounded-md text-sm">
              {repositoryUrl}
            </div>
          </div>
        )}

        {/* Workflow Summary for waypoint types */}
        {isWaypointType && (
          <div className="space-y-2">
            <FormLabel>
              Workflow {isEditMode ? "(Read-only)" : "Summary"}
            </FormLabel>
            <div
              className={`p-3 bg-muted rounded-md space-y-2 ${
                isEditMode ? "opacity-75" : ""
              }`}
            >
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Nodes:</span>
                <span className="font-medium">
                  {isEditMode && playbook?.waypoint_config
                    ? playbook.waypoint_config.nodes.length
                    : nodes.length}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Connections:</span>
                <span className="font-medium">
                  {isEditMode && playbook?.waypoint_config
                    ? playbook.waypoint_config.connections.length
                    : connections.length}
                </span>
              </div>
              {repositoryUrl && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Repository:</span>
                  <span className="font-medium text-xs">{repositoryUrl}</span>
                </div>
              )}
              {((isEditMode && playbook?.waypoint_config?.nodes.length) ||
                (!isEditMode && nodes.length)) && (
                <div className="pt-2 border-t border-border">
                  <span className="text-xs text-muted-foreground">Tools:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {(isEditMode && playbook?.waypoint_config
                      ? playbook.waypoint_config.nodes
                      : nodes
                    )
                      .slice(0, 5)
                      .map((node) => (
                        <Badge
                          key={node.id}
                          variant="outline"
                          className="text-xs"
                        >
                          {node.data.label}
                        </Badge>
                      ))}
                    {(isEditMode && playbook?.waypoint_config
                      ? playbook.waypoint_config.nodes.length
                      : nodes.length) > 5 && (
                      <Badge variant="outline" className="text-xs">
                        +
                        {(isEditMode && playbook?.waypoint_config
                          ? playbook.waypoint_config.nodes.length
                          : nodes.length) - 5}{" "}
                        more
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4">
          <DialogTrigger asChild>
            <Button type="submit" disabled={isLoading}>
              {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {isCipherType ? (
                <Fingerprint className="h-4 w-4" />
              ) : (
                <Waypoints className="h-4 w-4" />
              )}
              {isSaveMode ? "Save" : "Update"} Playbook
            </Button>
          </DialogTrigger>
        </div>
      </form>
    </Form>
  );
}
