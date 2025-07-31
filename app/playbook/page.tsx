"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { AuthLoadingScreen } from "@/components/AuthLoadingScreen";
import { useAuth } from "@/context/auth-context";
import { useTask } from "@/context/task-context";
import { PlaybookCard } from "@/components/playbook/PlaybookCard";
import { Button } from "@/components/ui/button";
import type { Playbook } from "@/lib/interface/playbook-interface";
import {
  Layers,
  Plus,
  ChevronLeft,
  ChevronRight,
  Fingerprint,
  Waypoints,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useRef } from "react";
import EmptyState from "@/components/EmptyState";
import { PlaybookAPI } from "@/lib/api/playbook-api";
import { toast } from "sonner";

export default function Playbook() {
  const { isLoading: isAuthLoading, isAuthenticated } = useAuth();
  const { createTask } = useTask();
  const router = useRouter();
  const cipherScrollRef = useRef<HTMLDivElement>(null);
  const waypointScrollRef = useRef<HTMLDivElement>(null);

  const [cipherPlaybooks, setCipherPlaybooks] = useState<Playbook[]>([]);
  const [waypointPlaybooks, setWaypointPlaybooks] = useState<Playbook[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});
  const [startedTasks, setStartedTasks] = useState<Record<string, string>>({});

  const loadPlaybooks = async () => {
    try {
      const data = PlaybookAPI.getAllPlaybooks();
      setCipherPlaybooks(data.cipher_playbooks);
      setWaypointPlaybooks(data.waypoint_playbooks);
    } catch (error) {
      console.error("Error loading playbooks:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadPlaybooks();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      router.push('/sign-in');
    }
  }, [isAuthLoading, isAuthenticated, router]);

  if (isAuthLoading) return <AuthLoadingScreen />;
  if (!isAuthenticated) return <AuthLoadingScreen />;

  const handleRunPlaybook = async (playbook: Playbook) => {
    if (playbook.type === "cipher") {
      // Validate required fields
      if (!playbook.cipher_config?.prompt || !playbook.cipher_config?.repository) {
        toast.error("Invalid cipher playbook", {
          description: "Missing prompt or repository information."
        });
        return;
      }

      try {
        // Set loading state for this specific playbook
        setLoadingStates(prev => ({ ...prev, [playbook.id]: true }));

        // Create task using task context (this adds it to the context automatically)
        const task = await createTask({
          repository_url: playbook.cipher_config.repository,
          prompt: playbook.cipher_config.prompt
        });

        if (!task) {
          throw new Error("Failed to create task");
        }

        // Store the started task
        setStartedTasks(prev => ({ ...prev, [playbook.id]: task.id }));

        // Show success feedback
        toast.success("Analysis Started!", {
          description: `"${playbook.name}" playbook is now running. Click "View Task" to monitor progress.`
        });

      } catch (error) {
        console.error("Error starting cipher analysis:", error);
        toast.error("Failed to start analysis", {
          description: error instanceof Error ? error.message : "An unexpected error occurred."
        });
      } finally {
        // Clear loading state
        setLoadingStates(prev => ({ ...prev, [playbook.id]: false }));
      }
    } else if (playbook.type === "waypoint") {
      // Validate required fields
      if (!playbook.waypoint_config?.nodes || playbook.waypoint_config.nodes.length === 0) {
        toast.error("Invalid waypoint playbook", {
          description: "No workflow nodes found."
        });
        return;
      }

      try {
        // Set loading state for this specific playbook
        setLoadingStates(prev => ({ ...prev, [playbook.id]: true }));

        // Navigate to waypoint page with playbook data
        router.push(`/waypoint?playbook=${playbook.id}`);
        
        // Show success feedback
        toast.success("Workflow Loaded!", {
          description: `"${playbook.name}" workflow opened in Waypoint. Verify and run the configuration.`
        });

      } catch (error) {
        console.error("Error loading waypoint workflow:", error);
        toast.error("Failed to load workflow", {
          description: error instanceof Error ? error.message : "An unexpected error occurred."
        });
      } finally {
        // Clear loading state
        setLoadingStates(prev => ({ ...prev, [playbook.id]: false }));
      }
    }
  };

  const handleViewTask = (playbook: Playbook) => {
    const taskId = startedTasks[playbook.id];
    if (taskId) {
      router.push(`/cipher/${taskId}`);
    }
  };

  const handleCopyPlaybook = (playbook: Playbook) => {
    console.log("Copying playbook:", playbook.name);
    // TODO: Implement copy logic
  };

  const handleSharePlaybook = (playbook: Playbook) => {
    console.log("Sharing playbook:", playbook.name);
    // TODO: Implement share logic
  };

  const handleDeletePlaybook = async (playbook: Playbook) => {
    // This is called after successful deletion from the dialog
    // Just refresh the list, don't call the API again
    await loadPlaybooks();
  };

  const handleEditPlaybook = async (playbook: Playbook) => {
    // Refresh the playbooks list after editing
    await loadPlaybooks();
  };

  const scrollCipher = (direction: "left" | "right") => {
    if (cipherScrollRef.current) {
      const scrollAmount = 320; // Card width + gap
      const currentScroll = cipherScrollRef.current.scrollLeft;
      const newScroll =
        direction === "left"
          ? currentScroll - scrollAmount
          : currentScroll + scrollAmount;

      cipherScrollRef.current.scrollTo({
        left: newScroll,
        behavior: "smooth",
      });
    }
  };

  const scrollWaypoint = (direction: "left" | "right") => {
    if (waypointScrollRef.current) {
      const scrollAmount = 320; // Card width + gap
      const currentScroll = waypointScrollRef.current.scrollLeft;
      const newScroll =
        direction === "left"
          ? currentScroll - scrollAmount
          : currentScroll + scrollAmount;

      waypointScrollRef.current.scrollTo({
        left: newScroll,
        behavior: "smooth",
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col pt-16 p-4">
      <div className="w-full max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-center mb-8 gap-2">
          <Layers size={32} />
          <h1 className="text-2xl font-semibold">Playbook</h1>
        </div>

        {/* Cipher Playbooks Section */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Fingerprint />
              <p className="font-semibold text-xl">Cipher</p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => scrollCipher("left")}
                className="h-8 w-8 p-0"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => scrollCipher("right")}
                className="h-8 w-8 p-0"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Horizontal Scrolling Cipher Cards */}
          <div className="relative">
            <div
              ref={cipherScrollRef}
              className="flex gap-6 overflow-x-auto pb-4 hide-scrollbar"
            >
              {isLoading ? (
                // Loading skeletons
                Array.from({ length: 3 }).map((_, index) => (
                  <div key={index} className="flex-none w-80">
                    <div className="h-48 bg-gray-200 rounded-lg animate-pulse" />
                  </div>
                ))
              ) : cipherPlaybooks.length > 0 ? (
                cipherPlaybooks.map((playbook) => (
                  <div key={playbook.id} className="flex-none w-80">
                    <PlaybookCard
                      playbook={playbook}
                      isLoading={loadingStates[playbook.id] || false}
                      hasStartedTask={!!startedTasks[playbook.id]}
                      onRun={handleRunPlaybook}
                      onViewTask={handleViewTask}
                      onCopy={handleCopyPlaybook}
                      onShare={handleSharePlaybook}
                      onEdit={handleEditPlaybook}
                      onDelete={handleDeletePlaybook}
                    />
                  </div>
                ))
              ) : (
                <EmptyState
                  heading="No Cipher playbooks yet"
                  subheading="Create prompts in Cipher to build your playbook library"
                />
              )}
            </div>
          </div>
        </div>

        {/* Waypoint Playbooks Section */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Waypoints />
              <p className="font-semibold text-xl">Waypoint</p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => scrollWaypoint("left")}
                className="h-8 w-8 p-0"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => scrollWaypoint("right")}
                className="h-8 w-8 p-0"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Horizontal Scrolling Waypoint Cards */}
          <div className="relative">
            <div
              ref={waypointScrollRef}
              className="flex gap-6 overflow-x-auto pb-4 hide-scrollbar"
            >
              {isLoading ? (
                // Loading skeletons
                Array.from({ length: 3 }).map((_, index) => (
                  <div key={index} className="flex-none w-80">
                    <div className="h-48 bg-gray-200 rounded-lg animate-pulse" />
                  </div>
                ))
              ) : waypointPlaybooks.length > 0 ? (
                waypointPlaybooks.map((playbook) => (
                  <div key={playbook.id} className="flex-none w-80">
                    <PlaybookCard
                      playbook={playbook}
                      isLoading={loadingStates[playbook.id] || false}
                      hasStartedTask={!!startedTasks[playbook.id]}
                      onRun={handleRunPlaybook}
                      onViewTask={handleViewTask}
                      onCopy={handleCopyPlaybook}
                      onShare={handleSharePlaybook}
                      onEdit={handleEditPlaybook}
                      onDelete={handleDeletePlaybook}
                    />
                  </div>
                ))
              ) : (
                <EmptyState
                  heading="No Waypoint playbooks yet"
                  subheading="Create workflows in Waypoint to build your playbook library"
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
