import * as React from 'react';
import { useLocation } from 'react-router-dom';
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { AppSidebar } from './app-sidebar';

interface LayoutProps {
  children: React.ReactNode;
  hideLayout?: boolean; // Add this prop
}

export function Layout({ children, hideLayout = false }: LayoutProps) {
  const location = useLocation();

  // Get page title based on current route - moved before early return
  const getPageTitle = React.useCallback(() => {
    switch (location.pathname) {
      case '/':
        return 'Home';
      case '/agents':
        return 'Dana Expert Agents';
      case '/library':
        return 'Library';
      default:
        // Handle dynamic routes
        if (location.pathname.startsWith('/agents/') && location.pathname.includes('/chat')) {
          return 'Agent Chat';
        }
        if (location.pathname.startsWith('/agents/')) {
          return 'Agent Details';
        }
        return 'Agent workspace';
    }
  }, [location.pathname]);

  // If hideLayout is true, render children without layout
  if (hideLayout) {
    return <>{children}</>;
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex gap-2 items-center px-4 h-16 border-b shrink-0">
          <SidebarTrigger className="-ml-1 text-gray-500 size-6" />
          <div className="flex gap-2 items-center">
            <span className="text-lg font-semibold">{getPageTitle()}</span>
          </div>
        </header>
        <main className="overflow-auto flex-1">{children}</main>
      </SidebarInset>
    </SidebarProvider>
  );
}
