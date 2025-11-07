// import { Button } from '@/components/ui/button';
import { IconLoader2, IconEdit, IconCheck, IconX } from '@tabler/icons-react';
import type { InterviewTemplateRead } from '@/types/library';
import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useContributionStore } from '@/stores/contribution-store';

interface SystemPromptPanelProps {
  template: InterviewTemplateRead;
}

export function SystemPromptPanel({ template }: SystemPromptPanelProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedSystemPrompt, setEditedSystemPrompt] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  
  const { systemPrompt, isLoadingSystemPrompt, loadSystemPrompt, updateSystemPrompt } = useContributionStore();

  // Load system prompt when component mounts or template changes
  useEffect(() => {
    if (template?.id) {
      loadSystemPrompt(template.id);
    }
  }, [template?.id, loadSystemPrompt]);

  // Initialize edited content when system prompt loads or editing starts
  useEffect(() => {
    if (isEditing && systemPrompt !== null) {
      setEditedSystemPrompt(systemPrompt);
    }
  }, [isEditing, systemPrompt]);

  const handleEdit = () => {
    setEditedSystemPrompt(systemPrompt || '');
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedSystemPrompt('');
  };

  const handleSave = async () => {
    if (!template) return;

    setIsSaving(true);
    try {
      await updateSystemPrompt(template.id, editedSystemPrompt);
      toast.success('System prompt updated successfully');
      setIsEditing(false);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to update system prompt');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {/* System Prompt Content */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                System Prompt
              </h3>
            </div>
            {!template.is_master && (
              <button
                onClick={isEditing ? handleCancel : handleEdit}
                className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors"
              >
                {isEditing ? (
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
          
          {isLoadingSystemPrompt ? (
            <div className="flex justify-center items-center py-8">
              <IconLoader2 className="w-6 h-6 text-gray-400 animate-spin" />
            </div>
          ) : isEditing ? (
            <div className="space-y-2">
              <textarea
                value={editedSystemPrompt}
                onChange={(e) => setEditedSystemPrompt(e.target.value)}
                className="w-full h-96 p-4 text-sm font-mono bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
                placeholder="Enter system prompt content..."
              />
              <div className="flex gap-2 justify-end">
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                >
                  {isSaving ? (
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
          ) : systemPrompt ? (
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <pre className="whitespace-pre-wrap text-sm text-gray-900 dark:text-gray-100 font-mono">
                {systemPrompt}
              </pre>
            </div>
          ) : (
            <div className="flex flex-col justify-center items-center py-8">
              <div className="text-5xl mb-4">📝</div>
              <p className="text-gray-600 dark:text-gray-400 text-center">
                No system prompt configured yet.
              </p>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-500 text-center">
                {template.is_master
                  ? 'Master templates cannot be edited.'
                  : 'Click Edit to add a system prompt that will be prepended to the document exploration prompt in chat mode.'}
              </p>
            </div>
          )}
        </div>

        {/* Info Section */}
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
            About System Prompt
          </h3>
          <div className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
            <p>
              The system prompt is prepended to the document exploration prompt when using chat mode.
              This allows you to customize the AI's behavior and instructions for document exploration.
            </p>
            <p>
              The system prompt will be saved in <code className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">system_prompt.prompt</code> in the template folder.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

