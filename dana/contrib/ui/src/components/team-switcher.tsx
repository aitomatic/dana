import * as React from 'react';
import { IconLayoutSidebarRightExpand } from '@tabler/icons-react';

import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from '@/components/ui/sidebar';
import { useSidebar } from '@/hooks/use-sidebar';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export function TeamSwitcher({
  teams,
}: {
  teams: {
    name: string;
    logo: React.ElementType;
    plan: string;
  }[];
}) {
  const [activeTeam] = React.useState(teams[0]);
  const { toggleSidebar, state } = useSidebar();

  if (!activeTeam) {
    return null;
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton
          size="lg"
          className="hover:bg-transparent hover:cursor-default hover:text-inherit"
        >
          <activeTeam.logo className="rounded-md size-8" />
          <div className="grid flex-1 text-sm leading-tight text-left">
            <span className="font-medium truncate">{activeTeam.name}</span>
            <span className="text-sm truncate">{activeTeam.plan}</span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className={cn('ml-auto cursor-pointer size-6')}
            onClick={(event: React.MouseEvent<HTMLButtonElement>) => {
              event.stopPropagation();
              toggleSidebar();
            }}
          >
            {state === 'expanded' && (
              <IconLayoutSidebarRightExpand className="text-gray-500 size-6" strokeWidth={1.5} />
            )}
            <span className="sr-only">Toggle Sidebar</span>
          </Button>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
