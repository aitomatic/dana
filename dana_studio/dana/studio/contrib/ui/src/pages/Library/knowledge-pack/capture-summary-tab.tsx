import { useState, useEffect } from 'react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Badge } from '@/components/ui/badge';
import { MarkdownViewerSmall } from '@/pages/Agents/chat/markdown-viewer';
import { NavArrowRight, NavArrowDown } from 'iconoir-react';
import { ClipboardX } from 'lucide-react';
import { apiService } from '@/lib/api';

// Type definitions based on analysis_data.json structure
interface Session {
  session: string;
  expert_insight: string;
  status: 'not_started' | 'in_progress' | 'completed';
  insights_count: number;
}

interface Topic {
  sessions: Session[];
  unified_report: string;
}

interface Template {
  template_id: number;
  template_name: string;
  topics: Record<string, Topic>;
  total_topics: number;
  total_sessions: number;
}

interface AnalysisData {
  kp_id: number;
  generated_at: string;
  templates: Template[];
}

interface CaptureSummaryTabProps {
  knowledgePackId: number;
}


// Helper function to get status badge styling
const getStatusBadge = (status: Session['status']) => {
  switch (status) {
    case 'not_started':
      return (
        <Badge variant="outline" className="bg-gray-50 text-gray-600 border-gray-300">
          Not Started
        </Badge>
      );
    case 'in_progress':
      return (
        <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-300">
          In Progress
        </Badge>
      );
    case 'completed':
      return (
        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
          Completed
        </Badge>
      );
    default:
      return null;
  }
};

// Helper function to check if topic has any insights
const topicHasInsights = (topic: Topic): boolean => {
  return topic.sessions.some((session) => session.insights_count > 0);
};

// Helper function to get total insights count for a topic
const getTopicInsightsCount = (topic: Topic): number => {
  return topic.sessions.reduce((total, session) => total + session.insights_count, 0);
};

