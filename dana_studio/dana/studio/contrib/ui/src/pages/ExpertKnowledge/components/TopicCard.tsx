import { CheckCircleSolid, Circle, NavArrowDown, NavArrowRight } from 'iconoir-react';
import type { QuestionProgress } from './ProgressTracker';
import type { TopicNoteContent } from './parseNotesUtils';

interface TopicCardProps {
  topicName: string;
  status: string;
  completeness: number;
  insightsCount: number;
  questions: QuestionProgress[];
  noteContent: TopicNoteContent | undefined;
  isCurrentTopic: boolean;
  isExpanded: boolean;
  onToggle: () => void;
}

export function TopicCard({
  topicName,
  status,
  completeness,
  insightsCount,
  questions,
  noteContent,
  isCurrentTopic,
  isExpanded,
  onToggle
}: TopicCardProps) {

  const getStatusIcon = (status: string, isCurrentTopic: boolean) => {
    if (status === 'completed') {
      return <CheckCircleSolid className="w-5 h-5 text-green-600 flex-shrink-0" strokeWidth={2.5} />;
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
    return 'text-gray-700 dark:text-gray-700';
  };

  const getBackgroundColor = (status: string, isCurrentTopic: boolean) => {
    if (isCurrentTopic && status === 'in_progress') {
      return 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500';
    }
    return '';
  };

  const getQuestionStatusIcon = (status: string) => {
    if (status === 'answered') {
      return <CheckCircleSolid className="w-4 h-4 text-green-600 flex-shrink-0" strokeWidth={2.5} />;
    }
    if (status === 'being_asked') {
      return (
        <div className="relative flex-shrink-0">
          <NavArrowRight className="w-4 h-4 text-blue-600" strokeWidth={2.5} />
          <div className="absolute -right-1 -top-1 w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
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

  const totalQuestions = questions.length;

  return (
    <div className={` transition-all duration-300 ${getBackgroundColor(status, isCurrentTopic)}`}>
      {/* Topic Header */}
      <div className="flex items-start gap-3 p-3">
        {getStatusIcon(status, isCurrentTopic)}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h4 className={`text-sm font-semibold ${getStatusColor(status, isCurrentTopic)} truncate`}>
              {topicName}
              {isCurrentTopic && (
                <span className="ml-2 text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-full">
                  Current
                </span>
              )}
            </h4>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                {completeness}%
              </span>
              <button
                onClick={onToggle}
                className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {isExpanded ? (
                  <NavArrowDown className="w-4 h-4" />
                ) : (
                  <NavArrowRight className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
          
          {/* Summary info when collapsed */}
          {!isExpanded && (
            <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {insightsCount > 0 && (
                <span>
                  {insightsCount} insight{insightsCount > 1 ? 's' : ''}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Topic Content - Expanded */}
      {isExpanded && (
        <div className="px-3 pb-3 pl-11 space-y-3 animate-in slide-in-from-top-2 duration-200">
          {/* Background */}
          {noteContent?.background && (
            <div className="space-y-1">
              <h5 className="text-xs font-medium text-gray-600 dark:text-gray-400">Background</h5>
              <p className="text-xs text-gray-700 dark:text-gray-300">{noteContent.background}</p>
            </div>
          )}

          {/* Questions */}
          {totalQuestions > 0 && (
            <div className="space-y-1">
              <h5 className="text-xs font-bold text-gray-700 dark:text-gray-400">
                Questions:
              </h5>
              <div className="ml-4 space-y-1 text-gray-700">
                {questions.map((question, index) => (
                  <div
                    key={index}
                    className={`flex items-start gap-2 text-xs ${
                      question.status === 'being_asked' 
                        ? 'bg-blue-50 dark:bg-blue-900/10 -mx-2 px-2 py-1 rounded' 
                        : ''
                    }`}
                  >
                    {getQuestionStatusIcon(question.status)}
                    <span className={getQuestionStatusColor(question.status)}>
                      {question.question_text}
                      {question.status === 'being_asked' && (
                        <span className="ml-2 text-xs px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded">
                          ASKING
                        </span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Expert Insights */}
          {noteContent?.expertInsights && noteContent.expertInsights.length > 0 && (
            <div className="space-y-1">
              <h5 className="text-xs font-bold text-gray-700 dark:text-gray-400">Expert Insights:</h5>
              <ul className="space-y-1">
                {noteContent.expertInsights.map((insight, index) => (
                  <li key={index} className="text-xs text-gray-700 dark:text-gray-300 flex items-start gap-2">
                    <span className="text-gray-400 mt-1 flex w-1 h-1 bg-gray-600 rounded-full shrink-0"></span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
