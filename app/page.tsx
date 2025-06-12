"use client";

import { useState, useEffect } from "react";
import { NavigationHeader, StepIndicator } from "@/components/ui/navigation";
import RepositorySelector from "@/components/RepositorySelector";
import TaskSelector from "@/components/TaskSelector";
import TaskExecution from "@/components/TaskExecution";
import SmartTaskExecution from "@/components/SmartTaskExecution";
import { TaskType } from "@/lib/api";

type Step = "repository" | "task" | "execution" | "smart-execution";

interface SmartAnalysisOptions {
  scope?: 'full' | 'security_focused' | 'performance_focused';
  depth?: 'surface' | 'deep' | 'comprehensive';
  target_languages?: string[];
}

const STEPS = [
  {
    id: "repository",
    label: "Repository",
    description: "Select source"
  },
  {
    id: "task",
    label: "Task",
    description: "Choose analysis"
  },
  {
    id: "execution",
    label: "Execution",
    description: "Run analysis"
  }
];

export default function Home() {
  const [currentStep, setCurrentStep] = useState<Step>("repository");
  const [selectedRepository, setSelectedRepository] = useState<string>("");
  const [selectedTask, setSelectedTask] = useState<TaskType | null>(null);
  
  // Smart analysis state
  const [smartAnalysisContext, setSmartAnalysisContext] = useState<string>("");
  const [smartAnalysisOptions, setSmartAnalysisOptions] = useState<SmartAnalysisOptions>({});

  // Helper function to scroll to top smoothly
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  // Scroll to top whenever the step changes
  useEffect(() => {
    scrollToTop();
  }, [currentStep]);

  const handleRepositorySelect = (repo: string) => {
    setSelectedRepository(repo);
    setCurrentStep("task");
    // Scroll to top when navigating to task selection
    scrollToTop();
  };

  const handleTaskSelect = (task: TaskType | null) => {
    setSelectedTask(task);
  };

  const handleStartTask = () => {
    setCurrentStep("execution");
    // Scroll to top when starting task execution
    scrollToTop();
  };

  const handleStartSmartTask = (context: string, options?: SmartAnalysisOptions) => {
    setSmartAnalysisContext(context);
    setSmartAnalysisOptions(options || {});
    setCurrentStep("smart-execution");
    // Scroll to top when starting smart analysis
    scrollToTop();
  };

  const handleBack = () => {
    switch (currentStep) {
      case "task":
        setCurrentStep("repository");
        setSelectedRepository("");
        setSelectedTask(null);
        break;
      case "execution":
      case "smart-execution":
        setCurrentStep("task");
        setSelectedTask(null);
        setSmartAnalysisContext("");
        setSmartAnalysisOptions({});
        break;
      default:
        setCurrentStep("repository");
        break;
    }
    // Scroll to top when navigating back
    scrollToTop();
  };

  const getNavigationProps = () => {
    switch (currentStep) {
      case "repository":
        return {
          title: "Whisper AI Assistant",
          subtitle: "Connect your repository to get started with AI-powered code analysis",
          breadcrumbs: [{ label: "Home", current: true }],
        };
      
      case "task":
        return {
          title: "Choose Analysis Type",
          subtitle: `Analyzing: ${selectedRepository}`,
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Task Selection", current: true }
          ],
          onBack: handleBack,
        };
      
      case "execution":
        return {
          title: selectedTask ? getTaskTitle(selectedTask) : "Running Analysis",
          subtitle: `Repository: ${getRepoName(selectedRepository)}`,
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Task Selection", href: "/task" },
            { label: "Execution", current: true }
          ],
          onBack: handleBack,
        };
      
      case "smart-execution":
        return {
          title: "Smart Analysis",
          subtitle: `Repository: ${getRepoName(selectedRepository)}`,
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Task Selection", href: "/task" },
            { label: "Smart Analysis", current: true }
          ],
          onBack: handleBack,
        };
      
      default:
        return {
          title: "Whisper AI Assistant",
          subtitle: "AI-powered code analysis and task automation",
        };
    }
  };

  const getStepIndicatorSteps = () => {
    return STEPS.map(step => ({
      ...step,
      status: currentStep === step.id 
        ? 'current' as const
        : getStepIndex(currentStep) > getStepIndex(step.id)
        ? 'completed' as const
        : 'upcoming' as const
    }));
  };

  const getStepIndex = (step: string) => {
    const stepMap: Record<string, number> = {
      repository: 0,
      task: 1,
      execution: 2,
      'smart-execution': 2
    };
    return stepMap[step] || 0;
  };

  const getTaskTitle = (task: string) => {
    const taskTitles: Record<string, string> = {
      "explore-codebase": "Explore Codebase",
      "dependency-audit": "Dependency Audit",
    };
    return taskTitles[task] || "Analysis";
  };

  const getRepoName = (repo: string) => {
    if (repo.includes('github.com')) {
      const match = repo.match(/github\.com\/([^\/]+\/[^\/]+)/);
      return match ? match[1] : repo;
    }
    return repo;
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case "repository":
        return (
          <div className="animate-in fade-in-0 duration-300">
            <RepositorySelector onRepoSelect={handleRepositorySelect} />
          </div>
        );
      
      case "task":
        return (
          <div className="animate-in fade-in-0 duration-300">
            <TaskSelector
              repository={selectedRepository}
              onTaskSelect={handleTaskSelect}
              onStartTask={handleStartTask}
              onStartSmartTask={handleStartSmartTask}
              selectedTask={selectedTask}
            />
          </div>
        );
      
      case "execution":
        return (
          <div className="animate-in fade-in-0 duration-300">
            <TaskExecution
              repository={selectedRepository}
              task={selectedTask || "explore-codebase"}
              onBack={handleBack}
            />
          </div>
        );
      
      case "smart-execution":
        return (
          <div className="animate-in fade-in-0 duration-300">
            <SmartTaskExecution
              repository={selectedRepository}
              context={smartAnalysisContext}
              options={smartAnalysisOptions}
              onBack={handleBack}
            />
          </div>
        );
      
      default:
        return (
          <div className="animate-in fade-in-0 duration-300">
            <RepositorySelector onRepoSelect={handleRepositorySelect} />
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <NavigationHeader {...getNavigationProps()} />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Step Indicator - shown for non-execution steps */}
        {currentStep !== "execution" && currentStep !== "smart-execution" && (
          <div className="mb-8">
            <div className="max-w-6xl mx-auto">
              <StepIndicator steps={getStepIndicatorSteps()} />
            </div>
          </div>
        )}
        
        {/* Main Content */}
        <main className="max-w-6xl mx-auto">
          {renderCurrentStep()}
        </main>
      </div>
    </div>
  );
}