export function CaptureSummaryTab({ knowledgePackId }: CaptureSummaryTabProps) {
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Template-level expanded state
  const [expandedTemplates, setExpandedTemplates] = useState<Set<number>>(new Set());
  // Topic-level expanded state (key format: "templateId-topicName")
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set());
  // Session-level expanded state (key format: "templateId-topicName-session")
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set());

  // Fetch interview analysis data
  useEffect(() => {
    const fetchAnalysisData = async () => {
      if (!knowledgePackId) {
        setError('Knowledge pack ID is required');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        const response = await apiService.getInterviewAnalysis(knowledgePackId);

        if (response.success && response.data) {
          // The API response structure is: { success, message, data: AnalysisData }
          // So response.data is the AnalysisData object
          setAnalysisData(response.data);
        } else {
          throw new Error(response.error || response.message || 'Failed to load interview analysis');
        }
      } catch (err: any) {
        console.error('Failed to fetch interview analysis:', err);
        setError(err?.message || 'Failed to load interview analysis');
        // Fallback to mock data for development/testing
        // setAnalysisData(mockAnalysisData);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalysisData();
  }, [knowledgePackId]);

  // Calculate summary statistics (only when data is available)
  const totalTemplates = analysisData?.templates.length ?? 0;
  
  // Count unique topics across all templates (same topic name in different templates counts as 1)
  const uniqueTopics = analysisData?.templates.reduce((uniqueSet, template) => {
    Object.keys(template.topics).forEach((topicName) => {
      uniqueSet.add(topicName);
    });
    return uniqueSet;
  }, new Set<string>()) ?? new Set<string>();
  const totalTopics = uniqueTopics.size;
  
  const totalSessionsWithInsights = analysisData?.templates.reduce((sum, template) => {
    return (
      sum +
      Object.values(template.topics).reduce((topicSum, topic) => {
        return topicSum + topic.sessions.filter((session) => session.insights_count > 0).length;
      }, 0)
    );
  }, 0) ?? 0;

  // Check if there are any templates with insights
  const hasAnyInsights = analysisData?.templates.some((template) =>
    Object.values(template.topics).some((topic) => topicHasInsights(topic))
  ) ?? false;

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 rounded-full border-b-2 border-blue-600 animate-spin"></div>
          <p className="text-gray-600">Loading capture summary...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center">
          <ClipboardX className="mx-auto mb-4 w-12 h-12 text-red-300" />
          <p className="text-red-600 font-medium">Error loading capture summary</p>
          <p className="text-sm text-red-500 mt-2">{error}</p>
        </div>
      </div>
    );
  }

  // Show empty state if no data
  if (!analysisData) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center">
          <ClipboardX className="mx-auto mb-4 w-12 h-12 text-gray-300" />
          <p className="text-gray-600">No analysis data available</p>
        </div>
      </div>
    );
  }

  const toggleTemplate = (templateId: number) => {
    setExpandedTemplates((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(templateId)) {
        newSet.delete(templateId);
      } else {
        newSet.add(templateId);
      }
      return newSet;
    });
  };

  const toggleTopic = (templateId: number, topicName: string) => {
    const key = `${templateId}-${topicName}`;
    setExpandedTopics((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  const toggleSession = (templateId: number, topicName: string, session: string) => {
    const key = `${templateId}-${topicName}-${session}`;
    setExpandedSessions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  if (totalTemplates === 0) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center">
          <ClipboardX className="mx-auto mb-4 w-12 h-12 text-gray-300" />
          <p className="text-gray-600">No capture templates found</p>
          <p className="text-sm text-gray-500 mt-2">Create capture templates to see insights here</p>
        </div>
      </div>
    );
  }

  if (!hasAnyInsights) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center">
          <ClipboardX className="mx-auto mb-4 w-12 h-12 text-gray-300" />
          <p className="text-gray-600">No insights captured yet</p>
          <p className="text-sm text-gray-500 mt-2">
            Complete capture knowledge sessions to see insights here
          </p>
        </div>
      </div>
    );
  }

  // At this point, analysisData is guaranteed to be non-null
  if (!analysisData) {
    return null;
  }

  return (
    <div className="flex flex-col w-[1200px] h-full overflow-hidden">
      {/* Header */}
      <div className="py-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Capture Summary</h3>
          <p className="text-sm text-gray-600 mt-1">
            Review all captured insights from capture templates
          </p>
        </div>
        {/* Summary Stats */}
        <div className="flex gap-4 mt-4">
          <div className="px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600">Templates</div>
            <div className="text-2xl font-semibold text-gray-900">{totalTemplates}</div>
          </div>
          <div className="px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600">Topics</div>
            <div className="text-2xl font-semibold text-gray-900">{totalTopics}</div>
          </div>
          <div className="px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600">Sessions with Insights</div>
            <div className="text-2xl font-semibold text-gray-900">{totalSessionsWithInsights}</div>
          </div>
        </div>
      </div>

      {/* Templates List */}
      <div className="flex-1 overflow-y-auto">
        <div className="space-y-4">
          {analysisData.templates.map((template) => {
            const isTemplateExpanded = expandedTemplates.has(template.template_id);
            const topicsWithInsights = Object.entries(template.topics).filter(([, topic]) =>
              topicHasInsights(topic)
            );

            return (
              <Collapsible
                key={template.template_id}
                open={isTemplateExpanded}
                onOpenChange={() => toggleTemplate(template.template_id)}
              >
                <div className="border border-gray-200 rounded-t-lg bg-white">
                  <CollapsibleTrigger className="w-full">
                    <div className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors rounded-t-lg">
                      <div className="flex items-center gap-3 flex-1">
                        {isTemplateExpanded ? (
                          <NavArrowDown className="w-5 h-5 text-gray-600" />
                        ) : (
                          <NavArrowRight className="w-5 h-5 text-gray-600" />
                        )}
                        <div className="text-left flex-1">
                          <div className="flex items-center justify-between gap-2">
                            <div className="font-semibold text-gray-900">{template.template_name}</div>
                            <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-300 text-xs flex-shrink-0">
                              Template
                            </Badge>
                          </div>
                          <div className="text-sm text-gray-500 mt-1">
                            {topicsWithInsights.length} topic{topicsWithInsights.length !== 1 ? 's' : ''}{' '}
                            with insights • {template.total_topics} total topics
                          </div>
                        </div>
                      </div>
                    </div>
                  </CollapsibleTrigger>

                  <CollapsibleContent>
                    <div className="px-4 pb-4 space-y-4">
                      {topicsWithInsights.length === 0 ? (
                        <div className="text-sm text-gray-500 py-4 text-center">
                          No topics with insights in this template
                        </div>
                      ) : (
                        topicsWithInsights.map(([topicName, topic]) => {
                          const topicKey = `${template.template_id}-${topicName}`;
                          const isTopicExpanded = expandedTopics.has(topicKey);
                          const topicInsightsCount = getTopicInsightsCount(topic);

                          return (
                            <Collapsible
                              key={topicKey}
                              open={isTopicExpanded}
                              onOpenChange={() => toggleTopic(template.template_id, topicName)}
                            >
                              <div className="border border-gray-200 rounded-t-lg bg-gray-50">
                                <CollapsibleTrigger className="w-full">
                                  <div className="flex items-center justify-between p-3 hover:bg-gray-100 transition-colors rounded-t-lg">
                                    <div className="flex items-center gap-2 flex-1">
                                      {isTopicExpanded ? (
                                        <NavArrowDown className="w-4 h-4 text-gray-600" />
                                      ) : (
                                        <NavArrowRight className="w-4 h-4 text-gray-600" />
                                      )}
                                      <div className="text-left flex-1">
                                        <div className="flex items-center justify-between gap-2">
                                          <div className="font-medium text-gray-900">{topicName}</div>
                                          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-300 text-xs flex-shrink-0">
                                            Topic
                                          </Badge>
                                        </div>
                                        <div className="text-xs text-gray-500 mt-1">
                                          {topicInsightsCount} insight
                                          {topicInsightsCount !== 1 ? 's' : ''} across{' '}
                                          {topic.sessions.filter((s) => s.insights_count > 0).length}{' '}
                                          session
                                          {topic.sessions.filter((s) => s.insights_count > 0).length !== 1
                                            ? 's'
                                            : ''}
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                </CollapsibleTrigger>

                                <CollapsibleContent>
                                  <div className="px-3 pb-3 space-y-3">
                                    {/* Unified Report */}
                                    {topic.unified_report && (
                                      <div className="bg-white rounded border border-gray-200 p-4">
                                        <div className="text-sm font-semibold text-gray-900 mb-3">
                                          Unified Report
                                        </div>
                                        <div className="prose prose-sm max-w-none">
                                          <MarkdownViewerSmall
                                            classname="text-sm"
                                            theme="light"
                                            backgroundContext="default"
                                          >
                                            {topic.unified_report}
                                          </MarkdownViewerSmall>
                                        </div>
                                      </div>
                                    )}

                                    {/* Sessions List */}
                                    <div className="space-y-2">
                                      <div className="text-sm font-semibold text-gray-900">
                                        Sessions
                                      </div>
                                      {topic.sessions
                                        .filter((session) => session.insights_count > 0)
                                        .map((session) => {
                                          const sessionKey = `${template.template_id}-${topicName}-${session.session}`;
                                          const isSessionExpanded = expandedSessions.has(sessionKey);

                                          return (
                                            <Collapsible
                                              key={sessionKey}
                                              open={isSessionExpanded}
                                              onOpenChange={() =>
                                                toggleSession(template.template_id, topicName, session.session)
                                              }
                                            >
                                              <div className="border border-gray-200 rounded bg-white">
                                                <CollapsibleTrigger className="w-full">
                                                  <div className="flex items-center justify-between p-3 hover:bg-gray-50 transition-colors">
                                                    <div className="flex items-center gap-2 flex-1">
                                                      {isSessionExpanded ? (
                                                        <NavArrowDown className="w-4 h-4 text-gray-600" />
                                                      ) : (
                                                        <NavArrowRight className="w-4 h-4 text-gray-600" />
                                                      )}
                                                      <div className="text-left flex-1">
                                                        <div className="flex items-center gap-2">
                                                          <span className="font-medium text-gray-900">
                                                            {session.session.replace('session_', 'Session ')}
                                                          </span>
                                                          {getStatusBadge(session.status)}
                                                          {session.insights_count > 0 && (
                                                            <Badge
                                                              variant="secondary"
                                                              className="bg-blue-100 text-blue-700 border-blue-200"
                                                            >
                                                              {session.insights_count} insight
                                                              {session.insights_count !== 1 ? 's' : ''}
                                                            </Badge>
                                                          )}
                                                        </div>
                                                      </div>
                                                    </div>
                                                  </div>
                                                </CollapsibleTrigger>

                                                <CollapsibleContent>
                                                  <div className="px-3 pb-3">
                                                    <div className="bg-gray-50 rounded border border-gray-200 p-4">
                                                      <div className="text-sm font-semibold text-gray-900 mb-2">
                                                        Expert Insights
                                                      </div>
                                                      <div className="prose prose-sm max-w-none">
                                                        <MarkdownViewerSmall
                                                          classname="text-sm"
                                                          theme="light"
                                                          backgroundContext="default"
                                                        >
                                                          {session.expert_insight}
                                                        </MarkdownViewerSmall>
                                                      </div>
                                                    </div>
                                                  </div>
                                                </CollapsibleContent>
                                              </div>
                                            </Collapsible>
                                          );
                                        })}
                                    </div>
                                  </div>
                                </CollapsibleContent>
                              </div>
                            </Collapsible>
                          );
                        })
                      )}
                    </div>
                  </CollapsibleContent>
                </div>
              </Collapsible>
            );
          })}
        </div>
      </div>
    </div>
  );
}

