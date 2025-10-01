import * as React from 'react';
import { useState } from 'react';
import { 
  ChatBubble, 
  Bug, 
  LightBulb, 
  Send, 
  CheckCircle, 
  Page,
  User,
  Mail
} from 'iconoir-react';
import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

// Types following UI Style Guide
interface SupportFormData {
  type: 'feedback' | 'bug' | 'feature';
  title: string;
  description: string;
  email: string;
  priority?: 'low' | 'medium' | 'high';
  category?: string;
  stepsToReproduce?: string;
  expectedBehavior?: string;
  actualBehavior?: string;
  attachments?: File[];
}

interface TabConfig {
  id: 'feedback' | 'bug' | 'feature';
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  color: string;
}

const TAB_CONFIG: Record<string, TabConfig> = {
  feedback: {
    id: 'feedback',
    label: 'General Feedback',
    icon: ChatBubble,
    description: 'Share your thoughts, suggestions, or general feedback about Dana Studio',
    color: 'text-blue-600',
  },
  bug: {
    id: 'bug',
    label: 'Bug Report',
    icon: Bug,
    description: 'Report issues, errors, or unexpected behavior you\'ve encountered',
    color: 'text-red-600',
  },
  feature: {
    id: 'feature',
    label: 'Feature Request',
    icon: LightBulb,
    description: 'Suggest new features or improvements to enhance Dana Studio',
    color: 'text-green-600',
  },
};

