import React, { useState, useEffect } from 'react';
import { useAgentStore } from '@/stores/agent-store';
import { getAgentAvatarSync } from '@/utils/avatar';
import { Pencil, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Trash } from 'iconoir-react';
import { DeleteAgentDialog } from '@/components/delete-agent-dialog';
import type { NavigateFunction } from 'react-router-dom';

const OverviewTab: React.FC<{
  navigate: NavigateFunction;
}> = ({ navigate }) => {
  const agent = useAgentStore((s) => s.selectedAgent);
  const { updateAgent, deleteAgent, isDeleting } = useAgentStore();
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState(agent?.name || '');
  const [isUpdating, setIsUpdating] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const handleEditName = () => {
    setIsEditingName(true);
    setEditedName(agent?.name || '');
  };

  const handleSaveName = async () => {
    if (!agent || !editedName.trim()) return;

    setIsUpdating(true);
    try {
      await updateAgent(agent.id, {
        ...agent,
        name: editedName.trim(),
      });
      setIsEditingName(false);
    } catch (error) {
      console.error('Failed to update agent name:', error);
      // Reset to original name on error
      setEditedName(agent.name);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditingName(false);
    setEditedName(agent?.name || '');
  };

  const handleDeleteAgent = async () => {
    if (!agent) return;

    try {
      await deleteAgent(agent.id);
      setDeleteDialogOpen(false);
    } catch (error) {
      console.error('Failed to delete agent:', error);
      // You might want to show a toast notification here
    }
  };

  const handleDeleteSuccess = () => {
    // Redirect to agents page with my tab selected after successful deletion
    navigate('/agents?tab=my');
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
  };

  // Update editedName when agent changes
  useEffect(() => {
    setEditedName(agent?.name || '');
  }, [agent?.name]);

  return (
    <div className="flex flex-col gap-8 h-full md:flex-row">
      <div className="flex flex-col flex-1 gap-4 p-6 h-full bg-white rounded-lg">
        <div className="flex flex-col gap-3">
          <div className="flex overflow-hidden justify-center items-center w-16 h-16 rounded-full">
            <img
              src={getAgentAvatarSync(agent?.id || 0)}
              alt={`${agent?.name || 'Agent'} avatar`}
              className="object-cover w-full h-full"
              onError={(e) => {
                // Fallback to colored circle if image fails to load
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                const parent = target.parentElement;
                if (parent) {
                  parent.className = `flex justify-center items-center w-12 h-12 text-lg font-bold text-white bg-gradient-to-br from-pink-400 to-purple-400 rounded-full`;
                  parent.innerHTML = `<span className="text-white">${agent?.name?.[0] || 'A'}</span>`;
                }
              }}
            />
          </div>
        </div>
        <div className="flex flex-col gap-2 p-4 text-sm rounded-lg border border-gray-200 group">
          <div className="text-sm font-semibold text-gray-600">Agent Profile</div>
          <div className="flex items-center text-sm text-gray-700">
            <div className="text-gray-600 w-30">Agent name:</div>
            {isEditingName ? (
              <div className="flex gap-2 items-center">
                <Input
                  value={editedName}
                  onChange={(e) => setEditedName(e.target.value)}
                  className="w-48 text-lg font-semibold text-gray-900"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSaveName();
                    } else if (e.key === 'Escape') {
                      handleCancelEdit();
                    }
                  }}
                  autoFocus
                  size="sm"
                />
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleSaveName}
                  disabled={isUpdating}
                  className="p-1 w-8 h-8"
                >
                  <Check className="w-4 h-4 text-green-600" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleCancelEdit}
                  disabled={isUpdating}
                  className="p-1 w-8 h-8"
                >
                  <X className="w-4 h-4 text-red-600" />
                </Button>
              </div>
            ) : (
              <div className="flex gap-2 items-center">
                <div className="text-lg font-semibold text-gray-900">{agent?.name ?? '-'}</div>
                <Button size="sm" variant="ghost" onClick={handleEditName} className="p-1 w-6 h-6">
                  <Pencil className="w-3 h-3 text-gray-500" />
                </Button>
              </div>
            )}
          </div>
          <div className="flex items-center text-sm text-gray-700">
            <div className="text-gray-600 w-30">Domain:</div>
            <div className="font-medium text-gray-900">{agent?.config?.domain ?? '-'}</div>
          </div>
          <div className="flex items-center text-sm text-gray-700">
            <div className="text-gray-600 w-30">Topic:</div>
            <div className="font-medium text-gray-900">{agent?.config?.topic || '-'}</div>
          </div>
          <div className="flex items-center text-sm text-gray-700">
            <div className="text-gray-600 w-30">Tasks:</div>
            <div className="font-medium text-gray-900">
              {agent?.config?.task || agent?.config?.tasks || '-'}
            </div>
          </div>
        </div>
        <div className="flex">
          <Button variant="outline" className="w-fit" onClick={handleDeleteClick}>
            <Trash className="size-4" strokeWidth={2} />
            Delete Agent
          </Button>
        </div>
      </div>

      {/* Delete Agent Dialog */}
      <DeleteAgentDialog
        isOpen={deleteDialogOpen}
        onClose={handleCancelDelete}
        onConfirm={handleDeleteAgent}
        onSuccess={handleDeleteSuccess}
        isDeleting={isDeleting}
        agentName={agent?.name}
      />
    </div>
  );
};

export default OverviewTab;
