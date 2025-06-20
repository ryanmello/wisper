"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  CheckCircle, 
  AlertTriangle, 
  Info, 
  Download,
  Clock,
  FileText,
  BarChart3,
  Shield,
  Zap
} from "lucide-react";
import { AnalysisProgress, SmartAnalysisResults, extractRepoName } from "@/lib/api";

interface ResultsProps {
  repository: string;
  taskType?: string;
  results: AnalysisProgress['results'] | SmartAnalysisResults | null;
  onBack: () => void;
  onNewAnalysis: () => void;
}

export default function Results({ 
  repository, 
  taskType,
  results, 
  onBack, 
  onNewAnalysis 
}: ResultsProps) {
  const repoName = extractRepoName(repository);
  const isSmartAnalysis = !taskType || taskType === 'smart-analysis';

  const getTaskIcon = (task?: string) => {
    switch (task) {
      case 'explore-codebase':
        return <FileText className="w-5 h-5" />;
      case 'dependency-audit':
        return <Shield className="w-5 h-5" />;
      default:
        return <BarChart3 className="w-5 h-5" />;
    }
  };

  const getTaskTitle = (task?: string) => {
    switch (task) {
      case 'explore-codebase':
        return 'Codebase Exploration';
      case 'dependency-audit':
        return 'Dependency Audit';
      default:
        return 'Smart Analysis';
    }
  };

  const renderTraditionalResults = (data: AnalysisProgress['results']) => {
    if (!data) return null;

    const { summary, statistics, detailed_results } = data;
    
    // Handle both possible data structures
    const analysis = detailed_results?.whisper_analysis || detailed_results;

    return (
      <div className="space-y-8">
        {/* Summary Section */}
        <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-xl">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Info className="w-5 h-5 text-blue-600" />
              </div>
              Executive Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="prose prose-gray max-w-none">
              <p className="text-gray-700 leading-relaxed text-base">{summary}</p>
            </div>
          </CardContent>
        </Card>

        {/* Statistics */}
        {statistics && (
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                </div>
                Analysis Statistics
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(statistics).map(([key, value]) => (
                  <div key={key} className="text-center p-4 bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl border border-slate-200 hover:shadow-md transition-shadow">
                    <div className="text-3xl font-bold text-slate-800 mb-1">{value}</div>
                    <div className="text-sm text-slate-600 capitalize font-medium">
                      {key.replace(/_/g, ' ')}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* AI Analysis Insights - New Section */}
        {analysis && ((analysis as any).ai_summary || (analysis as any).analysis) && (
          <Card className="shadow-lg border-0 bg-blue-50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl">
                <div className="p-2 bg-blue-600 rounded-lg shadow-md">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                AI Analysis Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-6">
                {/* Display analysis string if it exists */}
                {typeof (analysis as any).analysis === 'string' && (
                  <div className="prose prose-blue max-w-none">
                    <p className="text-gray-800 leading-relaxed whitespace-pre-wrap bg-white p-4 rounded-lg border">{(analysis as any).analysis}</p>
                  </div>
                )}
                {/* Display structured ai_summary if it exists */}
                {typeof (analysis as any).ai_summary === 'string' ? (
                  <div className="prose prose-blue max-w-none">
                    <p className="text-gray-800 leading-relaxed bg-white/60 p-4 rounded-lg border">{(analysis as any).ai_summary}</p>
                  </div>
                ) : (analysis as any).ai_summary && (
                  <div className="space-y-3">
                    {(analysis as any).ai_summary?.key_findings && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Key Findings</h4>
                        <ul className="space-y-1 text-gray-700">
                          {(analysis as any).ai_summary.key_findings.map((finding: string, index: number) => (
                            <li key={index} className="flex items-start gap-2">
                              <span className="text-blue-500 mt-1">•</span>
                              <span>{finding}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {(analysis as any).ai_summary?.recommendations && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Recommendations</h4>
                        <ul className="space-y-1 text-gray-700">
                          {(analysis as any).ai_summary.recommendations.map((rec: string, index: number) => (
                            <li key={index} className="flex items-start gap-2">
                              <span className="text-green-500 mt-1">•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Pull Request Information for Dependency Audit */}
        {taskType === 'dependency-audit' && analysis && (analysis as any).pull_request_url && (
          <Card className="shadow-lg border-0 bg-green-50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl text-green-800">
                <div className="p-2 bg-green-500 rounded-lg shadow-md">
                  <CheckCircle className="w-5 h-5 text-white" />
                </div>
                Pull Request Created Successfully
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-green-700">
                  A pull request has been automatically created with dependency fixes and updates.
                </p>
                <div className="flex items-center gap-3">
                  <a 
                    href={(analysis as any).pull_request_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"></path>
                      <path d="M5 5a2 2 0 00-2 2v6a2 2 0 002 2h6a2 2 0 002-2v-1a1 1 0 10-2 0v1H5V7h1a1 1 0 000-2H5z"></path>
                    </svg>
                    View Pull Request
                  </a>
                  {(analysis as any).pr_number && (
                    <Badge variant="outline" className="bg-green-100 text-green-800">
                      PR #{(analysis as any).pr_number}
                    </Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Detailed Analysis */}
        {analysis && (
          <>
            {/* Architecture Patterns */}
            {analysis.architecture_patterns && analysis.architecture_patterns.length > 0 && (
              <Card className="shadow-lg border-0 bg-white">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-3 text-xl">
                    <div className="p-2 bg-indigo-100 rounded-lg">
                      <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                    </div>
                    Architecture Patterns
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex flex-wrap gap-3">
                    {analysis.architecture_patterns.map((pattern, index) => (
                      <Badge 
                        key={index} 
                        variant="outline" 
                        className="px-4 py-2 bg-gradient-to-r from-indigo-50 to-blue-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100 transition-colors text-sm font-medium"
                      >
                        {pattern}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Main Components */}
            {analysis.main_components && analysis.main_components.length > 0 && (
              <Card className="shadow-lg border-0 bg-white">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-3 text-xl">
                    <div className="p-2 bg-orange-100 rounded-lg">
                      <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                    </div>
                    Key Components
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-4">
                    {analysis.main_components.map((component: any, index) => (
                      <div key={index} className="p-4 border border-gray-200 rounded-xl bg-gray-50 hover:shadow-md transition-shadow">
                        <div className="font-semibold text-gray-900 text-lg">{component.name || `Component ${index + 1}`}</div>
                        {component.description && (
                          <div className="text-gray-700 mt-2 leading-relaxed">{component.description}</div>
                        )}
                        {component.path && (
                          <div className="text-xs text-gray-500 mt-2 font-mono bg-gray-100 px-2 py-1 rounded inline-block">{component.path}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Language Analysis */}
            {analysis.language_analysis && (
              <Card className="shadow-lg border-0 bg-white">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-3 text-xl">
                    <div className="p-2 bg-green-100 rounded-lg">
                      <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                      </svg>
                    </div>
                    Language Breakdown
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-3">
                    {Object.entries(analysis.language_analysis).map(([lang, info]: [string, any]) => (
                      <div key={lang} className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200 hover:shadow-md transition-shadow">
                        <span className="font-semibold text-gray-900 text-lg">{lang}</span>
                        <div className="text-right">
                          <span className="text-lg font-bold text-green-700">
                            {typeof info === 'object' ? info.files || info.count : info}
                          </span>
                          <span className="text-sm text-green-600 ml-1">files</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    );
  };

  const renderSmartResults = (data: SmartAnalysisResults) => {
    return (
      <div className="space-y-6">
        {/* Summary Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5" />
              AI Analysis Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 leading-relaxed">{data.summary}</p>
          </CardContent>
        </Card>

        {/* Vulnerability Summary */}
        {data.vulnerability_summary && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Security Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">
                    {data.vulnerability_summary.critical_vulnerabilities}
                  </div>
                  <div className="text-sm text-red-700">Critical</div>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {data.vulnerability_summary.high_vulnerabilities}
                  </div>
                  <div className="text-sm text-orange-700">High</div>
                </div>
                <div className="text-center p-3 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">
                    {data.vulnerability_summary.medium_vulnerabilities}
                  </div>
                  <div className="text-sm text-yellow-700">Medium</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {data.vulnerability_summary.low_vulnerabilities}
                  </div>
                  <div className="text-sm text-blue-700">Low</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-600">
                    {data.vulnerability_summary.total_vulnerabilities}
                  </div>
                  <div className="text-sm text-gray-700">Total</div>
                </div>
              </div>
              
              <div className="flex items-center gap-2 mb-3">
                <span className="text-sm font-medium">Risk Level:</span>
                <Badge 
                  variant={data.vulnerability_summary.risk_level === 'HIGH' ? 'destructive' : 
                          data.vulnerability_summary.risk_level === 'MEDIUM' ? 'secondary' : 'default'}
                >
                  {data.vulnerability_summary.risk_level}
                </Badge>
                <span className="text-sm text-gray-600">
                  (Score: {data.vulnerability_summary.risk_score}/100)
                </span>
              </div>

              {data.vulnerability_summary.affected_modules?.length > 0 && (
                <div>
                  <div className="text-sm font-medium mb-2">Affected Modules:</div>
                  <div className="flex flex-wrap gap-1">
                    {data.vulnerability_summary.affected_modules.map((module, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {module}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Recommendations */}
        {data.recommendations && data.recommendations.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data.recommendations.map((recommendation, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-yellow-800">{recommendation}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tool Results */}
        {data.tool_results && Object.keys(data.tool_results).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Detailed Tool Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(data.tool_results).map(([toolName, toolResult]: [string, any]) => (
                  <div key={toolName} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium capitalize">
                        {toolName.replace(/_/g, ' ')}
                      </h4>
                      <Badge variant="outline">
                        {toolResult.success ? 'Success' : 'Failed'}
                      </Badge>
                    </div>
                    {toolResult.summary && (
                      <p className="text-sm text-gray-600 mb-2">{toolResult.summary}</p>
                    )}
                    {toolResult.findings && Array.isArray(toolResult.findings) && (
                      <div className="text-sm">
                        <div className="font-medium mb-1">Key Findings:</div>
                        <ul className="list-disc list-inside space-y-1 text-gray-600">
                          {toolResult.findings.slice(0, 3).map((finding: string, index: number) => (
                            <li key={index}>{finding}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Metrics */}
        {data.metrics && Object.keys(data.metrics).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Analysis Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(data.metrics).map(([key, value]) => (
                  <div key={key} className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">{value}</div>
                    <div className="text-sm text-gray-600 capitalize">
                      {key.replace(/_/g, ' ')}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between flex-col lg:flex-row lg:items-center gap-6 mb-8">
            <div className="flex items-center gap-4">
              <Button 
                variant="ghost" 
                onClick={onBack}
                className="p-2 hover:bg-white/60 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Button>
              <div className="w-12 h-12 bg-gray-800 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-lg">W</span>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-3xl font-bold">
                    {getTaskTitle(taskType)} Results
                  </h1>
                </div>
                <p className="text-gray-600 text-lg">
                  Analysis completed for <span className="font-semibold text-gray-800">{repoName}</span>
                </p>
                <div className="flex flex-wrap items-center gap-4 mt-3">
                  <div className="flex items-center gap-2 px-3 py-1 bg-green-50 rounded-full border border-green-200">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-700">Analysis Complete</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <Button 
                variant="outline" 
                onClick={onNewAnalysis}
                className="bg-white/80 hover:bg-white border-gray-200 backdrop-blur-sm"
              >
                <Zap className="w-4 h-4 mr-2" />
                New Analysis
              </Button>
              <Button 
                variant="outline"
                className="bg-white/80 hover:bg-white border-gray-200 backdrop-blur-sm"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </div>

        {/* Results Content */}
        <div className="space-y-8">
          {results ? (
            isSmartAnalysis ? 
              renderSmartResults(results as SmartAnalysisResults) : 
              renderTraditionalResults(results as AnalysisProgress['results'])
          ) : (
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
              <CardContent className="text-center py-12">
                <div className="flex flex-col items-center gap-4">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
                    <AlertTriangle className="w-8 h-8 text-gray-400" />
                  </div>
                  <p className="text-gray-600 text-lg">No results available to display.</p>
                  <Button variant="outline" onClick={onNewAnalysis} className="mt-2">
                    Run New Analysis
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
} 
