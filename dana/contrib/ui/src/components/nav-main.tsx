'use client';

import * as React from 'react';
import { IconChevronRight } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from '@/components/ui/sidebar';

export function NavMain({
  items,
}: {
  items: {
    title: string;
    url: string;
    icon?: React.ComponentType<{ className?: string }>;
    isActive?: boolean;
    items?: {
      title: string;
      url: string;
    }[];
  }[];
}) {
  const navigate = useNavigate();

  return (
    <SidebarGroup>
      <SidebarMenu>
        {items.map((item) => (
          <React.Fragment key={item.title}>
            {item.items ? (
              <Collapsible asChild defaultOpen={item.isActive} className="group/collapsible">
                <SidebarMenuItem>
                  <CollapsibleTrigger asChild>
                    <SidebarMenuButton
                      tooltip={item.title}
                      isActive={item.isActive}
                      className="h-12 [&[data-active=true]]:!bg-brand-50 [&[data-active=true]]:!text-brand-600 hover:!bg-gray-100 hover:!text-gray-600 text-gray-600"
                    >
                      {item.icon && <item.icon className="!size-5" />}
                      <span className="text-sm font-medium">{item.title}</span>
                      <IconChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                    </SidebarMenuButton>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <SidebarMenuSub>
                      {item.items?.map((subItem) => (
                        <SidebarMenuSubItem key={subItem.title}>
                          <SidebarMenuSubButton asChild>
                            <a
                              href="#"
                              onClick={(e) => {
                                e.preventDefault();
                                navigate(subItem.url);
                              }}
                            >
                              <span className="text-sm font-medium text-gray-900">
                                {subItem.title}
                              </span>
                            </a>
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                      ))}
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </SidebarMenuItem>
              </Collapsible>
            ) : (
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  tooltip={item.title}
                  isActive={item.isActive}
                  className="h-12 [&[data-active=true]]:!bg-brand-50 [&[data-active=true]]:!text-brand-600 hover:!bg-gray-100 hover:!text-gray-600 text-gray-600 [&>span:last-child]:truncate"
                >
                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      navigate(item.url);
                    }}
                  >
                    {item.icon && <item.icon className="!size-5" />}
                    <span className="text-sm font-medium">{item.title}</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )}
          </React.Fragment>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}
