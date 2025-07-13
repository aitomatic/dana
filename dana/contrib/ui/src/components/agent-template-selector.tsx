import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { IconEye, IconCode, IconCheck } from '@tabler/icons-react';
import { AGENT_TEMPLATES } from '@/constants/dana-code';

interface AgentTemplateSelectorProps {
  onTemplateSelect: (
    templateCode: string,
    templateName: string,
    templateDescription: string,
  ) => void;
  className?: string;
}

const AgentTemplateSelector = ({ onTemplateSelect, className }: AgentTemplateSelectorProps) => {
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState('all');

  const handleTemplateSelect = (templateKey: string) => {
    const template = AGENT_TEMPLATES[templateKey as keyof typeof AGENT_TEMPLATES];
    if (template) {
      onTemplateSelect(template.code, template.name, template.description);
      setSelectedTemplate(templateKey);
    }
  };

  const handlePreviewTemplate = (templateKey: string) => {
    setPreviewTemplate(templateKey);
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      General: '🤖',
      Information: '📊',
      Analytics: '📈',
      Business: '💼',
      Finance: '💰',
      Development: '💻',
      Content: '✍️',
      Health: '🏥',
      Legal: '⚖️',
      Education: '🎓',
      Research: '🔬',
    };
    return icons[category] || '📋';
  };

  const getFilteredTemplates = () => {
    const templates = Object.entries(AGENT_TEMPLATES);

    switch (activeCategory) {
      case 'general':
        return templates.filter(([key]) =>
          ['SIMPLE_ASSISTANT', 'WEATHER_AGENT', 'RESEARCH_AGENT'].includes(key),
        );
      case 'business':
        return templates.filter(([key]) =>
          [
            'CUSTOMER_SUPPORT',
            'PROJECT_MANAGER',
            'MARKETING_SPECIALIST',
            'FINANCIAL_ADVISOR',
          ].includes(key),
        );
      case 'technical':
        return templates.filter(([key]) => ['CODE_REVIEWER', 'DATA_ANALYSIS'].includes(key));
      case 'specialized':
        return templates.filter(([key]) =>
          ['CONTENT_WRITER', 'HEALTH_ADVISOR', 'LEGAL_ADVISOR', 'EDUCATIONAL_TUTOR'].includes(key),
        );
      default:
        return templates;
    }
  };

  const categories = [
    { id: 'all', name: 'All' },
    { id: 'general', name: 'General' },
    { id: 'business', name: 'Business' },
    { id: 'technical', name: 'Technical' },
    { id: 'specialized', name: 'Specialized' },
  ];

  return (
    <div className={className}>
      <div className="mb-4">
        <h3 className="mb-2 text-lg font-semibold text-gray-900">Choose a Template</h3>
        <p className="text-sm text-gray-600">
          Select a template to get started quickly, or start from scratch with a blank template.
        </p>
      </div>

      {/* Category Tabs */}
      <div className="flex overflow-x-auto gap-2 mb-4">
        {categories.map((category) => (
          <Button
            key={category.id}
            variant={activeCategory === category.id ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveCategory(category.id)}
            className="whitespace-nowrap"
          >
            {category.name}
          </Button>
        ))}
      </div>

      {/* Template Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[400px] overflow-y-auto">
        {getFilteredTemplates().map(([key, template]) => (
          <TemplateCard
            key={key}
            templateKey={key}
            template={template}
            isSelected={selectedTemplate === key}
            onSelect={() => handleTemplateSelect(key)}
            onPreview={() => handlePreviewTemplate(key)}
          />
        ))}
      </div>

      {/* Template Preview Dialog */}
      {previewTemplate && (
        <Dialog open={!!previewTemplate} onOpenChange={() => setPreviewTemplate(null)}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
            <DialogHeader>
              <DialogTitle>
                {AGENT_TEMPLATES[previewTemplate as keyof typeof AGENT_TEMPLATES]?.name} - Template
                Preview
              </DialogTitle>
              <DialogDescription>
                {AGENT_TEMPLATES[previewTemplate as keyof typeof AGENT_TEMPLATES]?.description}
              </DialogDescription>
            </DialogHeader>
            <div className="flex flex-col gap-4">
              <div className="flex gap-2 items-center">
                <Badge variant="secondary">
                  {AGENT_TEMPLATES[previewTemplate as keyof typeof AGENT_TEMPLATES]?.category}
                </Badge>
                <span className="text-sm text-gray-500">
                  {getCategoryIcon(
                    AGENT_TEMPLATES[previewTemplate as keyof typeof AGENT_TEMPLATES]?.category ||
                      '',
                  )}
                </span>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 max-h-[400px] overflow-auto">
                <pre className="text-sm text-gray-800 whitespace-pre-wrap">
                  {AGENT_TEMPLATES[previewTemplate as keyof typeof AGENT_TEMPLATES]?.code}
                </pre>
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setPreviewTemplate(null)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => {
                    if (previewTemplate) {
                      handleTemplateSelect(previewTemplate);
                      setPreviewTemplate(null);
                    }
                  }}
                >
                  Use This Template
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

interface TemplateCardProps {
  templateKey: string;
  template: {
    name: string;
    description: string;
    code: string;
    category: string;
  };
  isSelected: boolean;
  onSelect: () => void;
  onPreview: () => void;
}

function TemplateCard({ template, isSelected, onSelect, onPreview }: TemplateCardProps) {
  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      General: '🤖',
      Information: '📊',
      Analytics: '📈',
      Business: '💼',
      Finance: '💰',
      Development: '💻',
      Content: '✍️',
      Health: '🏥',
      Legal: '⚖️',
      Education: '🎓',
      Research: '🔬',
    };
    return icons[category] || '📋';
  };

  return (
    <div
      className={`border rounded-lg p-4 cursor-pointer transition-all duration-200 hover:shadow-md ${
        isSelected ? 'bg-blue-50 ring-2 ring-blue-500' : 'bg-white'
      }`}
    >
      <div className="flex justify-between items-start mb-3">
        <div className="flex gap-2 items-center">
          <span className="text-2xl">{getCategoryIcon(template.category)}</span>
          <div>
            <h3 className="text-base font-semibold">{template.name}</h3>
            <Badge variant="secondary" className="text-xs">
              {template.category}
            </Badge>
          </div>
        </div>
        {isSelected && <IconCheck className="w-5 h-5 text-blue-600" />}
      </div>
      <p className="mb-3 text-sm text-gray-600">{template.description}</p>
      <div className="flex gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={(e) => {
            e.stopPropagation();
            onPreview();
          }}
          className="flex-1"
        >
          <IconEye className="mr-1 w-4 h-4" />
          Preview
        </Button>
        <Button
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onSelect();
          }}
          className="flex-1"
        >
          <IconCode className="mr-1 w-4 h-4" />
          Use
        </Button>
      </div>
    </div>
  );
}

export default AgentTemplateSelector;
