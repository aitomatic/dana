import { useParams } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { ChatPlusIn, Tools } from 'iconoir-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { IconDotsVertical, IconEdit, IconMenu2, IconTrash } from '@tabler/icons-react';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';

const ConversationItem = ({ conversation, isActive, onSelect, onRename, onDelete }: any) => {
  return (
    <div
      key={conversation.id}
      className={cn(
        'flex rounded-lg px-4 py-2 w-full cursor-pointer group relative',
        isActive ? 'bg-gray-100' : 'hover:bg-gray-50',
      )}
      onClick={onSelect}
    >
      <div className="flex flex-col flex-1 min-w-0 gap-2">
        <div
          className={cn(
            'min-w-0 truncate text-sm font-medium',
            'animate-slideIn',
            isActive ? 'text-gray-700' : 'text-gray-500',
          )}
        >
          {conversation?.meta_data?.name || 'New conversation'}
        </div>
      </div>
      <ConversationActions conversation={conversation} onRename={onRename} onDelete={onDelete} />
    </div>
  );
};

interface ConversationActionsProps {
  conversation: any;
  onRename: (conversation: any) => void;
  onDelete: (conversation: any) => void;
}

const ConversationActions = ({ conversation, onRename, onDelete }: ConversationActionsProps) => {
  return (
    <div
      className="absolute transition-opacity opacity-0 right-2 group-hover:opacity-100"
      onClick={(e) => e.stopPropagation()}
    >
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger asChild>
          <IconDotsVertical
            className="w-4 h-4 text-gray-500 rotate-90"
            data-testid={`conversation-actions-button-${conversation.id}`}
          />
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem onClick={() => onRename(conversation)}>
            <IconEdit className="w-4 h-4" />
            Rename
          </DropdownMenuItem>
          <DropdownMenuItem
            className="text-error-600 hover:text-error-600"
            onClick={() => onDelete(conversation)}
            data-testid="conversation-delete-trigger-button"
          >
            <IconTrash className="w-4 h-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

const ConversationsSidebar = ({
  setIsSidebarCollapsed,
}: {
  setIsSidebarCollapsed: (isCollapsed: boolean) => void;
}) => {
  const [isRenameOpen, setIsRenameOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState<any | null>(null);
  const [newName, setNewName] = useState('');

  const { chat_id } = useParams();

  const handleRename = async () => {
    if (selectedConversation && newName.trim()) {
      setIsRenameOpen(false);
      setNewName('');
    }
  };

  const handleDelete = async (conversation: any) => {
    setSelectedConversation(conversation);
    setIsDeleteOpen(true);
  };

  const confirmDelete = async () => {
    if (selectedConversation) {
      setIsDeleteOpen(false);
    }
  };

  const handleSelectConversation = (conversation: any) => {
    console.log(conversation);
  };

  const handleOpenRename = (conversation: any) => {
    setSelectedConversation(conversation);
    setNewName(conversation?.meta_data?.name || '');
    setIsRenameOpen(true);
  };

  return (
    <div className="flex flex-col w-full h-full border-r border-gray-200 dark:border-gray-300">
      <div className="flex flex-col gap-3">
        <div className="flex flex-row items-center justify-between w-full h-12 px-4 border-b border-gray-200 dark:border-gray-300">
          <div className="flex items-center gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center justify-center rounded-md cursor-pointer hover:bg-gray-100 size-8">
                  <IconMenu2
                    onClick={() => setIsSidebarCollapsed(true)}
                    size={20}
                    strokeWidth={2}
                    className="text-gray-600 cursor-pointer"
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom">Close</TooltipContent>
            </Tooltip>

            <span className="text-sm font-semibold text-gray-600">History</span>
          </div>

          <div className="flex flex-row items-center">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center justify-center rounded-md cursor-pointer hover:bg-gray-100 size-8">
                  <Tools
                    onClick={() => {}}
                    width={18}
                    height={18}
                    className="text-gray-600 cursor-pointer"
                    strokeWidth={1.5}
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom">Manage Agent</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center justify-center rounded-md cursor-pointer hover:bg-gray-100 size-8">
                  <ChatPlusIn onClick={() => {}} width={18} height={18} className="text-gray-600" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom">New chat</TooltipContent>
            </Tooltip>
          </div>
        </div>

        <div className="flex flex-col gap-2 h-[calc(100vh-130px)] overflow-scroll scrollbar-hide">
          <div className="flex flex-col gap-3 px-2">
            {[].length > 0 ? (
              [].map((conversation: any) => (
                <ConversationItem
                  key={conversation.id}
                  conversation={conversation}
                  isActive={conversation.conversation_id === chat_id}
                  onSelect={() => handleSelectConversation(conversation)}
                  onRename={handleOpenRename}
                  onDelete={handleDelete}
                />
              ))
            ) : (
              <span className="pl-3 text-sm text-gray-400">History is empty</span>
            )}
          </div>
        </div>
      </div>

      <Dialog open={isRenameOpen} onOpenChange={setIsRenameOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Conversation</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4 p-4">
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Enter new name"
            />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setIsRenameOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleRename}>Save</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Conversation</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4 p-4">
            <p className="text-sm text-gray-600">
              Are you sure you want to delete this conversation? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setIsDeleteOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={confirmDelete}
                data-testid="conversation-delete-button"
              >
                Delete
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ConversationsSidebar;
