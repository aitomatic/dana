import React, { useEffect } from 'react';
import { X, FileText, Calendar, AlertCircle } from 'lucide-react';
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
  structured_data?: any;
}

interface MessageContent {
  message: string;
  showGenerateButton: boolean;
  topicPath: string;
  nodeLabel: string;
  status: string;
}

interface KnowledgeSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  topicPath: string;
  content: KnowledgeContent | MessageContent | null;
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
    if (
      !content ||
      'message' in content ||
      !('questions_by_topics' in content) ||
      !('answers_by_topics' in content)
    )
      return null;

    const knowledgeContent = content as KnowledgeContent;
    if (!knowledgeContent.questions_by_topics || !knowledgeContent.answers_by_topics) return null;

    const topics = Object.keys(knowledgeContent.questions_by_topics);

    return topics.map((topic) => {
      const questions = knowledgeContent.questions_by_topics[topic] || [];
      const answer = knowledgeContent.answers_by_topics[topic] || '';

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
              <ul className="mb-4 ml-8 space-y-2">
                {questions.map((question: string, qIndex: number) => (
                  <li key={qIndex} className="text-sm list-disc text-gray-700 rounded-md">
                    {/* <Info size={12} className="inline mr-2 text-blue-500" /> */}
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
              <div className="py-2 pl-4 bg-white">
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
    if (
      !content ||
      'message' in content ||
      !('user_instructions' in content) ||
      !content.user_instructions ||
      content.user_instructions.length === 0
    )
      return null;

    const knowledgeContent = content as KnowledgeContent;

    return (
      <div className="mb-6">
        <h4 className="flex gap-2 items-center mb-3 text-sm font-semibold text-gray-700">
          <AlertCircle size={16} />
          User Instructions
        </h4>
        <div className="space-y-2">
          {knowledgeContent.user_instructions?.map((instruction: string, index: number) => (
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
    if (!content || 'message' in content || !('final_confidence' in content)) return null;

    const knowledgeContent = content as KnowledgeContent;

    return (
      <div className="p-4 mb-6 bg-gray-50 rounded-lg">
        <h4 className="flex gap-2 items-center mb-3 text-sm font-semibold text-gray-700">
          <Calendar size={16} />
          Generation Details
        </h4>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <span className="text-gray-500">Confidence:</span>
            <div className="font-medium text-gray-700">{knowledgeContent.final_confidence}%</div>
          </div>
          <div>
            <span className="text-gray-500">Questions:</span>
            <div className="font-medium text-gray-700">{knowledgeContent.total_questions}</div>
          </div>
          <div>
            <span className="text-gray-500">Iterations:</span>
            <div className="font-medium text-gray-700">{knowledgeContent.iterations_used}</div>
          </div>
        </div>
      </div>
    );
  };

  const renderStructuredData = () => {
    return (
      <div className="mb-6">
        <div className="p-4 bg-gray-50 rounded-lg border">
          <pre className="overflow-x-auto text-xs text-gray-700 whitespace-pre-wrap">
            {JSON.stringify(content, null, 2)}
          </pre>
        </div>
      </div>
    );
  };

  const renderMessageContent = () => {
    if (!content || !('message' in content)) return null;

    const messageContent = content as MessageContent;

    const handleGenerateKnowledge = () => {
      // Auto-send message to Dana Agent Maker
      const message = `Generate knowledge for "${messageContent.nodeLabel}" (${messageContent.topicPath})`;

      // Use the global sendMessage function if available
      if (typeof window !== 'undefined' && (window as any).sendMessage) {
        (window as any).setInput(message);
        (window as any).sendMessage();
      }

      // Close the sidebar
      onClose();
    };

    return (
      <div className="space-y-6">
        {/* Message */}
        <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
          <div className="flex gap-2 items-start">
            <AlertCircle size={20} className="text-amber-600 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-amber-800">{messageContent.message}</p>
            </div>
          </div>
        </div>

        {/* Generate Knowledge Button */}
        {messageContent.showGenerateButton && (
          <div className="flex justify-center">
            <button
              onClick={handleGenerateKnowledge}
              className="px-6 py-3 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Generate Knowledge
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex fixed inset-0 z-50">
      {/* Background overlay */}
      <div className="flex-1" onClick={onClose} />
      {/* Sidebar */}
      <div className="flex flex-col max-h-full bg-white border-l border-gray-200 shadow-xl w-200">
        {/* Header */}
        <div className="flex justify-between items-center px-4 py-2 bg-gray-50 border-b border-gray-200">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {formatTopicName(topicPath)}
            </h3>
            {/* <p className="text-sm text-gray-600 truncate">{topicPath}</p> */}
          </div>
          <button
            onClick={onClose}
            className="p-2 ml-3 rounded-full transition-colors hover:bg-gray-200"
          >
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto flex-1 p-4 custom-scrollbar">
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
              {/* Message Content (for nodes without knowledge) */}
              {'message' in content && renderMessageContent()}

              {/* Knowledge Content (for nodes with generated knowledge) */}
              {!('message' in content) && (
                <>
                  {/* Content V2 - Structured Data */}
                  {content.structured_data && renderStructuredData()}

                  {/* Content V1 - Legacy Format */}
                  {!content.structured_data && (
                    <>
                      {/* Description */}
                      {/* {content.knowledge_area_description && (
                        <div>
                          <h4 className="mb-2 text-sm font-semibold text-gray-700">Description</h4>
                          <p className="text-sm leading-relaxed text-gray-600">
                            {content.knowledge_area_description}
                          </p>
                        </div>
                      )} */}

                      {/* User Instructions */}
                      {renderUserInstructions()}

                      {/* Q&A Pairs by Topic */}
                      {renderQAndAPairs()}

                      {/* Metadata */}
                      {renderMetadata()}
                    </>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeSidebar;
