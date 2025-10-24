import { useEffect, useState, useCallback } from 'react';
import { Check, Circle, NavArrowDown, NavArrowRight } from 'iconoir-react';
import { IconLoader2 } from '@tabler/icons-react';
import { apiService } from '@/lib/api';

export interface QuestionProgress {
  question_text: string;
  status: string; // "not_asked", "being_asked", "answered", "skipped"
  asked_at: string | null;
}

export interface TopicProgress {
  topic_name: string;
  status: string; // "not_started", "in_progress", "completed"
  completeness: number;
  insights_count: number;
  questions: QuestionProgress[];
}

export interface ProgressData {
  topics: TopicProgress[];
  overall_completeness: number;
  current_topic: string | null;
}

interface ProgressTrackerProps {
  sessionId: number;
}

export function ProgressTracker({ sessionId }: ProgressTrackerProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set());

  const fetchProgress = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await apiService.getSessionProgress(sessionId);
      
      if (response.success && response.data) {
        setProgress(response.data);
        
        // Auto-expand current topic
        if (response.data.current_topic) {
          setExpandedTopics((prev) => {
            const newSet = new Set(prev);
            newSet.add(response.data.current_topic);
            return newSet;
          });
        }
      } else {
        setError(response.error || 'Failed to load progress');
      }
    } catch (err: any) {
      console.error('Failed to fetch progress:', err);
      setError(err?.message || 'Failed to load progress');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchProgress();
  }, [fetchProgress]);

  // Expose refresh function globally for chat sidebar to call
  useEffect(() => {
    (window as any).refreshSessionProgress = fetchProgress;
    return () => {
      delete (window as any).refreshSessionProgress;
    };
  }, [fetchProgress]);

  const getStatusIcon = (status: string, isCurrentTopic: boolean) => {
    if (status === 'completed') {
      return <Check className="w-5 h-5 text-green-600 flex-shrink-0" strokeWidth={2.5} />;
    }
    if (status === 'in_progress') {
      return (
        <div className="relative flex-shrink-0">
          <Circle className="w-5 h-5 text-blue-600" strokeWidth={2.5} />
          {isCurrentTopic && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
            </div>
          )}
        </div>
      );
    }
    return <Circle className="w-5 h-5 text-gray-300" strokeWidth={2} />;
  };

  const getStatusColor = (status: string, isCurrentTopic: boolean) => {
    if (status === 'completed') return 'text-gray-700 dark:text-gray-300';
    if (status === 'in_progress') {
      return isCurrentTopic
        ? 'text-blue-700 dark:text-blue-300 font-semibold'
        : 'text-blue-600 dark:text-blue-400 font-medium';
    }
    return 'text-gray-500 dark:text-gray-500';
  };

  const getBackgroundColor = (status: string, isCurrentTopic: boolean) => {
    if (isCurrentTopic && status === 'in_progress') {
      return 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500';
    }
    return '';
  };

  const toggleTopic = (topicName: string) => {
    setExpandedTopics((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(topicName)) {
        newSet.delete(topicName);
      } else {
        newSet.add(topicName);
      }
      return newSet;
    });
  };

  const getQuestionStatusIcon = (status: string, isBeingAsked: boolean) => {
    if (status === 'answered') {
      return <Check className="w-4 h-4 text-green-600 flex-shrink-0" strokeWidth={2.5} />;
    }
    if (status === 'being_asked') {
      return (
        <div className="relative flex-shrink-0">
          <NavArrowRight className="w-4 h-4 text-blue-600" strokeWidth={2.5} />
          {isBeingAsked && (
            <div className="absolute -right-1 -top-1 w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
          )}
        </div>
      );
    }
    if (status === 'skipped') {
      return <Circle className="w-4 h-4 text-gray-400 line-through" strokeWidth={2} />;
    }
    return <Circle className="w-4 h-4 text-gray-300" strokeWidth={2} />;
  };

  const getQuestionStatusColor = (status: string) => {
    if (status === 'answered') return 'text-gray-700 dark:text-gray-300';
    if (status === 'being_asked') return 'text-blue-700 dark:text-blue-300 font-medium';
    if (status === 'skipped') return 'text-gray-400 dark:text-gray-600 line-through';
    return 'text-gray-500 dark:text-gray-500';
  };

  const getAnsweredCount = (questions: QuestionProgress[]) => {
    return questions.filter((q) => q.status === 'answered').length;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <IconLoader2 className="w-6 h-6 text-green-600 animate-spin" />
        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
          Loading progress...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">{error}</p>
      </div>
    );
  }

  if (!progress || progress.topics.length === 0) {
    return (
      <div className="text-center py-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          No topics found yet. Start the interview to see progress.
        </p>
      </div>
    );
  }

  const completedCount = progress.topics.filter((t) => t.status === 'completed').length;
  const totalCount = progress.topics.length;

  return (
    <div className="space-y-4">
      {/* Overall Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-300">
            Overall Progress
          </span>
          <span className="text-gray-600 dark:text-gray-400">
            {completedCount}/{totalCount} Topics ({progress.overall_completeness}%)
          </span>
        </div>
        <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-600 transition-all duration-500 ease-out"
            style={{ width: `${progress.overall_completeness}%` }}
          ></div>
        </div>
      </div>

      {/* Topics List */}
      <div className="space-y-1">
        {progress.topics.map((topic, index) => {
          const isCurrentTopic = topic.topic_name === progress.current_topic;
          const isExpanded = expandedTopics.has(topic.topic_name);
          const answeredCount = getAnsweredCount(topic.questions);
          const totalQuestions = topic.questions.length;
          
          return (
            <div
              key={index}
              className={`transition-all duration-300 ${getBackgroundColor(
                topic.status,
                isCurrentTopic
              )}`}
            >
              {/* Topic Header */}
              <div className="flex items-start gap-3 p-3">
                {getStatusIcon(topic.status, isCurrentTopic)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h4
                      className={`text-md text-gray-700 font-semibold ${getStatusColor(
                        topic.status,
                        isCurrentTopic
                      )} truncate`}
                    >
                      {topic.topic_name}
                      {isCurrentTopic && (
                        <span className="ml-2 text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-full">
                          Current
                        </span>
                      )}
                    </h4>
                    <span className="text-xs text-gray-600 dark:text-gray-400 flex-shrink-0">
                      {topic.completeness}%
                    </span>
                  </div>
                  
                  {/* Question Summary and Toggle */}
                  {totalQuestions > 0 && (
                    <button
                      onClick={() => toggleTopic(topic.topic_name)}
                      className="flex items-center gap-1 mt-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                    >
                      {isExpanded ? (
                        <NavArrowDown className="w-3 h-3" />
                      ) : (
                        <NavArrowRight className="w-3 h-3" />
                      )}
                      <span>
                        Questions ({answeredCount}/{totalQuestions} answered)
                      </span>
                    </button>
                  )}
                  
                  {topic.insights_count > 0 && !isExpanded && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {topic.insights_count} insight{topic.insights_count > 1 ? 's' : ''} captured
                    </p>
                  )}
                </div>
              </div>

              {/* Collapsible Questions List */}
              {isExpanded && totalQuestions > 0 && (
                <div className="px-3 pb-3 pl-11 space-y-2 animate-in slide-in-from-top-2 duration-200">
                  {topic.questions.map((question, qIndex) => {
                    const isBeingAsked = question.status === 'being_asked';
                    
                    return (
                      <div
                        key={qIndex}
                        className={`flex items-start gap-2 text-xs ${
                          isBeingAsked ? 'bg-blue-50 dark:bg-blue-900/10 -mx-2 px-2 py-1 rounded' : ''
                        }`}
                      >
                        {getQuestionStatusIcon(question.status, isBeingAsked)}
                        <span className={getQuestionStatusColor(question.status)}>
                          {question.question_text}
                          {isBeingAsked && (
                            <span className="ml-2 text-xs px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded">
                              ASKING
                            </span>
                          )}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

