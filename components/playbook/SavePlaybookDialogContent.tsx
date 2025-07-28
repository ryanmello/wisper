"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, X, Plus, Layers } from "lucide-react";
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
import {
  DialogContent,
  DialogTitle,
  DialogHeader,
  DialogDescription,
} from "../ui/dialog";
import { toast } from "sonner";
import { PlaybookAPI } from "@/lib/api/playbook-api";

const formSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  description: z.string().min(1, "Description is required").max(500),
  prompt: z.string().min(10, "Prompt must be at least 10 characters").max(1000),
  tags: z.array(z.string()).min(1, "At least one tag is required").max(10),
});

export default function SavePlaybookDialogContent({
  prompt,
  repository,
  onSuccess,
}: {
  prompt: string;
  repository?: string;
  onSuccess?: (playbookId: string) => void;
}) {
  const [newTag, setNewTag] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      description: "",
      prompt: prompt,
      tags: [],
    },
  });

  const tags = form.watch("tags") || [];

  // Update form when prompt changes
  useEffect(() => {
    form.reset({
      name: "",
      description: "",
      prompt: prompt,
      tags: [],
    });
    setNewTag("");
  }, [prompt, form]);

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

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    setIsLoading(true);
    try {
      const result = await PlaybookAPI.saveCipherPlaybook({
        name: values.name.trim(),
        description: values.description.trim(),
        prompt: values.prompt.trim(),
        repository,
        tags: values.tags,
      });
      if (result.success) {
        onSuccess?.(result.playbook_id);
        toast.success("Playbook Saved!", {
          description: "Your cipher playbook has been saved successfully.",
        });
        form.reset();
        setNewTag("");
      } else {
        toast.error("Failed to save playbook", {
          description: result.message,
        });
      }
    } catch (err) {
      toast.error("Failed to save playbook", {
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
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Save Playbook</DialogTitle>
        <DialogDescription>
          Save your cipher prompt as a reusable playbook.
        </DialogDescription>
      </DialogHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 py-4">
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
                    placeholder="Describe what this playbook does..."
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

          <FormField
            control={form.control}
            name="prompt"
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

          {repository && (
            <div className="space-y-2">
              <FormLabel>Repository</FormLabel>
              <div className="p-2 bg-muted rounded-md text-sm">
                {repository}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-4">
            <Button type="submit" disabled={isLoading}>
              {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              <Layers className="h-4 w-4 mr-2" />
              Save Playbook
            </Button>
          </div>
        </form>
      </Form>
    </DialogContent>
  );
}
