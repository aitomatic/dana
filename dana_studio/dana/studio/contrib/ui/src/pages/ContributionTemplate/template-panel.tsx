import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { IconLoader2, IconEdit, IconCheck, IconX } from '@tabler/icons-react';
import type { InterviewTemplateRead } from '@/types/library';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';
import 'github-markdown-css/github-markdown.css';
import { useState } from 'react';
import { apiService } from '@/lib/api';
import { toast } from 'sonner';
import { useContributionStore } from '@/stores/contribution-store';
import { AnimatedMarkdown } from '@/components/animated-diff';
import { parseDiffResponse } from '@/lib/diff-utils';

interface TemplatePanelProps {
  template: InterviewTemplateRead;
  showContent?: boolean;
  showMetadata?: boolean;
}

export function TemplatePanel({
  template,
  showContent = true,
  showMetadata = true,
}: TemplatePanelProps) {
  const [isEditingTemplate, setIsEditingTemplate] = useState(false);
  const [editedReadmeContent, setEditedReadmeContent] = useState('');
  const [isSavingReadme, setIsSavingReadme] = useState(false);
  const [enableAnimation, setEnableAnimation] = useState(true);
  const { markTemplateAsCompleted, isSaving, setAnimatingTemplate, templateDiff, setTemplateDiff, refreshTemplate } = useContributionStore();

  // Parse diff if needed
  const parsedDiff = templateDiff ? parseDiffResponse(templateDiff) : null;
  
  // Debug logging
  console.log('📊 TemplatePanel - templateDiff changed:', {
    hasTemplateDiff: !!templateDiff,
    parsedDiff,
  });

  const handleEditTemplate = () => {
    setEditedReadmeContent(template.readme_content || '');
    setIsEditingTemplate(true);
  };

  const handleCancelEdit = () => {
    setIsEditingTemplate(false);
    setEditedReadmeContent('');
  };

  const handleSaveReadme = async () => {
    if (!template) return;

    setIsSavingReadme(true);
    try {
      const result = await apiService.updateTemplateContent(template.id, editedReadmeContent);

      if (result.success) {
        toast.success('Template updated successfully');
        setIsEditingTemplate(false);
        // Update the template content in memory
        template.readme_content = editedReadmeContent;
      } else {
        toast.error(result.error || 'Failed to update template');
      }
    } catch (error: any) {
      toast.error(error?.message || 'Failed to update template');
    } finally {
      setIsSavingReadme(false);
    }
  };

  const handleMarkAsCompleted = async () => {
    try {
      await markTemplateAsCompleted();
      toast.success('Template marked as completed successfully!');
    } catch (error: any) {
      toast.error(error?.message || 'Failed to mark template as completed');
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

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-600 text-white">Completed</Badge>;
      case 'generating':
        return <Badge className="bg-purple-600 text-white">Generating</Badge>;
      case 'pending':
        return <Badge className="bg-blue-600 text-white">Pending</Badge>;
      case 'failed':
        return <Badge className="bg-red-600 text-white">Failed</Badge>;
      case 'draft':
      default:
        return <Badge className="bg-gray-600 text-white">Draft</Badge>;
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {/* Template Content (Markdown) */}
        {showContent && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Knowledge Capture Template
                </h3>
                <div className="flex items-center gap-2">
                  {getStatusBadge(template.template_metadata?.status)}
                </div>
              </div>
              {!template.is_master && template.readme_content && (
                <button
                  onClick={isEditingTemplate ? handleCancelEdit : handleEditTemplate}
                  className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors"
                >
                  {isEditingTemplate ? (
                    <>
                      <IconX className="w-4 h-4" />
                      Cancel
                    </>
                  ) : (
                    <>
                      <IconEdit className="w-4 h-4" />
                      Edit
                    </>
                  )}
                </button>
              )}
            </div>
            {template.readme_content ? (
              isEditingTemplate ? (
                <div className="space-y-2">
                  <textarea
                    value={editedReadmeContent}
                    onChange={(e) => setEditedReadmeContent(e.target.value)}
                    className="w-full h-96 p-4 text-sm font-mono bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
                    placeholder="Enter markdown content..."
                  />
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={handleCancelEdit}
                      className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveReadme}
                      disabled={isSavingReadme}
                      className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                    >
                      {isSavingReadme ? (
                        <>
                          <IconLoader2 className="w-4 h-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <IconCheck className="w-4 h-4" />
                          Save Changes
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="relative">
                  {enableAnimation ? (
                    <AnimatedMarkdown
                      content={template.readme_content}
                      diff={parsedDiff}
                      className={cn(
                        'markdown-body',
                        'max-w-none',
                        'prose prose-sm dark:prose-invert',
                        'bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700',
                        '[&_pre]:!bg-gray-100 [&_pre]:dark:!bg-gray-800',
                        '[&_code]:!bg-gray-100 [&_code]:dark:!bg-gray-800',
                        '[&_code]:!text-gray-900 [&_code]:dark:!text-gray-100',
                      )}
                      animate={true}
                      animationSpeed={10}
                      onAnimationComplete={() => {
                        console.log('Animation complete - clearing diff and refreshing template');
                        setAnimatingTemplate(false);
                        setTemplateDiff(null);
                        // Refresh template to get the actual updated content from server
                        refreshTemplate();
                      }}
                    />
                  ) : (
                    <div
                      className={cn(
                        'markdown-body',
                        'max-w-none',
                        'prose prose-sm dark:prose-invert',
                        'bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700',
                        '[&_pre]:!bg-gray-100 [&_pre]:dark:!bg-gray-800',
                        '[&_code]:!bg-gray-100 [&_code]:dark:!bg-gray-800',
                        '[&_code]:!text-gray-900 [&_code]:dark:!text-gray-100',
                      )}
                    >
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{template.readme_content}</ReactMarkdown>
                    </div>
                  )}
                  
                  {/* Animation toggle button */}
                  <button
                    onClick={() => setEnableAnimation(!enableAnimation)}
                    className="absolute hidden top-2 right-2 z-10 text-xs px-2 py-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                    title={enableAnimation ? 'Disable animations' : 'Enable animations'}
                  >
                    {enableAnimation ? '⚡ Animation: On' : '⚡ Animation: Off'}
                  </button>
                </div>
              )
            ) : (
              <div className="flex flex-col justify-center items-center py-8">
                <div className="text-5xl mb-4">📄</div>
                <p className="text-gray-600 dark:text-gray-400 text-center">
                  No template instructions available yet.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Template Metadata Info */}
        {showMetadata && (
          <>
            {/* Template Name */}
            {template.name && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Template Name
                </h3>
                <div className="flex items-center gap-3">
                  <p className="text-gray-900 dark:text-gray-100 text-lg font-semibold">
                    {template.name}
                  </p>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(template.template_metadata?.status)}
                  </div>
                </div>
              </div>
            )}

            {/* Status */}
            {template.template_metadata?.status && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Status</h3>
                <div className="flex items-center gap-2">
                  {getStatusBadge(template.template_metadata.status)}
                </div>
              </div>
            )}

            {/* Domain & Role */}
            {(template.template_metadata?.domain || template.template_metadata?.role) && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Template Info
                </h3>
                {template.template_metadata?.domain && (
                  <p className="text-gray-900 dark:text-gray-100">
                    <span className="font-medium">Domain:</span> {template.template_metadata.domain}
                  </p>
                )}
                {template.template_metadata?.role && (
                  <p className="text-gray-900 dark:text-gray-100">
                    <span className="font-medium">Role:</span> {template.template_metadata.role}
                  </p>
                )}
              </div>
            )}

            {/* Total Topics */}
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

            {/* Estimated Duration */}
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

            {/* Description */}
            {template.description && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Description
                </h3>
                <p className="text-gray-900 dark:text-gray-100">{template.description}</p>
              </div>
            )}

            {/* Master Template Badge */}
            {template.is_master && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Template Type
                </h3>
                <Badge className="bg-purple-600 text-white">Master Template (Read-Only)</Badge>
              </div>
            )}

            {/* Timestamps */}
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Timeline</h3>
              <div className="space-y-1 text-sm">
                <p className="text-gray-900 dark:text-gray-100">
                  <span className="font-medium">Created:</span> {formatDate(template.created_at)}
                </p>
                <p className="text-gray-900 dark:text-gray-100">
                  <span className="font-medium">Last Updated:</span>{' '}
                  {formatDate(template.updated_at)}
                </p>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Actions - Mark as Completed Button */}
      {!template.is_master && template.template_metadata?.status !== 'completed' && (
        <div className="flex-shrink-0 px-6 py-4 border-t border-gray-200 dark:border-gray-800 space-y-3">
          <Button
            onClick={handleMarkAsCompleted}
            disabled={isSaving}
            variant="default"
            className="w-full text-white gap-2 disabled:opacity-50"
          >
            {isSaving ? (
              <>
                <IconLoader2 className="w-4 h-4 animate-spin" />
                Marking as Completed...
              </>
            ) : (
              <>
                <IconCheck className="w-4 h-4" />
                Mark as Completed
              </>
            )}
          </Button>
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Mark this template as completed when you're satisfied with the interview questions
          </p>
        </div>
      )}
    </div>
  );
}

