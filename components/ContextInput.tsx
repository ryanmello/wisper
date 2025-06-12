"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { WhisperAPI, generateContextSuggestions, ToolRegistryInfo } from "@/lib/api";

interface ContextInputProps {
  repository: string;
  onContextSubmit: (context: string, options?: SmartAnalysisOptions) => void;
  onBack: () => void;
  detectedLanguage?: string;
}

interface SmartAnalysisOptions {
  scope?: 'full' | 'security_focused' | 'performance_focused';
  depth?: 'surface' | 'deep' | 'comprehensive';
  target_languages?: string[];
}

export default function ContextInput({ 
  repository, 
  onContextSubmit, 
  onBack, 
  detectedLanguage 
}: ContextInputProps) {
  const [context, setContext] = useState("");
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [options, setOptions] = useState<SmartAnalysisOptions>({
    scope: 'full',
    depth: 'comprehensive',
    target_languages: []
  });
  const [toolsInfo, setToolsInfo] = useState<ToolRegistryInfo | null>(null);
  const [detectedIntent, setDetectedIntent] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Generate context suggestions
  const suggestions = generateContextSuggestions(repository, detectedLanguage);

  // Load tools information
  useEffect(() => {
    const loadToolsInfo = async () => {
      try {
        const info = await WhisperAPI.getToolsRegistry();
        setToolsInfo(info);
      } catch (error) {
        console.error('Failed to load tools info:', error);
      }
    };

    loadToolsInfo();
  }, []);

  // Simple intent detection based on keywords
  useEffect(() => {
    if (!context) {
      setDetectedIntent(null);
      return;
    }

    const contextLower = context.toLowerCase();
    
    if (contextLower.includes('security') || contextLower.includes('vulnerabilit')) {
      setDetectedIntent('Security Analysis');
      setOptions(prev => ({ ...prev, scope: 'security_focused' }));
    } else if (contextLower.includes('performance') || contextLower.includes('optimization')) {
      setDetectedIntent('Performance Analysis');
      setOptions(prev => ({ ...prev, scope: 'performance_focused' }));
    } else if (contextLower.includes('explore') || contextLower.includes('architecture')) {
      setDetectedIntent('Codebase Exploration');
      setOptions(prev => ({ ...prev, scope: 'full' }));
    } else if (contextLower.includes('bug') || contextLower.includes('issue')) {
      setDetectedIntent('Code Quality Review');
      setOptions(prev => ({ ...prev, scope: 'full' }));
    } else {
      setDetectedIntent('General Analysis');
      setOptions(prev => ({ ...prev, scope: 'full' }));
    }
  }, [context]);

  const handleSuggestionClick = (suggestion: string) => {
    setContext(suggestion);
    setSelectedSuggestion(suggestion);
  };

  const handleSubmit = () => {
    if (!context.trim()) return;
    
    setIsAnalyzing(true);
    onContextSubmit(context, options);
  };

  const handleCustomInput = (value: string) => {
    setContext(value);
    setSelectedSuggestion(null);
  };

  const repoName = repository.match(/github\.com\/([^\/]+\/[^\/]+)/)?.[1] || repository;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-6">
            <Button 
              variant="ghost" 
              onClick={onBack}
              className="p-2"
              disabled={isAnalyzing}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Button>
            <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">W</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">🧠 Smart Analysis</h1>
              <p className="text-gray-600">
                Describe what you want to analyze in <strong>{repoName}</strong>
              </p>
            </div>
          </div>
        </div>

        {/* Context Input */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>What would you like to analyze?</CardTitle>
            <CardDescription>
              Describe your analysis goals in natural language. Our AI will select the best tools for your needs.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <textarea
              value={context}
              onChange={(e) => handleCustomInput(e.target.value)}
              placeholder="e.g., find security vulnerabilities in this Go web framework, or explore the architecture of this React app..."
              className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isAnalyzing}
            />
            
            {detectedIntent && (
              <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-blue-800">Detected Intent:</span>
                  <Badge variant="outline" className="bg-blue-100 text-blue-800">
                    {detectedIntent}
                  </Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Suggestions */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Quick Suggestions</CardTitle>
            <CardDescription>
              Click on any suggestion to use it as your analysis context
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {suggestions.map((suggestion, index) => (
                <Button
                  key={index}
                  variant={selectedSuggestion === suggestion ? "default" : "outline"}
                  className="h-auto p-3 text-left justify-start"
                  onClick={() => handleSuggestionClick(suggestion)}
                  disabled={isAnalyzing}
                >
                  <span className="text-sm">{suggestion}</span>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Advanced Options */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">Advanced Options</CardTitle>
                <CardDescription>Fine-tune your analysis parameters</CardDescription>
              </div>
              <Button
                variant="ghost"
                onClick={() => setShowAdvanced(!showAdvanced)}
                disabled={isAnalyzing}
              >
                {showAdvanced ? "Hide" : "Show"} Advanced
              </Button>
            </div>
          </CardHeader>
          
          {showAdvanced && (
            <CardContent>
              <div className="space-y-4">
                {/* Scope Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Analysis Scope
                  </label>
                  <div className="flex gap-2">
                    {(['full', 'security_focused', 'performance_focused'] as const).map((scope) => (
                      <Button
                        key={scope}
                        variant={options.scope === scope ? "default" : "outline"}
                        size="sm"
                        onClick={() => setOptions(prev => ({ ...prev, scope }))}
                        disabled={isAnalyzing}
                      >
                        {scope.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Depth Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Analysis Depth
                  </label>
                  <div className="flex gap-2">
                    {(['surface', 'deep', 'comprehensive'] as const).map((depth) => (
                      <Button
                        key={depth}
                        variant={options.depth === depth ? "default" : "outline"}
                        size="sm"
                        onClick={() => setOptions(prev => ({ ...prev, depth }))}
                        disabled={isAnalyzing}
                      >
                        {depth.charAt(0).toUpperCase() + depth.slice(1)}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Available Tools Info */}
                {toolsInfo && (
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Available Tools</h4>
                    <div className="flex flex-wrap gap-2">
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
                    <p className="text-xs text-gray-600 mt-2">
                      {toolsInfo.healthy_tools} of {toolsInfo.total_tools} tools available
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          )}
        </Card>

        {/* Action Button */}
        <div className="flex justify-center">
          <Button
            onClick={handleSubmit}
            disabled={!context.trim() || isAnalyzing}
            size="lg"
            className="px-8"
          >
            {isAnalyzing ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Starting Analysis...
              </>
            ) : (
              <>
                <span className="mr-2">🚀</span>
                Start Smart Analysis
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
} 