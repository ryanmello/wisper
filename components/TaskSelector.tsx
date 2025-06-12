"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { WhisperAPI, generateContextSuggestions, ToolRegistryInfo, TaskType } from "@/lib/api";
import { Zap, Brain, Clock, Target, Settings2, Lightbulb } from "lucide-react";

interface TaskSelectorProps {
  repository: string;
  onTaskSelect: (task: TaskType | null) => void;
  onStartTask: () => void;
  onStartSmartTask: (context: string, options?: any) => void;
  selectedTask: TaskType | null;
}

interface SmartAnalysisOptions {
  scope?: 'full' | 'security_focused' | 'performance_focused';
  depth?: 'surface' | 'deep' | 'comprehensive';
  target_languages?: string[];
}

interface DetectedIntent {
  type: string;
  confidence: number;
  keywords: string[];
  suggestedScope: 'full' | 'security_focused' | 'performance_focused';
}

interface AIAnalysis {
  intents: DetectedIntent[];
  complexity: 'simple' | 'moderate' | 'complex';
  recommendation: string;
  estimatedTime: string;
  suggestedApproach: 'single_analysis' | 'multiple_focused' | 'comprehensive';
}

// AI-powered intent analysis function
async function analyzeIntentWithAI(context: string, repoUrl: string): Promise<AIAnalysis | null> {
  if (!context.trim() || context.length < 10) return null;

  try {
    // Get the API base URL from environment or default to localhost
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // Call the backend API instead of frontend route
    const response = await fetch(`${API_BASE_URL}/api/analyze-intent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        context,
        repository: repoUrl,
        maxTokens: 200
      }),
    });

    if (!response.ok) {
      throw new Error('AI analysis failed');
    }

    return await response.json();
  } catch (error) {
    console.error('AI intent analysis failed:', error);
    return null;
  }
}

// All task types - including future ones for inspiration and planning
const suggestedTasks = [
  {
    id: "explore-codebase",
    title: "Explore Codebase",
    description: "Get a comprehensive overview of the repository structure, main components, and architecture patterns",
    icon: "🔍",
    difficulty: "Easy",
    estimatedTime: "5-10 min",
    category: "Analysis",
    isAvailable: true,
  },
  {
    id: "dependency-audit",
    title: "Dependency Audit",
    description: "Review project dependencies for security vulnerabilities and automatically create PR with fixes",
    icon: "📦",
    difficulty: "Medium",
    estimatedTime: "8-12 min",
    category: "Security",
    isAvailable: true,
  },
  {
    id: "find-bugs",
    title: "Find Potential Bugs",
    description: "Scan the codebase for common programming errors, edge cases, and potential runtime issues",
    icon: "🐛",
    difficulty: "Medium",
    estimatedTime: "10-15 min",
    category: "Quality",
    isAvailable: false,
  },
  {
    id: "security-audit",
    title: "Security Audit",
    description: "Review code for security vulnerabilities, exposed secrets, and unsafe practices",
    icon: "🔒",
    difficulty: "Hard",
    estimatedTime: "15-20 min",
    category: "Security",
    isAvailable: false,
  },
  {
    id: "performance-review",
    title: "Performance Review",
    description: "Identify performance bottlenecks, memory leaks, and optimization opportunities",
    icon: "⚡",
    difficulty: "Medium",
    estimatedTime: "10-15 min",
    category: "Performance",
    isAvailable: false,
  },
  {
    id: "documentation-check",
    title: "Documentation Review",
    description: "Analyze code documentation completeness and suggest improvements",
    icon: "📚",
    difficulty: "Easy",
    estimatedTime: "5-10 min",
    category: "Documentation",
    isAvailable: false,
  },
  {
    id: "test-coverage",
    title: "Test Coverage Analysis",
    description: "Review existing tests and identify areas that need better test coverage",
    icon: "🧪",
    difficulty: "Medium",
    estimatedTime: "10-15 min",
    category: "Testing",
    isAvailable: false,
  },
  {
    id: "code-style",
    title: "Code Style Review",
    description: "Check code formatting, naming conventions, and style consistency",
    icon: "🎨",
    difficulty: "Easy",
    estimatedTime: "5-8 min",
    category: "Style",
    isAvailable: false,
  },
];

export default function TaskSelector({ 
  repository, 
  onTaskSelect, 
  onStartTask,
  onStartSmartTask,
  selectedTask, 
}: TaskSelectorProps) {
  
  const [analysisMode, setAnalysisMode] = useState<'quick' | 'smart'>('quick');
  const [toolsInfo, setToolsInfo] = useState<ToolRegistryInfo | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Enhanced Smart Analysis state with AI
  const [context, setContext] = useState("");
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [options, setOptions] = useState<SmartAnalysisOptions>({
    scope: 'full',
    depth: 'comprehensive',
    target_languages: []
  });

  // AI-powered intent detection
  const [aiAnalysis, setAIAnalysis] = useState<AIAnalysis | null>(null);
  const [isAnalyzingIntent, setIsAnalyzingIntent] = useState(false);

  // Helper function to scroll to top smoothly
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  // Generate context suggestions
  const suggestions = generateContextSuggestions(repository);

  // Load tools information (optional - for showing available tools)
  useEffect(() => {
    const loadToolsInfo = async () => {
      try {
        const info = await WhisperAPI.getToolsRegistry();
        setToolsInfo(info);
      } catch (error) {
        console.log('Tools registry not available:', error);
      }
    };

    loadToolsInfo();
  }, []);

  // Scroll to top when component mounts or analysis mode changes
  useEffect(() => {
    scrollToTop();
  }, [analysisMode]);

  // Manual AI intent analysis function
  const analyzeIntentManually = async () => {
    if (!context.trim() || context.length < 10) {
      return;
    }

    setIsAnalyzingIntent(true);
    try {
      const analysis = await analyzeIntentWithAI(context, repository);
      setAIAnalysis(analysis);
      
      // Auto-configure options based on AI analysis
      if (analysis && analysis.intents.length > 0) {
        const primaryIntent = analysis.intents[0];
        setOptions(prev => ({ 
          ...prev, 
          scope: primaryIntent.suggestedScope,
          depth: analysis.complexity === 'complex' ? 'comprehensive' : 'deep'
        }));
      }
    } catch (error) {
      console.error('Intent analysis failed:', error);
      // Fallback to simple keyword detection
      fallbackToSimpleDetection(context);
    } finally {
      setIsAnalyzingIntent(false);
    }
  };

  // Clear AI analysis when context changes significantly
  useEffect(() => {
    // Reset analysis when context is cleared or significantly changed
    if (!context.trim()) {
      setAIAnalysis(null);
    }
  }, [context]);

  // Fallback to simple keyword detection if AI fails
  const fallbackToSimpleDetection = (text: string) => {
    const contextLower = text.toLowerCase();
    const detectedIntents: DetectedIntent[] = [];

    if (contextLower.includes('security') || contextLower.includes('vulnerabilit')) {
      detectedIntents.push({
        type: 'Security Analysis',
        confidence: 0.8,
        keywords: ['security', 'vulnerability'],
        suggestedScope: 'security_focused'
      });
    }
    
    if (contextLower.includes('performance') || contextLower.includes('optimization')) {
      detectedIntents.push({
        type: 'Performance Analysis',
        confidence: 0.8,
        keywords: ['performance', 'optimization'],
        suggestedScope: 'performance_focused'
      });
    }

    if (contextLower.includes('explore') || contextLower.includes('architecture')) {
      detectedIntents.push({
        type: 'Codebase Exploration',
        confidence: 0.7,
        keywords: ['explore', 'architecture'],
        suggestedScope: 'full'
      });
    }

    if (detectedIntents.length > 0) {
      setAIAnalysis({
        intents: detectedIntents,
        complexity: detectedIntents.length > 1 ? 'moderate' : 'simple',
        recommendation: detectedIntents.length > 1 
          ? 'Multiple analysis goals detected. Consider running a comprehensive analysis.'
          : 'Single analysis goal detected.',
        estimatedTime: '10-20 min',
        suggestedApproach: detectedIntents.length > 1 ? 'comprehensive' : 'single_analysis'
      });
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "Easy": return "bg-green-100 text-green-800";
      case "Medium": return "bg-yellow-100 text-yellow-800";
      case "Hard": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      Analysis: "bg-blue-100 text-blue-800",
      Quality: "bg-purple-100 text-purple-800",
      Security: "bg-red-100 text-red-800",
      Performance: "bg-orange-100 text-orange-800",
      Documentation: "bg-indigo-100 text-indigo-800",
      Testing: "bg-green-100 text-green-800",
      Style: "bg-pink-100 text-pink-800",
      Dependencies: "bg-cyan-100 text-cyan-800",
    };
    return colors[category] || "bg-gray-100 text-gray-800";
  };

  // Smart Analysis helper functions
  const handleSuggestionClick = (suggestion: string) => {
    setContext(suggestion);
    setSelectedSuggestion(suggestion);
  };

  const handleSmartSubmit = () => {
    if (!context.trim()) return;
    
    setIsAnalyzing(true);
    onStartSmartTask(context, options);
  };

  const handleCustomInput = (value: string) => {
    setContext(value);
    setSelectedSuggestion(null);
  };

  // Mode switching handlers
  const handleQuickModeSelect = () => {
    setAnalysisMode('quick');
    // Clear smart analysis state when switching to quick mode
    setContext("");
    setSelectedSuggestion(null);
    setIsAnalyzing(false);
    setShowAdvanced(false);
  };

  const handleSmartModeSelect = () => {
    setAnalysisMode('smart');
    // No need to clear task selection - smart mode operates independently
  };

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-foreground mb-2">Choose Your Analysis Approach</h2>
        <p className="text-muted-foreground mx-auto">
          Select between quick predefined tasks or smart AI-powered analysis tailored to your specific needs
        </p>
      </div>

      {/* Analysis Type Selection - Enhanced Design */}
      <div>
        <div className="grid md:grid-cols-2 gap-6 max-w-6xl mx-auto">
          {/* Quick Tasks Mode */}
          <div className={`group relative p-6 rounded-2xl border-2 cursor-pointer transition-all duration-300 ${
            analysisMode === 'quick' 
              ? 'border-primary bg-primary/5 shadow-lg shadow-primary/20' 
              : 'border-border hover:border-primary/50 hover:shadow-md'
          }`}
          onClick={handleQuickModeSelect}
          >
            <div className="flex items-start space-x-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${
                analysisMode === 'quick' 
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary'
              }`}>
                <Zap className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h3 className="text-xl font-semibold text-foreground">Quick Tasks</h3>
                  {analysisMode === 'quick' && (
                    <Badge className="bg-primary text-primary-foreground">Selected</Badge>
                  )}
                </div>
                <p className="text-muted-foreground mb-4">
                  Choose from expertly crafted analysis templates. Fast setup with proven methodologies.
                </p>
                <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                  <div className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>5-20 min</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Target className="w-4 h-4" />
                    <span>Pre-configured</span>
                  </div>
                </div>
              </div>
            </div>
            {analysisMode === 'quick' && (
              <div className="absolute top-4 right-4">
                <div className="w-3 h-3 bg-primary rounded-full"></div>
              </div>
            )}
          </div>

          {/* Smart Analysis Mode */}
          <div className={`group relative p-6 rounded-2xl border-2 cursor-pointer transition-all duration-300 ${
            analysisMode === 'smart' 
              ? 'border-primary bg-primary/5 shadow-lg shadow-primary/20' 
              : 'border-border hover:border-primary/50 hover:shadow-md'
          }`}
          onClick={handleSmartModeSelect}
          >
            <div className="flex items-start space-x-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${
                analysisMode === 'smart'
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary'
              }`}>
                <Brain className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h3 className="text-xl font-semibold text-foreground">Smart Analysis</h3>
                  {analysisMode === 'smart' && (
                    <Badge className="bg-primary text-primary-foreground">Selected</Badge>
                  )}
                </div>
                <p className="text-muted-foreground mb-4">
                  Describe your goals naturally. AI selects optimal tools and creates custom analysis workflows.
                </p>
                <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                  <div className="flex items-center space-x-1">
                    <Brain className="w-4 h-4" />
                    <span>AI-powered</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Settings2 className="w-4 h-4" />
                    <span>Customizable</span>
                  </div>
                </div>
              </div>
            </div>
            {analysisMode === 'smart' && (
              <div className="absolute top-4 right-4">
                <div className="w-3 h-3 bg-primary rounded-full"></div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Smart Analysis Interface */}
      {analysisMode === 'smart' && (
        <div className="space-y-6">
          {/* Context Input */}
          <Card className="shadow-sm">
            <CardHeader className="pb-4">
              <div className="flex items-center space-x-2">
                <Brain className="w-5 h-5 text-primary" />
                <CardTitle>Describe Your Analysis Goals</CardTitle>
              </div>
              <CardDescription>
                Tell us what you want to discover about your codebase. Our AI will design the perfect analysis strategy.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <textarea
                value={context}
                onChange={(e) => handleCustomInput(e.target.value)}
                placeholder="e.g., 'Find security vulnerabilities in this web application' or 'Analyze the architecture and identify performance bottlenecks'"
                className="w-full h-32 p-4 border border-border rounded-xl resize-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors bg-background text-foreground placeholder:text-muted-foreground"
                disabled={isAnalyzing}
              />
              
              {/* AI Analysis Trigger Button */}
              <div className="flex items-center justify-between mt-3">
                <div className="text-sm text-muted-foreground">
                  {context.length < 10 ? (
                    <span>Enter at least 10 characters for AI analysis</span>
                  ) : (
                    <span>Ready for AI intent analysis • {context.length} characters</span>
                  )}
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={analyzeIntentManually}
                  disabled={isAnalyzingIntent || context.length < 10 || isAnalyzing}
                  className="ml-3"
                >
                  {isAnalyzingIntent ? (
                    <>
                      <div className="animate-spin w-4 h-4 border-2 border-primary border-t-transparent rounded-full mr-2"></div>
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4 mr-2" />
                      Analyze Intent
                    </>
                  )}
                </Button>
              </div>
              
              {aiAnalysis && (
                <div className="mt-4 space-y-4">
                  {/* Multiple Detected Intents */}
                  <div className="p-4 bg-primary/10 rounded-lg border border-primary/20">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <Target className="w-4 h-4 text-primary" />
                        <span className="text-sm font-medium text-primary">AI Analysis Results:</span>
                      </div>
                      {/* Option to re-analyze */}
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={analyzeIntentManually}
                        disabled={isAnalyzingIntent || isAnalyzing}
                        className="text-xs h-6 px-2"
                      >
                        Re-analyze
                      </Button>
                    </div>
                    
                    <div className="space-y-3">
                      {/* Show all detected intents */}
                      <div className="flex flex-wrap gap-2">
                        {aiAnalysis.intents.map((intent, index) => (
                          <Badge 
                            key={index}
                            variant="outline" 
                            className="bg-primary/10 text-primary border-primary/30"
                          >
                            {intent.type} ({Math.round(intent.confidence * 100)}%)
                          </Badge>
                        ))}
                      </div>

                      {/* Complexity and recommendation */}
                      <div className="text-sm text-muted-foreground">
                        <div className="flex items-center space-x-2 mb-1">
                          <Lightbulb className="w-4 h-4" />
                          <span className="font-medium">Complexity:</span>
                          <Badge variant="secondary" className={
                            aiAnalysis.complexity === 'complex' ? 'bg-orange-100 text-orange-800' :
                            aiAnalysis.complexity === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }>
                            {aiAnalysis.complexity}
                          </Badge>
                          <span>• Est. {aiAnalysis.estimatedTime}</span>
                        </div>
                      </div>

                      {/* AI Recommendation */}
                      <div className="text-sm bg-background/50 rounded p-3 border-l-4 border-primary">
                        <span className="font-medium">AI Recommendation:</span>
                        <p className="mt-1">{aiAnalysis.recommendation}</p>
                      </div>

                      {/* Multiple intents warning */}
                      {aiAnalysis.intents.length > 1 && (
                        <div className="text-sm bg-amber-50 border border-amber-200 rounded p-3">
                          <div className="flex items-start space-x-2">
                            <Lightbulb className="w-4 h-4 text-amber-600 mt-0.5" />
                            <div>
                              <span className="font-medium text-amber-800">Multiple Goals Detected</span>
                              <p className="text-amber-700 mt-1">
                                Your request involves {aiAnalysis.intents.length} different analysis types. 
                                {aiAnalysis.suggestedApproach === 'comprehensive' 
                                  ? ' A comprehensive analysis will address all goals in one run.'
                                  : ' Consider running focused analyses for each goal.'
                                }
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Suggestions */}
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg flex items-center space-x-2">
                <Zap className="w-5 h-5 text-primary" />
                <span>Quick Start Suggestions</span>
              </CardTitle>
              <CardDescription>
                Choose from these common analysis scenarios to get started quickly
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {suggestions.map((suggestion, index) => (
                  <Button
                    key={index}
                    variant={selectedSuggestion === suggestion ? "default" : "outline"}
                    className="h-auto p-4 text-left justify-start hover:shadow-sm transition-all"
                    onClick={() => handleSuggestionClick(suggestion)}
                    disabled={isAnalyzing}
                  >
                    <span className="text-sm leading-relaxed">{suggestion}</span>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Advanced Options */}
          <Card className="shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Settings2 className="w-5 h-5 text-primary" />
                  <div>
                    <CardTitle className="text-lg">Advanced Configuration</CardTitle>
                    <CardDescription>Fine-tune analysis parameters for optimal results</CardDescription>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  disabled={isAnalyzing}
                  className="hover:bg-muted/50"
                >
                  {showAdvanced ? "Hide" : "Show"} Options
                </Button>
              </div>
            </CardHeader>
            
            {showAdvanced && (
              <CardContent className="space-y-6">
                {/* Scope Selection */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-3">
                    Analysis Scope
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {(['full', 'security_focused', 'performance_focused'] as const).map((scope) => (
                      <Button
                        key={scope}
                        variant={options.scope === scope ? "default" : "outline"}
                        onClick={() => setOptions(prev => ({ ...prev, scope }))}
                        disabled={isAnalyzing}
                        className="h-auto p-4 flex-col space-y-1"
                      >
                        <span className="font-medium">
                          {scope === 'full' ? 'Comprehensive' : 
                           scope === 'security_focused' ? 'Security Focus' : 'Performance Focus'}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {scope === 'full' ? 'Complete analysis' : 
                           scope === 'security_focused' ? 'Security-first approach' : 'Performance optimization'}
                        </span>
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Depth Selection */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-3">
                    Analysis Depth
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {(['surface', 'deep', 'comprehensive'] as const).map((depth) => (
                      <Button
                        key={depth}
                        variant={options.depth === depth ? "default" : "outline"}
                        onClick={() => setOptions(prev => ({ ...prev, depth }))}
                        disabled={isAnalyzing}
                        className="h-auto p-4 flex-col space-y-1"
                      >
                        <span className="font-medium capitalize">{depth}</span>
                        <span className="text-xs text-muted-foreground">
                          {depth === 'surface' ? 'Quick overview' : 
                           depth === 'deep' ? 'Detailed analysis' : 'Exhaustive review'}
                        </span>
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Available Tools Info */}
                {toolsInfo && (
                  <div className="p-4 bg-muted/50 rounded-xl border">
                    <h4 className="text-sm font-medium text-foreground mb-3">Available Analysis Tools</h4>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {Object.keys(toolsInfo.tools).map((toolName) => (
                        <Badge
                          key={toolName}
                          variant="secondary"
                          className={toolsInfo.tools[toolName].healthy ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}
                        >
                          {toolName.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {toolsInfo.healthy_tools} of {toolsInfo.total_tools} tools available for analysis
                    </p>
                  </div>
                )}
              </CardContent>
            )}
          </Card>

          {/* Smart Analysis Action Button */}
          <div className="flex justify-center pt-6">
            <Button
              onClick={handleSmartSubmit}
              disabled={!context.trim() || isAnalyzing}
              size="lg"
              className="bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? (
                <>
                  <div className="animate-spin -ml-1 mr-3 h-5 w-5 border-2 border-primary-foreground border-t-transparent rounded-full"></div>
                  Starting Analysis...
                </>
              ) : (
                <>
                  <Brain className="w-4 h-4 mr-2" />
                  Start Analysis
                </>
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Quick Tasks Grid */}
      {analysisMode === 'quick' && (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-2xl font-semibold text-foreground mb-2">Select Analysis Task</h3>
            <p className="text-muted-foreground">Choose from our collection of proven analysis workflows</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {suggestedTasks.map((task) => (
              <Card 
                key={task.id}
                className={`transition-all duration-200 group ${
                  task.isAvailable 
                    ? 'cursor-pointer hover:shadow-lg' 
                    : 'cursor-not-allowed opacity-50'
                } ${
                  selectedTask === task.id 
                    ? 'ring-2 ring-primary border-primary shadow-lg shadow-primary/20 bg-primary/5' 
                    : task.isAvailable 
                      ? 'border-border hover:border-primary/50' 
                      : 'border-border'
                }`}
                onClick={() => {
                  if (task.isAvailable && (task.id === 'explore-codebase' || task.id === 'dependency-audit')) {
                    onTaskSelect(task.id as TaskType);
                  }
                }}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between mb-3">
                    <div className="text-3xl">{task.icon}</div>
                    <div className="flex flex-col gap-2">
                      <Badge className={getDifficultyColor(task.difficulty)} variant="secondary">
                        {task.difficulty}
                      </Badge>
                    </div>
                  </div>
                  <CardTitle className={`text-lg transition-colors ${
                    task.isAvailable 
                      ? 'group-hover:text-primary' 
                      : ''
                  }`}>
                    {task.title}
                  </CardTitle>
                  <CardDescription className="text-sm leading-relaxed">
                    {task.description}
                  </CardDescription>
                </CardHeader>
                
                <CardContent className="pt-0">
                  <Separator className="mb-4" />
                  <div className="flex items-center justify-between text-sm">
                    <Badge className={getCategoryColor(task.category)} variant="outline">
                      {task.category}
                    </Badge>
                    <div className="flex items-center space-x-1 text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      <span>{task.estimatedTime}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Quick Task Action Button */}
          <div className="flex justify-center pt-6">
            <Button 
              onClick={onStartTask} 
              disabled={!selectedTask}
              size="lg"
              className="bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Zap className="w-4 h-4 mr-2" />
              Start Analysis
            </Button>
          </div>
        </div>
      )}
    </div>
  );
} 