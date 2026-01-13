import { Badge } from '@/components/ui/badge';
import { IconLoader2 } from '@tabler/icons-react';
import type { InterviewSessionRead, InterviewTemplateRead } from '@/types/library';
import { SESSION_STATUS } from '@/lib/constants';
import ReactMarkdown from 'react-markdown';
import { EnhancedProgressNotes } from './components/EnhancedProgressNotes';

interface SummaryPanelProps {
  session: InterviewSessionRead;
  template: InterviewTemplateRead | null;
  showSessionInfo?: boolean;
  showTemplateInfo?: boolean;
}

export function SummaryPanel({
  session,
  template,
  showSessionInfo = true,
  showTemplateInfo = true,
}: SummaryPanelProps) {

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case SESSION_STATUS.COMPLETED:
        return <Badge className="bg-green-600 text-white">Completed</Badge>;
      case SESSION_STATUS.IN_PROGRESS:
        return <Badge className="bg-blue-600 text-white">In Progress</Badge>;
      case SESSION_STATUS.DRAFT:
      default:
        return <Badge className="bg-gray-600 text-white">Draft</Badge>;
    }
  };

  const formatDate = (date?: string | null) => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {/* Session Info Tab */}
        {showSessionInfo && (
          <>


            {/* Interview Progress & Notes (Combined) */}
            <div className="space-y-2">
            
              <EnhancedProgressNotes sessionId={session.id} />
            </div>

            {/* Session Name */}
            {session.session_name && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Session Name
                </h3>
                <p className="text-gray-900 dark:text-gray-100">{session.session_name}</p>
              </div>
            )}

            {/* Interviewee Information */}
            {(session.interviewee_name || session.interviewee_role) && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Interviewee
                </h3>
                {session.interviewee_name && (
                  <p className="text-gray-900 dark:text-gray-100">
                    <span className="font-medium">Name:</span> {session.interviewee_name}
                  </p>
                )}
                {session.interviewee_role && (
                  <p className="text-gray-900 dark:text-gray-100">
                    <span className="font-medium">Role:</span> {session.interviewee_role}
                  </p>
                )}
              </div>
            )}

            {/* Timestamps */}
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Timeline</h3>
              <div className="space-y-1 text-sm">
                <p className="text-gray-900 dark:text-gray-100">
                  <span className="font-medium">Created:</span> {formatDate(session.created_at)}
                </p>
                {session.started_at && (
                  <p className="text-gray-900 dark:text-gray-100">
                    <span className="font-medium">Started:</span> {formatDate(session.started_at)}
                  </p>
                )}
                {session.completed_at && (
                  <p className="text-gray-900 dark:text-gray-100">
                    <span className="font-medium">Completed:</span>{' '}
                    {formatDate(session.completed_at)}
                  </p>
                )}
                <p className="text-gray-900 dark:text-gray-100">
                  <span className="font-medium">Last Updated:</span>{' '}
                  {formatDate(session.updated_at)}
                </p>
              </div>
                          {/* Session Status */}
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Session Status
              </h3>
              <div className="flex items-center gap-2">{getStatusBadge(session.status)}</div>
            </div>
            </div>

          </>
        )}

        {/* Capture Template Info Tab */}
        {showTemplateInfo && (
          <>
            {template ? (
              <div className="space-y-6">
                {template.name && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Template Name
                    </h3>
                    <p className="text-gray-900 dark:text-gray-100 text-lg font-semibold">
                      {template.name}
                    </p>
                  </div>
                )}

                {template.template_metadata?.domain && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Domain</h3>
                    <p className="text-gray-900 dark:text-gray-100">
                      {template.template_metadata.domain}
                    </p>
                  </div>
                )}

                {template.template_metadata?.role && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Role</h3>
                    <p className="text-gray-900 dark:text-gray-100">
                      {template.template_metadata.role}
                    </p>
                  </div>
                )}

                {template.template_metadata?.total_topics && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Total Topics
                    </h3>
                    <p className="text-gray-900 dark:text-gray-100">
                      {template.template_metadata.total_topics}
                    </p>
                  </div>
                )}

                {template.template_metadata?.estimated_duration && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Estimated Duration
                    </h3>
                    <p className="text-gray-900 dark:text-gray-100">
                      {template.template_metadata.estimated_duration} minutes
                    </p>
                  </div>
                )}

                {/* Template README/Guide */}
                {template.readme_content && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Template Guide
                    </h3>
                    <div className="prose prose-sm dark:prose-invert max-w-none bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                      <ReactMarkdown>{template.readme_content}</ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center py-8 text-center">
                <IconLoader2 className="w-6 h-6 text-green-600 animate-spin" />
                <span className="ml-2 text-gray-600 dark:text-gray-400">
                  Loading template information...
                </span>
              </div>
            )}
          </>
        )}
      </div>

      {/* Auto-save message - only show on Session Summary tab */}
      {showSessionInfo && (
        <div className="flex-shrink-0 px-6 py-4 border-t border-gray-200 dark:border-gray-800">
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Your conversation is auto-saved
          </p>
        </div>
      )}
    </div>
  );
}
