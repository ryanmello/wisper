"use client";

import { useState, useEffect, useCallback } from "react";
import { NavigationHeader, StepIndicator } from "@/components/ui/navigation";
import RepositorySelector from "@/components/RepositorySelector";
import TaskSelector from "@/components/TaskSelector";
import TaskExecution from "@/components/TaskExecution";
import SmartTaskExecution from "@/components/SmartTaskExecution";
import Results from "@/components/TaskResults";
import { TaskType, AnalysisProgress, SmartAnalysisResults } from "@/lib/api";
import { getRepoName, scrollToTop } from "@/lib/utils";

type Step = "repository" | "task" | "execution" | "smart-execution" | "results";



const STEPS = [
  {
    id: "repository",
    label: "Repository",
    description: "Select source",
  },
  {
    id: "task",
    label: "Task",
    description: "Choose analysis",
  },
  {
    id: "execution",
    label: "Execution",
    description: "Run analysis",
  },
  {
    id: "results",
    label: "Results",
    description: "View findings",
  },
];

export default function Home() {
  const [currentStep, setCurrentStep] = useState<Step>("repository");
  const [selectedRepository, setSelectedRepository] = useState<string>("");
  const [selectedTask, setSelectedTask] = useState<TaskType | null>(null);
  const [smartAnalysisContext, setSmartAnalysisContext] = useState<string>("");

  const [analysisResults, setAnalysisResults] = useState<
    AnalysisProgress["results"] | SmartAnalysisResults | null
  >(null);

  useEffect(() => {
    scrollToTop();
  }, [currentStep]);

  const handleRepositorySelect = (repo: string) => {
    setSelectedRepository(repo);
    setCurrentStep("task");
    scrollToTop();
  };

  const handleTaskSelect = (task: TaskType | null) => {
    setSelectedTask(task);
  };

  const handleStartTask = () => {
    setCurrentStep("execution");
    scrollToTop();
  };

  const handleStartSmartTask = (context: string) => {
    setSmartAnalysisContext(context);
    setCurrentStep("smart-execution");
    scrollToTop();
  };

  const handleTaskComplete = useCallback(
    (results: AnalysisProgress["results"] | SmartAnalysisResults) => {
      setAnalysisResults(results);
      setCurrentStep("results");
      scrollToTop();
    },
    []
  );

  const handleNewAnalysis = () => {
    setCurrentStep("task");
    setSelectedTask(null);
    setSmartAnalysisContext("");
    setAnalysisResults(null);
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
        break;
      case "results":
        setCurrentStep("task");
        setAnalysisResults(null);
        break;
      default:
        setCurrentStep("repository");
        break;
    }
    scrollToTop();
  };

  const getNavigationProps = () => {
    switch (currentStep) {
      case "repository":
        return {
          title: "Whisper AI Assistant",
          subtitle:
            "Connect your repository to get started with AI-powered code analysis",
          breadcrumbs: [{ label: "Home", current: true }],
        };

      case "task":
        return {
          title: "Choose Analysis Type",
          subtitle: `Analyzing: ${selectedRepository}`,
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Task Selection", current: true },
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
            { label: "Execution", current: true },
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
            { label: "Smart Analysis", current: true },
          ],
          onBack: handleBack,
        };

      case "results":
        return {
          title: "Analysis Results",
          subtitle: `Repository: ${getRepoName(selectedRepository)}`,
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Task Selection", href: "/task" },
            { label: "Execution", href: "/execution" },
            { label: "Results", current: true },
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
    return STEPS.map((step) => ({
      ...step,
      status:
        currentStep === step.id
          ? ("current" as const)
          : getStepIndex(currentStep) > getStepIndex(step.id)
          ? ("completed" as const)
          : ("upcoming" as const),
    }));
  };

  const getStepIndex = (step: string) => {
    const stepMap: Record<string, number> = {
      repository: 0,
      task: 1,
      execution: 2,
      "smart-execution": 2,
      results: 3,
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

  const renderCurrentStep = () => {
    switch (currentStep) {
      case "repository":
        return <RepositorySelector onRepoSelect={handleRepositorySelect} />;

      case "task":
        return (
          <TaskSelector
            repository={selectedRepository}
            onTaskSelect={handleTaskSelect}
            onStartTask={handleStartTask}
            onStartSmartTask={handleStartSmartTask}
            selectedTask={selectedTask}
          />
        );

      case "execution":
        return (
          <TaskExecution
            repository={selectedRepository}
            task={selectedTask || "explore-codebase"}
            onBack={handleBack}
            onComplete={handleTaskComplete}
          />
        );

      case "smart-execution":
        return (
          <SmartTaskExecution
            repository={selectedRepository}
            context={smartAnalysisContext}
            onBack={handleBack}
            onComplete={handleTaskComplete}
          />
        );

      case "results":
        return (
          <Results
            repository={selectedRepository}
            taskType={selectedTask || "smart-analysis"}
            results={analysisResults}
            onBack={handleBack}
            onNewAnalysis={handleNewAnalysis}
          />
        );

      default:
        return <RepositorySelector onRepoSelect={handleRepositorySelect} />;
    }
  };

  return (
    <div className="min-h-screen">
      <NavigationHeader {...getNavigationProps()} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {
          <div className="mb-8">
            <div className="mx-auto">
              <StepIndicator steps={getStepIndicatorSteps()} />
            </div>
          </div>
        }

        <main className="mx-auto">{renderCurrentStep()}</main>
      </div>
    </div>
  );
}
