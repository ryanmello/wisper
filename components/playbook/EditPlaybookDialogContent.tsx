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
import { toast } from "sonner";
import { PlaybookAPI } from "@/lib/api/playbook-api";
import {
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "../ui/dialog";
import type { Playbook } from "@/lib/interface/playbook-interface";

const formSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  description: z.string().min(1, "Description is required").max(500),
  prompt: z.string().min(10, "Prompt must be at least 10 characters").max(1000),
  tags: z.array(z.string()).min(1, "At least one tag is required").max(10),
});

export default function EditPlaybookDialogContent({
  playbook,
  onSuccess,
}: {
  playbook: Playbook;
  onSuccess?: (playbookId: string) => void;
}) {
  const [newTag, setNewTag] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Only support cipher playbooks for now
  if (playbook.type !== "cipher" || !playbook.cipher_config) {
    return (
      <div className="p-6 text-center">
        <p className="text-muted-foreground">
          Edit is only supported for cipher playbooks.
        </p>
      </div>
    );
  }

  const cipher = playbook.cipher_config;

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: cipher.name,
      description: cipher.description || "",
      prompt: cipher.prompt,
      tags: cipher.tags || [],
    },
  });

  const tags = form.watch("tags") || [];

  // Reset form with playbook data when component mounts
  useEffect(() => {
    form.reset({
      name: cipher.name,
      description: cipher.description || "",
      prompt: cipher.prompt,
      tags: cipher.tags || [],
    });
    setNewTag("");
  }, [playbook, form, cipher]);

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
      const updatedCipherConfig = {
        ...cipher,
        name: values.name.trim(),
        description: values.description.trim(),
        prompt: values.prompt.trim(),
        tags: values.tags,
        updated_at: new Date().toISOString(),
      };

      const result = await PlaybookAPI.updatePlaybook(playbook.id, {
        name: values.name.trim(),
        description: values.description.trim(),
        tags: values.tags,
        cipher_config: updatedCipherConfig,
      });
      if (result.success) {
        onSuccess?.(playbook.id);
        toast.success("Playbook Updated!", {
          description: "Your cipher playbook has been updated successfully.",
        });
      } else {
        toast.error("Failed to update playbook", {
          description: result.message,
        });
      }
    } catch (err) {
      toast.error("Failed to update playbook", {
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
    <div>
      <DialogHeader>
        <DialogTitle>Edit Playbook</DialogTitle>
        <DialogDescription>
          Update your playbook details below.
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

          {cipher.repository && (
            <div className="space-y-2">
              <FormLabel>Repository</FormLabel>
              <div className="p-2 bg-muted rounded-md text-sm">
                {cipher.repository}
              </div>
            </div>
          )}

          <div className="flex justify-end pt-4">
            <DialogTrigger asChild>
              <Button type="submit" disabled={isLoading}>
                {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                <Layers className="h-4 w-4" />
                Update Playbook
              </Button>
            </DialogTrigger>
          </div>
        </form>
      </Form>
    </div>
  );
}
