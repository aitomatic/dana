import * as React from "react";
import { Book, Box3dCenter } from "iconoir-react";
import { useLocation } from "react-router-dom";

import { NavMain } from "@/components/nav-main";
import { TeamSwitcher } from "@/components/team-switcher";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";

// DXA DANA configuration data
const data = {
  user: {
    name: "Username",
    email: "user@example.com",
    avatar: "",
  },
  teams: [
    {
      name: "DXA DANA",
      logo: () => (
        <img
          src="/static/logo.svg"
          alt="DXA DANA"
          className="size-8 rounded-md"
        />
      ),
      plan: "Domain-Expert Agents",
    },
  ],
  navMain: [
    {
      title: "Domain-Expert Agents",
      url: "/agents",
      icon: Box3dCenter,
    },
    {
      title: "Library",
      url: "/library",
      icon: Book,
    },
  ],
};

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation();

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
      <SidebarContent>
        <NavMain items={navItems} />
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