export default function SupportPage() {
  const [activeTab, setActiveTab] = useState<'feedback' | 'bug' | 'feature'>('feedback');
  const [formData, setFormData] = useState<SupportFormData>({
    type: 'feedback',
    title: '',
    description: '',
    email: '',
    priority: 'medium',
    category: '',
    stepsToReproduce: '',
    expectedBehavior: '',
    actualBehavior: '',
    attachments: [],
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleTabChange = (tabId: 'feedback' | 'bug' | 'feature') => {
    setActiveTab(tabId);
    setFormData(prev => ({ ...prev, type: tabId }));
    setSubmitStatus('idle');
  };

  const handleInputChange = (field: keyof SupportFormData, value: string | File[]) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      // Simulate API call - replace with actual implementation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      console.log('Support form submitted:', formData);
      setSubmitStatus('success');
      
      // Reset form
      setFormData({
        type: activeTab,
        title: '',
        description: '',
        email: '',
        priority: 'medium',
        category: '',
        stepsToReproduce: '',
        expectedBehavior: '',
        actualBehavior: '',
        attachments: [],
      });
    } catch (error) {
      console.error('Error submitting support form:', error);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderFormFields = () => {
    const currentTab = TAB_CONFIG[activeTab];
    
    return (
      <div className="space-y-6">
        {/* Common Fields */}
        <div className="space-y-4">
          <div>
            <label htmlFor="title" className="block mb-2 text-sm font-medium text-gray-900">
              Title *
            </label>
            <Input
              id="title"
              type="text"
              placeholder={`Brief ${currentTab.label.toLowerCase()} title`}
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              className="w-full"
              required
            />
          </div>

          <div>
            <label htmlFor="email" className="block mb-2 text-sm font-medium text-gray-900">
              Email Address *
            </label>
            <Input
              id="email"
              type="email"
              placeholder="your.email@example.com"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              className="w-full"
              required
            />
          </div>

          <div>
            <label htmlFor="description" className="block mb-2 text-sm font-medium text-gray-900">
              Description *
            </label>
            <Textarea
              id="description"
              placeholder={`Please provide detailed information about your ${currentTab.label.toLowerCase()}...`}
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              className="w-full min-h-[120px]"
              required
            />
          </div>
        </div>

        {/* Tab-specific Fields */}
        {activeTab === 'bug' && (
          <div className="space-y-4">
            <Separator />
            <h3 className="text-lg font-semibold text-gray-900">Bug Report Details</h3>
            
            <div>
              <label htmlFor="priority" className="block mb-2 text-sm font-medium text-gray-900">
                Priority
              </label>
              <select
                id="priority"
                value={formData.priority}
                onChange={(e) => handleInputChange('priority', e.target.value as 'low' | 'medium' | 'high')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="low">Low - Minor issue</option>
                <option value="medium">Medium - Moderate impact</option>
                <option value="high">High - Critical issue</option>
              </select>
            </div>

            <div>
              <label htmlFor="stepsToReproduce" className="block mb-2 text-sm font-medium text-gray-900">
                Steps to Reproduce
              </label>
              <Textarea
                id="stepsToReproduce"
                placeholder="1. Go to...&#10;2. Click on...&#10;3. See error..."
                value={formData.stepsToReproduce}
                onChange={(e) => handleInputChange('stepsToReproduce', e.target.value)}
                className="w-full min-h-[100px]"
              />
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label htmlFor="expectedBehavior" className="block mb-2 text-sm font-medium text-gray-900">
                  Expected Behavior
                </label>
                <Textarea
                  id="expectedBehavior"
                  placeholder="What should have happened?"
                  value={formData.expectedBehavior}
                  onChange={(e) => handleInputChange('expectedBehavior', e.target.value)}
                  className="w-full min-h-[80px]"
                />
              </div>
              <div>
                <label htmlFor="actualBehavior" className="block mb-2 text-sm font-medium text-gray-900">
                  Actual Behavior
                </label>
                <Textarea
                  id="actualBehavior"
                  placeholder="What actually happened?"
                  value={formData.actualBehavior}
                  onChange={(e) => handleInputChange('actualBehavior', e.target.value)}
                  className="w-full min-h-[80px]"
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'feature' && (
          <div className="space-y-4">
            <Separator />
            <h3 className="text-lg font-semibold text-gray-900">Feature Request Details</h3>
            
            <div>
              <label htmlFor="category" className="block mb-2 text-sm font-medium text-gray-900">
                Category
              </label>
              <select
                id="category"
                value={formData.category}
                onChange={(e) => handleInputChange('category', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select a category</option>
                <option value="ui-ux">UI/UX Improvement</option>
                <option value="functionality">New Functionality</option>
                <option value="performance">Performance Enhancement</option>
                <option value="integration">Integration</option>
                <option value="accessibility">Accessibility</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label htmlFor="priority" className="block mb-2 text-sm font-medium text-gray-900">
                Priority
              </label>
              <select
                id="priority"
                value={formData.priority}
                onChange={(e) => handleInputChange('priority', e.target.value as 'low' | 'medium' | 'high')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="low">Low - Nice to have</option>
                <option value="medium">Medium - Would be helpful</option>
                <option value="high">High - Critical need</option>
              </select>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end pt-4">
          <Button
            type="submit"
            disabled={isSubmitting || !formData.title || !formData.description || !formData.email}
            className="px-8"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Submit {currentTab.label}
              </>
            )}
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-4 py-8 mx-auto max-w-7xl sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="mb-2 text-2xl font-bold text-gray-900">Support Center</h1>
            <p className="mx-auto mb-6 max-w-3xl text-gray-600 text-sm">
              We're here to help! Share your feedback, report bugs, or suggest new features to make Dana Studio even better.
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-4 py-6 mx-auto max-w-4xl sm:px-6 lg:px-8">
        {/* Success/Error Messages */}
        {submitStatus === 'success' && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Thank you!</h3>
                <p className="mt-1 text-sm text-green-700">
                  Your {TAB_CONFIG[activeTab].label.toLowerCase()} has been submitted successfully. We'll review it and get back to you soon.
                </p>
              </div>
            </div>
          </div>
        )}

        {submitStatus === 'error' && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Submission Failed</h3>
                <p className="mt-1 text-sm text-red-700">
                  There was an error submitting your request. Please try again or contact support directly.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {Object.values(TAB_CONFIG).map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabChange(tab.id)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                      isActive
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center">
                      <Icon className={`w-5 h-5 mr-2 ${isActive ? tab.color : 'text-gray-400'}`} />
                      {tab.label}
                    </div>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Form */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  {React.createElement(TAB_CONFIG[activeTab].icon, { 
                    className: `w-6 h-6 mr-2 ${TAB_CONFIG[activeTab].color}` 
                  })}
                  {TAB_CONFIG[activeTab].label}
                </CardTitle>
                <CardDescription>
                  {TAB_CONFIG[activeTab].description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit}>
                  {renderFormFields()}
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Tips */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quick Tips</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start">
                  <Page className="w-5 h-5 text-blue-600 mt-0.5 mr-3" />
                  <div>
                    <h4 className="font-medium text-gray-900">Be Specific</h4>
                    <p className="text-sm text-gray-600">
                      Provide clear, detailed descriptions to help us understand your request.
                    </p>
                  </div>
                </div>
                <div className="flex items-start">
                  <User className="w-5 h-5 text-green-600 mt-0.5 mr-3" />
                  <div>
                    <h4 className="font-medium text-gray-900">Include Context</h4>
                    <p className="text-sm text-gray-600">
                      Share your use case and how this would benefit your workflow.
                    </p>
                  </div>
                </div>
                <div className="flex items-start">
                  <Mail className="w-5 h-5 text-purple-600 mt-0.5 mr-3" />
                  <div>
                    <h4 className="font-medium text-gray-900">Stay Updated</h4>
                    <p className="text-sm text-gray-600">
                      We'll email you updates on your submission status.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Contact Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Need Immediate Help?</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-gray-600">
                  For urgent issues or questions, you can reach us directly:
                </p>
                <div className="space-y-2">
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => window.open('mailto:support@aitomatic.com', '_blank')}
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    support@aitomatic.com
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Status Badges */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Response Times</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Bug Reports</span>
                  <Badge variant="destructive">24-48 hours</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Feature Requests</span>
                  <Badge variant="secondary">1-2 weeks</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">General Feedback</span>
                  <Badge variant="outline">3-5 days</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
