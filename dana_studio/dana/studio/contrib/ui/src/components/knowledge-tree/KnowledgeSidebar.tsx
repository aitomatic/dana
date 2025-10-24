/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect } from 'react';
import { X, FileText, Calendar, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useUIStore } from '@/stores/ui-store';
import { Button } from '@/components/ui/button';

interface KnowledgeItemContent {
  content: string;
  references?: string[];
}

interface KnowledgeItem {
  question: string;
  facts: KnowledgeItemContent[];
  heuristics: KnowledgeItemContent[];
  procedures: KnowledgeItemContent[];
}

interface QuestionBankContent {
  path_parts: string[];
  knowledges: KnowledgeItem[];
  structured_data?: unknown;
  total_questions: number;
}

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
  structured_data?: unknown;
}

interface MessageContent {
  message: string;
  showGenerateButton: boolean;
  topicPath: string;
  nodeLabel: string;
  status: string;
  title: string;
  description: string;
}

interface KnowledgeSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  topicPath: string;
  content: KnowledgeContent | MessageContent | QuestionBankContent | null;
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

  console.log('🎨 KnowledgeSidebar render:', { 
    isOpen,
    hasContent: !!content,
    contentType: content 
      ? ('knowledges' in content ? 'QuestionBank' 
        : 'message' in content ? 'Message' 
        : 'KnowledgeContent')
      : 'null',
    hasKnowledges: content && 'knowledges' in content,
    knowledgesCount: content && 'knowledges' in content ? content.knowledges.length : 0,
  });
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

  // Helper function to parse question text and extract individual questions
  const parseQuestions = (questionText: string): string[] => {
    // Remove markdown code blocks
    const cleanText = questionText.replace(/```text\n?/g, '').replace(/```/g, '');

    // Split by *Question N* pattern
    const questions = cleanText.split(/\*Question \d+\*/g).filter((q) => q.trim());

    return questions.map((q) => q.trim().replace(/^:\s*/, ''));
  };

  const renderQuestionBank = () => {
    if (!content || !('knowledges' in content)) {
      console.log('❌ renderQuestionBank: no content or no knowledges field');
      return null;
    }

    const questionBankContent = content as QuestionBankContent;
    console.log('✅ renderQuestionBank: rendering question bank', {
      knowledgesCount: questionBankContent.knowledges.length,
      totalQuestions: questionBankContent.total_questions,
    });

    return (
      <div className="space-y-6">
        {/* Header Info */}
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex gap-2 items-center mb-2">
            <FileText size={18} className="text-blue-600" />
            <h3 className="font-semibold text-blue-900 text-md">Question Bank</h3>
          </div>
          <p className="text-sm text-blue-700">
            {questionBankContent.total_questions} questions organized into{' '}
            {questionBankContent.knowledges.length} knowledge iterations
          </p>
        </div>

        {/* Knowledge Items */}
        {questionBankContent.knowledges.map((knowledge, index) => {
          const questions = parseQuestions(knowledge.question);

          return (
            <div key={index} className="pb-6 border-b border-gray-200 last:border-b-0">
              <div className="flex gap-2 items-center mb-4">
                <div className="flex justify-center items-center px-2 py-1 text-xs font-semibold text-blue-700 bg-blue-100 rounded-full">
                  Iteration {index + 1}
                </div>
                <span className="text-sm text-gray-500">{questions.length} questions</span>
              </div>

              {/* Raw Question Text with Full Context */}
              <div className="mb-4 bg-white rounded-lg border-blue-200 shadow-sm border-1">
                <div className="px-4 py-3 bg-gradient-to-r from-blue-50 rounded-t-lg border-b border-blue-200 to-blue-100/50">
                  <h4 className="text-xs font-semibold tracking-wide text-blue-700 uppercase">
                    Questions & Context
                  </h4>
                </div>
                <div className="p-2 bg-white">
                  <div className="max-w-none leading-relaxed text-gray-900 bg-white prose prose-base">
                    <ReactMarkdown>{knowledge.question}</ReactMarkdown>
                  </div>
                </div>
              </div>

              {/* Facts, Heuristics, Procedures */}
              {(knowledge.facts.length > 0 ||
                knowledge.heuristics.length > 0 ||
                knowledge.procedures.length > 0) && (
                <div className="space-y-4">
                  {knowledge.facts.length > 0 && (
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <h5 className="flex gap-2 items-center mb-3 text-sm font-semibold text-green-800">
                        <FileText size={16} />
                        Facts
                      </h5>
                      <div className="space-y-2">
                        {knowledge.facts.map((fact, fIndex) => (
                          <div key={fIndex} className="pl-4 border-l-2 border-green-300">
                            <div className="max-w-none text-sm text-gray-700 prose prose-sm">
                              <ReactMarkdown>{fact.content}</ReactMarkdown>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {knowledge.heuristics.length > 0 && (
                    <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                      <h5 className="flex gap-2 items-center mb-3 text-sm font-semibold text-amber-800">
                        <AlertCircle size={16} />
                        Heuristics
                      </h5>
                      <div className="space-y-2">
                        {knowledge.heuristics.map((heuristic, hIndex) => (
                          <div key={hIndex} className="pl-4 border-l-2 border-amber-300">
                            <div className="max-w-none text-sm text-gray-700 prose prose-sm">
                              <ReactMarkdown>{heuristic.content}</ReactMarkdown>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {knowledge.procedures.length > 0 && (
                    <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                      <h5 className="flex gap-2 items-center mb-3 text-sm font-semibold text-purple-800">
                        <Calendar size={16} />
                        Procedures
                      </h5>
                      <div className="space-y-2">
                        {knowledge.procedures.map((procedure, pIndex) => (
                          <div key={pIndex} className="pl-4 border-l-2 border-purple-300">
                            <div className="max-w-none text-sm text-gray-700 prose prose-sm">
                              <ReactMarkdown>{procedure.content}</ReactMarkdown>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
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
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="space-y-2">
            <h3 className="font-semibold text-gray-900 text-md">{messageContent.title}</h3>
            <p className="text-sm text-gray-600">{messageContent.description}</p>
          </div>
        </div>

        {/* Generate Knowledge Button */}
        {messageContent.showGenerateButton && (
          <div className="flex">
            <Button onClick={handleGenerateKnowledge} variant="default">
              Generate Knowledge
            </Button>
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

              {/* Question Bank Content (for knowledge pack nodes) */}
              {'knowledges' in content && renderQuestionBank()}

              {/* Knowledge Content (for nodes with generated knowledge) */}
              {!('message' in content) && !('knowledges' in content) && (
                <>
                  {/* Content V2 - Structured Data */}
                  {content.structured_data && renderStructuredData()}

                  {/* Content V1 - Legacy Format */}
                  {!content.structured_data && (
                    <>
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
