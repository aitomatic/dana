import { useParams, useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useState, useEffect } from 'react';
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
import { useChatStore } from '@/stores/chat-store';
import type { ConversationRead } from '@/types/conversation';

const ConversationItem = ({ conversation, isActive, onSelect, onRename, onDelete }: {
  conversation: ConversationRead;
  isActive: boolean;
  onSelect: () => void;
  onRename: () => void;
  onDelete: () => void;
}) => {
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
          {conversation.title || 'New conversation'}
        </div>
      </div>
      <ConversationActions conversation={conversation} onRename={onRename} onDelete={onDelete} />
    </div>
  );
};

const ConversationActions = ({ conversation, onRename, onDelete }: {
  conversation: ConversationRead;
  onRename: () => void;
  onDelete: () => void;
}) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <div className="flex items-center justify-center rounded-md cursor-pointer hover:bg-gray-100 size-8 opacity-0 group-hover:opacity-100 transition-opacity">
          <IconDotsVertical size={16} className="text-gray-600" />
        </div>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={onRename}>
          <IconEdit size={16} className="mr-2" />
          Rename
        </DropdownMenuItem>
        <DropdownMenuItem onClick={onDelete} className="text-red-600">
          <IconTrash size={16} className="mr-2" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

interface ConversationsSidebarProps {
  setIsSidebarCollapsed: (collapsed: boolean) => void;
  agentId?: string;
}

const ConversationsSidebar: React.FC<ConversationsSidebarProps> = ({ setIsSidebarCollapsed, agentId }) => {
  const navigate = useNavigate();
  const { conversation_id } = useParams();
  const [isRenameOpen, setIsRenameOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState<ConversationRead | null>(null);
  const [newName, setNewName] = useState('');

  const {
    conversations,
    isLoading,
    fetchConversations,
    updateConversation,
    deleteConversation,
    createConversation,
  } = useChatStore();

  // Fetch conversations when agentId changes
  useEffect(() => {
    if (agentId) {
      fetchConversations(parseInt(agentId));
    }
  }, [agentId, fetchConversations]);

  const handleRename = async () => {
    if (selectedConversation && newName.trim()) {
      try {
        await updateConversation(selectedConversation.id, {
          title: newName.trim(),
          agent_id: selectedConversation.agent_id,
        });
        setIsRenameOpen(false);
        setNewName('');
        // Refresh conversations
        if (agentId) {
          fetchConversations(parseInt(agentId));
        }
      } catch (error) {
        console.error('Failed to rename conversation:', error);
      }
    }
  };

  const handleDelete = async (conversation: ConversationRead) => {
    setSelectedConversation(conversation);
    setIsDeleteOpen(true);
  };

  const confirmDelete = async () => {
    if (selectedConversation) {
      try {
        await deleteConversation(selectedConversation.id);
        setIsDeleteOpen(false);
        // If we're currently viewing this conversation, navigate to agent chat
        if (conversation_id && parseInt(conversation_id) === selectedConversation.id) {
          navigate(`/agents/${agentId}/chat`);
        }
        // Refresh conversations
        if (agentId) {
          fetchConversations(parseInt(agentId));
        }
      } catch (error) {
        console.error('Failed to delete conversation:', error);
      }
    }
  };

  const handleSelectConversation = (conversation: ConversationRead) => {
    navigate(`/agents/${agentId}/chat/${conversation.id}`);
  };

  const handleOpenRename = (conversation: ConversationRead) => {
    setSelectedConversation(conversation);
    setNewName(conversation.title || '');
    setIsRenameOpen(true);
  };

  const handleNewChat = () => {
    navigate(`/agents/${agentId}/chat`);
  };

  const handleCreateConversation = async () => {
    if (agentId) {
      try {
        await createConversation({
          title: "New conversation",
          agent_id: parseInt(agentId),
        });
        // Refresh conversations
        fetchConversations(parseInt(agentId));
      } catch (error) {
        console.error('Failed to create conversation:', error);
      }
    }
  };

  return (
    <div className="flex flex-col h-full bg-background border-r border-gray-200 dark:border-gray-300">
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-300">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Conversations</h2>
        <div className="flex flex-row items-center">
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center justify-center rounded-md cursor-pointer hover:bg-gray-100 size-8">
                <Tools
                  onClick={() => { }}
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
                <ChatPlusIn onClick={handleNewChat} width={18} height={18} className="text-gray-600" />
              </div>
            </TooltipTrigger>
            <TooltipContent side="bottom">New chat</TooltipContent>
          </Tooltip>
        </div>
      </div>

      <div className="flex flex-col gap-2 h-[calc(100vh-130px)] overflow-scroll scrollbar-hide">
        <div className="flex flex-col gap-3 px-2">
          {isLoading ? (
            <div className="flex items-center justify-center p-4">
              <div className="text-sm text-gray-500">Loading conversations...</div>
            </div>
          ) : conversations.length > 0 ? (
            conversations.map((conversation: ConversationRead) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isActive={conversation.id === parseInt(conversation_id || '0')}
                onSelect={() => handleSelectConversation(conversation)}
                onRename={() => handleOpenRename(conversation)}
                onDelete={() => handleDelete(conversation)}
              />
            ))
          ) : (
            <span className="pl-3 text-sm text-gray-400">History is empty</span>
          )}
        </div>
      </div>

      {/* Rename Dialog */}
      <Dialog open={isRenameOpen} onOpenChange={setIsRenameOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Conversation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Enter new name"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleRename();
                }
              }}
            />
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setIsRenameOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleRename}>Rename</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Conversation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p>Are you sure you want to delete this conversation? This action cannot be undone.</p>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setIsDeleteOpen(false)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={confirmDelete}>
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
