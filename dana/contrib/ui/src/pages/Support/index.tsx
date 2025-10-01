import React from 'react';
import { Bug, LightBulb, Mail } from 'iconoir-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function SupportPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-4 py-8 mx-auto max-w-7xl sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="mb-2 text-2xl font-bold text-gray-900">Support Center</h1>
            <p className="mx-auto mb-6 max-w-3xl text-gray-600 text-sm">
              We're here to help! Submit your feedback, report bugs, or suggest new features to make Dana Studio even better.
            </p>
          </div>
        </div>
      </div>

      {/* Main Content - Centered */}
      <div className="flex items-center justify-center min-h-[60vh] px-4 py-12">
        <div className="w-full max-w-2xl">
          {/* Main Support Options */}
          <Card className="mb-8">
            <CardHeader className="text-center">
              <CardTitle className="text-xl">Submit Your Request</CardTitle>
              <CardDescription>
                Choose the appropriate form for your support request
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {/* Feature Request Button */}
                <Button
                  onClick={() => window.open('https://aitomatic-project-hub.atlassian.net/jira/software/c/form/1724931d-cd6c-4af8-b5c0-d72d85ba5707', '_blank')}
                  className="h-16 flex-col gap-2 bg-blue-600 hover:bg-blue-700 text-white"
                  size="lg"
                >
                  <LightBulb className="w-6 h-6" />
                  <span className="font-medium">Feature Request</span>
                </Button>

                {/* Bug Report Button */}
                <Button
                  onClick={() => window.open('https://aitomatic-project-hub.atlassian.net/jira/software/c/form/b446c093-0534-4fc9-8c61-b61e733453d5', '_blank')}
                  className="h-16 flex-col gap-2 bg-red-600 hover:bg-red-700 text-white"
                  size="lg"
                >
                  <Bug className="w-6 h-6" />
                  <span className="font-medium">Bug Report</span>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Contact Information */}
          <Card>
            <CardHeader className="text-center">
              <CardTitle className="text-lg">Need Immediate Help?</CardTitle>
              <CardDescription>
                For urgent issues or questions, contact us directly
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <Button
                variant="outline"
                onClick={() => window.open('mailto:support@aitomatic.com', '_blank')}
                className="gap-2"
              >
                <Mail className="w-4 h-4" />
                support@aitomatic.com
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}