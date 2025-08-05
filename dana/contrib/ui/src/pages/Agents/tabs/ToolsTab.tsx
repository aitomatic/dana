import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  IconSearch,
  IconPlus,
  IconDatabase,
  IconCalendar,
  IconCloud,
  IconWorld,
  IconListCheck,
} from '@tabler/icons-react';

// Mock tool data
const mockTools = [
  {
    id: 1,
    name: 'Google Patents',
    description: 'Connect to Google Patents to retrieve Patent document',
    icon: <img src="https://www.google.com/favicon.ico" alt="Google" className="w-6 h-6" />,
  },
  {
    id: 2,
    name: 'Calendar Integration',
    description: 'Connect to Google Patents to retrieve Patent document',
    icon: <IconCalendar className="w-6 h-6 text-blue-500" />,
  },
  {
    id: 3,
    name: 'Internal Storage Access',
    description: 'Connect to Google Patents to retrieve Patent document',
    icon: <IconDatabase className="w-6 h-6 text-indigo-500" />,
  },
  {
    id: 4,
    name: 'Web Search',
    description: 'Connect to Google Patents to retrieve Patent document',
    icon: <IconWorld className="w-6 h-6 text-gray-500" />,
  },
  {
    id: 5,
    name: 'Big Query',
    description: 'Connect to Google Patents to retrieve Patent document',
    icon: <IconCloud className="w-6 h-6 text-purple-500" />,
  },
  {
    id: 6,
    name: 'Big Query',
    description: 'Connect to Google Patents to retrieve Patent document',
    icon: <IconCloud className="w-6 h-6 text-purple-500" />,
  },
  {
    id: 7,
    name: 'Scheduling events',
    description: 'Connect to Google Patents to retrieve Patent document',
    icon: <IconListCheck className="w-6 h-6 text-green-500" />,
  },
  {
    id: 8,
    name: 'Scheduling events',
    description: 'Connect to Google Patents to retrieve Patent document',
    icon: <IconListCheck className="w-6 h-6 text-green-500" />,
  },
  {
    id: 9,
    name: 'Scheduling events',
    description: 'Connect to Google Patents to retrieve Patent document',
    icon: <IconListCheck className="w-6 h-6 text-green-500" />,
  },
];

const ToolsTab: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredTools = mockTools.filter((tool) =>
    tool.name.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <div className="flex flex-col p-6 h-full bg-white rounded-lg">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Tools</h1>
        <Button variant="outline" className="flex items-center">
          <IconPlus className="mr-2 w-4 h-4" /> Add Tool
        </Button>
      </div>
      <div className="mb-6 max-w-sm">
        <div className="relative">
          <IconSearch className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
          <Input
            placeholder="Search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3">
        {filteredTools.map((tool) => (
          <div
            key={tool.id}
            className="bg-white border border-gray-200 rounded-xl p-6 flex flex-col shadow-sm hover:shadow-md transition-shadow min-h-[140px]"
          >
            <div className="flex items-center mb-4">
              {tool.icon}
              <span className="ml-3 text-lg font-semibold text-gray-900">{tool.name}</span>
            </div>
            <p className="flex-1 text-sm text-gray-600">{tool.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ToolsTab;
