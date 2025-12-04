/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { toast } from 'sonner';
import { apiService } from '@/lib/api';
import { IconRefresh, IconCheck } from '@tabler/icons-react';

interface PromptSetting {
  category: string;
  key: string;
  full_key: string;
  value: string | null;
  name: string;
  description: string;
  placeholders: string[];
  placeholder_examples: Record<string, string>;
  default_value: string | null;
  applies_to: string;
  is_active: boolean;
}

interface PromptSettingsResponse {
  settings: Record<string, PromptSetting[]>;
  categories: string[];
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<PromptSettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [editedValues, setEditedValues] = useState<Record<string, string>>({});

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await apiService.getAllPromptSettings();
      setSettings(response);
      // Initialize edited values with current values
      const initialValues: Record<string, string> = {};
      (Object.values(response.settings) as PromptSetting[][]).forEach((categorySettings) => {
        categorySettings.forEach((setting) => {
          initialValues[setting.full_key] = setting.value || '';
        });
      });
      setEditedValues(initialValues);
    } catch (error: any) {
      toast.error(`Failed to load settings: ${error?.message || 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (category: string, key: string, fullKey: string) => {
    try {
      setSaving((prev) => ({ ...prev, [fullKey]: true }));
      const value = editedValues[fullKey] || '';
      await apiService.updatePromptSetting(category, key, value);
      toast.success(`Prompt setting ${fullKey} updated successfully`);
      await loadSettings(); // Reload to get updated values
    } catch (error: any) {
      toast.error(`Failed to update setting: ${error?.message || 'Unknown error'}`);
    } finally {
      setSaving((prev) => ({ ...prev, [fullKey]: false }));
    }
  };

  const handleReset = async (category: string, key: string, fullKey: string) => {
    try {
      setSaving((prev) => ({ ...prev, [fullKey]: true }));
      await apiService.resetPromptSetting(category, key);
      toast.success(`Prompt setting ${fullKey} reset to default`);
      await loadSettings(); // Reload to get reset values
    } catch (error: any) {
      toast.error(`Failed to reset setting: ${error?.message || 'Unknown error'}`);
    } finally {
      setSaving((prev) => ({ ...prev, [fullKey]: false }));
    }
  };

  const handleValueChange = (fullKey: string, value: string) => {
    setEditedValues((prev) => ({ ...prev, [fullKey]: value }));
  };

  const copyPlaceholderToClipboard = async (placeholder: string) => {
    try {
      await navigator.clipboard.writeText(placeholder);
      toast.success(`Copied ${placeholder} to clipboard`);
    } catch (error: any) {
      toast.error(`Failed to copy to clipboard: ${error?.message || 'Unknown error'}`);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">Settings</h1>
        <p>Loading settings...</p>
      </div>
    );
  }

  if (!settings || settings.categories.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">Settings</h1>
        <p>No prompt settings found.</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-muted-foreground">Configure global prompt settings for knowledge generation</p>
      </div>

      <Tabs defaultValue={settings.categories[0]} className="w-full">
        <TabsList className="grid w-full grid-cols-auto">
          {settings.categories.map((category) => (
            <TabsTrigger key={category} value={category}>
              {category.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
            </TabsTrigger>
          ))}
        </TabsList>

        {settings.categories.map((category) => (
          <TabsContent key={category} value={category} className="space-y-4">
            {settings.settings[category]?.map((setting) => (
              <Card key={setting.full_key}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle>{setting.name}</CardTitle>
                      <CardDescription className="mt-2">{setting.description}</CardDescription>
                    </div>
                    <div className="flex gap-2">
                      {setting.default_value && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleReset(setting.category, setting.key, setting.full_key)}
                          disabled={saving[setting.full_key]}
                        >
                          <IconRefresh className="h-4 w-4 mr-2" />
                          Reset to Default
                        </Button>
                      )}
                      <Button
                        size="sm"
                        onClick={() => handleSave(setting.category, setting.key, setting.full_key)}
                        disabled={saving[setting.full_key]}
                      >
                        <IconCheck className="h-4 w-4 mr-2" />
                        {saving[setting.full_key] ? 'Saving...' : 'Save'}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {setting.placeholders.length > 0 && (
                    <div>
                      <Label className="mb-2 block">Available Variables</Label>
                      <div className="flex flex-wrap gap-2">
                        {setting.placeholders.map((placeholder) => {
                          const example = setting.placeholder_examples?.[placeholder];
                          return (
                            <Tooltip key={placeholder}>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => copyPlaceholderToClipboard(placeholder)}
                                  className="font-mono text-xs"
                                >
                                  {placeholder}
                                </Button>
                              </TooltipTrigger>
                              {example && (
                                <TooltipContent side="top" className="max-w-md bg-popover text-popover-foreground">
                                  <div className="space-y-2">
                                    <div className="font-semibold">Example:</div>
                                    <div className="text-sm whitespace-pre-wrap font-mono bg-secondary text-secondary-foreground p-2 rounded border border-border">
                                      {example}
                                    </div>
                                  </div>
                                </TooltipContent>
                              )}
                            </Tooltip>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  <div>
                    <Label htmlFor={`textarea-${setting.full_key}`}>Prompt Content</Label>
                    <Textarea
                      id={`textarea-${setting.full_key}`}
                      value={editedValues[setting.full_key] || ''}
                      onChange={(e) => handleValueChange(setting.full_key, e.target.value)}
                      className="mt-2 font-mono text-sm min-h-[300px]"
                      placeholder="Enter prompt content..."
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}

