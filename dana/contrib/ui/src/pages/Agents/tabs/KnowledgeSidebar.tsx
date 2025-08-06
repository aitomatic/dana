import React, { useEffect } from 'react';
import { X, FileText, Calendar, Info, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useUIStore } from '@/stores/ui-store';

interface KnowledgeContent {
  knowledge_area_description: string;
  questions: string[];
  questions_by_topics: Record<string, string[]>;
  final_confidence: number;
  confidence_by_topics: Record<string, number>;
  iterations_used: number;
  total_questions: number;
  answers_by_topics: Record<string, string>;
  user_instructions?: string[];
}

interface KnowledgeSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  topicPath: string;
  content: KnowledgeContent | null;
  loading: boolean;
  error: string | null;
}

const KnowledgeSidebar: React.FC<KnowledgeSidebarProps> = ({
  isOpen,
  onClose,
  topicPath,
  content,
  loading,
  error,
}) => {
  const { closeChatSidebar } = useUIStore();

  // Close chat sidebar when knowledge sidebar opens
  useEffect(() => {
    if (isOpen) {
      closeChatSidebar();
    }
  }, [isOpen, closeChatSidebar]);

  console.log({ content });
  if (!isOpen) return null;

  const formatTopicName = (topicPath: string) => {
    const parts = topicPath.split(' - ');
    return parts[parts.length - 1] || topicPath;
  };

  const renderQAndAPairs = () => {
    if (!content?.questions_by_topics || !content?.answers_by_topics) return null;

    const topics = Object.keys(content.questions_by_topics);

    return topics.map((topic) => {
      const questions = content.questions_by_topics[topic] || [];
      const answer = content.answers_by_topics[topic] || '';

      // Format topic name for display
      const formattedTopic = topic.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());

      return (
        <div key={topic} className="mb-8">
          <h4 className="flex gap-2 items-center pb-2 mb-4 text-sm font-semibold text-gray-700 border-b border-gray-200">
            <FileText size={16} />
            {formattedTopic}
          </h4>

          {/* Questions for this topic */}
          {questions.length > 0 && (
            <div className="mb-4">
              <h5 className="mb-2 text-xs font-medium tracking-wide text-gray-600 uppercase">
                Research Questions
              </h5>
              <ul className="mb-4 space-y-2">
                {questions.map((question, qIndex) => (
                  <li
                    key={qIndex}
                    className="p-2 text-sm text-gray-600 bg-gray-50 rounded-md border-l-4 border-blue-200"
                  >
                    <Info size={12} className="inline mr-2 text-blue-500" />
                    {question}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Answer for this topic */}
          {answer && (
            <div className="space-y-4">
              <h5 className="mb-2 text-xs font-medium tracking-wide text-gray-600 uppercase">
                Generated Knowledge
              </h5>
              <div className="py-2 pl-4 bg-white border-l-4 border-green-200">
                <div className="max-w-none leading-relaxed text-gray-700 prose prose-sm">
                  {Array.isArray(answer) ? (
                    <ul className="pl-5 list-disc">
                      {answer.map((item, idx) => (
                        <li key={idx}>
                          <ReactMarkdown>{item}</ReactMarkdown>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <ReactMarkdown>{answer}</ReactMarkdown>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      );
    });
  };

  const renderUserInstructions = () => {
    if (!content?.user_instructions || content.user_instructions.length === 0) return null;

    return (
      <div className="mb-6">
        <h4 className="flex gap-2 items-center mb-3 text-sm font-semibold text-gray-700">
          <AlertCircle size={16} />
          User Instructions
        </h4>
        <div className="space-y-2">
          {content.user_instructions.map((instruction, index) => (
            <div
              key={index}
              className="p-3 text-sm text-blue-700 bg-blue-50 rounded-md border-l-4 border-blue-200"
            >
              <div className="max-w-none prose prose-sm">
                <ReactMarkdown>{instruction}</ReactMarkdown>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderMetadata = () => {
    if (!content) return null;

    return (
      <div className="p-4 mb-6 bg-gray-50 rounded-lg">
        <h4 className="flex gap-2 items-center mb-3 text-sm font-semibold text-gray-700">
          <Calendar size={16} />
          Generation Details
        </h4>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <span className="text-gray-500">Confidence:</span>
            <div className="font-medium text-gray-700">{content.final_confidence}%</div>
          </div>
          <div>
            <span className="text-gray-500">Questions:</span>
            <div className="font-medium text-gray-700">{content.total_questions}</div>
          </div>
          <div>
            <span className="text-gray-500">Iterations:</span>
            <div className="font-medium text-gray-700">{content.iterations_used}</div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex fixed inset-0 z-50">
      {/* Background overlay */}
      <div className="flex-1  " onClick={onClose} />

      {/* Sidebar */}
      <div className="flex flex-col w-200 max-h-full bg-white border-l border-gray-200 shadow-xl">
        {/* Header */}
        <div className="flex justify-between items-center p-4 bg-gray-50 border-b border-gray-200">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {formatTopicName(topicPath)}
            </h3>
            <p className="text-sm text-gray-600 truncate">{topicPath}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 ml-3 rounded-full transition-colors hover:bg-gray-200"
          >
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto flex-1 p-4">
          {loading && (
            <div className="flex justify-center items-center py-8">
              <div className="w-8 h-8 rounded-full border-b-2 border-blue-600 animate-spin"></div>
              <span className="ml-3 text-gray-600">Loading knowledge...</span>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {!loading && !error && !content && (
            <div className="py-8 text-center">
              <FileText size={48} className="mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">No knowledge content available</p>
            </div>
          )}

          {!loading && !error && content && (
            <div className="space-y-6">
              {/* Description */}
              {content.knowledge_area_description && (
                <div>
                  <h4 className="mb-2 text-sm font-semibold text-gray-700">Description</h4>
                  <p className="text-sm leading-relaxed text-gray-600">
                    {content.knowledge_area_description}
                  </p>
                </div>
              )}

              {/* User Instructions */}
              {renderUserInstructions()}

              {/* Q&A Pairs by Topic */}
              {renderQAndAPairs()}

              {/* Metadata */}
              {renderMetadata()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeSidebar;
