import * as React from 'react';
import { Book, Box3dCenter } from 'iconoir-react';
import { useLocation } from 'react-router-dom';

import { NavMain } from '@/components/nav-main';
import { TeamSwitcher } from '@/components/team-switcher';
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarRail,
  SidebarFooter,
} from '@/components/ui/sidebar';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useSidebar } from '@/hooks/use-sidebar';

// Import logo as a module
import logo from '/logo.svg';
// Import version from package.json
import packageJson from '../../package.json';

// DXA DANA configuration data
const data = {
  user: {
    name: 'Username',
    email: 'user@example.com',
    avatar: '',
  },
  teams: [
    {
      name: 'Aitomatic',
      logo: () => <img src={logo} alt="Aitomatic" className="rounded-md size-8" />,
      plan: 'Dana Agent Studio',
    },
  ],
  navMain: [
    {
      title: 'Dana Expert Agents',
      url: '/agents',
      icon: Box3dCenter,
    },
    {
      title: 'Library',
      url: '/library',
      icon: Book,
    },
  ],
};

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation();
  const { state } = useSidebar();

  // Create navigation items with dynamic active state
  const navItems = React.useMemo(() => {
    return data.navMain.map((item) => ({
      ...item,
      isActive: location.pathname === item.url,
    }));
  }, [location.pathname]);

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent className="flex-1">
        <NavMain items={navItems} />
      </SidebarContent>
      <SidebarFooter className="flex p-4 border-t">
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="text-sm text-muted-foreground">
              {state === 'collapsed' ? `${packageJson.version}` : `Version-${packageJson.version}`}
            </span>
          </TooltipTrigger>
          <TooltipContent side="right">Version {packageJson.version}</TooltipContent>
        </Tooltip>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
