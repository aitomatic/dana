import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { IconPlus } from '@tabler/icons-react';
import { IconClipboard } from '@tabler/icons-react';
import { IconSchool } from '@tabler/icons-react';
import { NetworkRightSolid } from 'iconoir-react';
import { useKnowledgePackStore } from '@/stores';

interface CreateItemDropdownProps {
  onKnowledgePackClick?: () => void;
  onContributionTemplateClick?: () => void;
  onCaptureKnowledgeClick?: () => void;
}

export function CreateItemDropdown({
  onKnowledgePackClick,
  onContributionTemplateClick,
  onCaptureKnowledgeClick,
}: CreateItemDropdownProps) {
  const { setKnowledgePackOpen } = useKnowledgePackStore();

  const handleKnowledgePackClick = () => {
    if (onKnowledgePackClick) {
      onKnowledgePackClick();
    } else {
      setKnowledgePackOpen(true);
    }
  };

  const handleContributionTemplateClick = () => {
    if (onContributionTemplateClick) {
      onContributionTemplateClick();
    }
  };

  const handleCaptureKnowledgeClick = () => {
    if (onCaptureKnowledgeClick) {
      onCaptureKnowledgeClick();
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button size="lg" className="gap-2">
          <IconPlus className="w-4 h-4" />
          Create
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        {/* Knowledge Pack */}
        <DropdownMenuItem
          onClick={handleKnowledgePackClick}
          className="flex gap-3 items-start p-3 rounded-lg transition-all duration-300 cursor-pointer hover:bg-gray-50 dark:hover:bg-surface-light"
        >
          <NetworkRightSolid className="w-5 h-5 mt-0.5 text-orange-500" />
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              Knowledge Pack
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Ready-to-use knowledge pack from various sources
            </span>
          </div>
        </DropdownMenuItem>

        {/* Capture Template */}
        <DropdownMenuItem
          onClick={handleContributionTemplateClick}
          className="flex gap-3 items-start p-3 rounded-lg transition-all duration-300 cursor-pointer hover:bg-gray-50 dark:hover:bg-surface-light"
        >
          <IconClipboard className="w-5 h-5 mt-0.5 text-blue-500" />
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              Capture Template
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
            Template for to knowledge capture
            </span>
          </div>
        </DropdownMenuItem>

        {/* Capture Knowledge */}
        <DropdownMenuItem
          onClick={handleCaptureKnowledgeClick}
          className="flex gap-3 items-start p-3 rounded-lg transition-all duration-300 cursor-pointer hover:bg-gray-50 dark:hover:bg-surface-light"
        >
          <IconSchool className="w-5 h-5 mt-0.5 text-green-500" />
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium text-gray-900 dark:text-white">
             Capture Knowledge
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Interview session to capture knowledge
            </span>
          </div>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
