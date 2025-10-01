import { Bug, LightBulb, Mail, Clock, CheckCircle, ArrowRight } from 'iconoir-react';
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
        <div className="w-full max-w-4xl">
          {/* SLA Information */}
          <div className="mb-8 text-center">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Our Service Level Agreements</h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="flex items-center justify-center gap-2 p-3 bg-white rounded-lg border border-gray-200">
                <Clock className="w-5 h-5 text-red-600" />
                <div className="text-left">
                  <div className="text-sm font-medium text-gray-900">Critical Bugs</div>
                  <div className="text-xs text-gray-600">Response: &lt; 24h</div>
                </div>
              </div>
              <div className="flex items-center justify-center gap-2 p-3 bg-white rounded-lg border border-gray-200">
                <Clock className="w-5 h-5 text-yellow-600" />
                <div className="text-left">
                  <div className="text-sm font-medium text-gray-900">Bug Reports</div>
                  <div className="text-xs text-gray-600">Response: 3-5 days</div>
                </div>
              </div>
              <div className="flex items-center justify-center gap-2 p-3 bg-white rounded-lg border border-gray-200">
                <Clock className="w-5 h-5 text-blue-600" />
                <div className="text-left">
                  <div className="text-sm font-medium text-gray-900">Feature Requests</div>
                  <div className="text-xs text-gray-600">Review: 1-2 weeks</div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Support Options */}
          <Card className="mb-8">
            <CardHeader className="text-center">
              <CardTitle className="text-xl">Submit Your Request</CardTitle>
              <CardDescription>
                Choose the appropriate form for your support request
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                {/* Feature Request Card */}
                <Card 
                  className="group cursor-pointer transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-2 hover:border-blue-300"
                  onClick={() => window.open('https://aitomatic-project-hub.atlassian.net/jira/software/c/form/1724931d-cd6c-4af8-b5c0-d72d85ba5707', '_blank')}
                >
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-3 bg-blue-100 rounded-full group-hover:bg-blue-200 transition-colors">
                          <LightBulb className="w-6 h-6 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">Feature Request</h3>
                          <p className="text-sm text-gray-600">Suggest new features</p>
                        </div>
                      </div>
                      <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors" />
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-gray-700">Product roadmap consideration</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-gray-700">Community voting</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-gray-700">Regular updates</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Bug Report Card */}
                <Card 
                  className="group cursor-pointer transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-2 hover:border-red-300"
                  onClick={() => window.open('https://aitomatic-project-hub.atlassian.net/jira/software/c/form/b446c093-0534-4fc9-8c61-b61e733453d5', '_blank')}
                >
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-3 bg-red-100 rounded-full group-hover:bg-red-200 transition-colors">
                          <Bug className="w-6 h-6 text-red-600" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">Bug Report</h3>
                          <p className="text-sm text-gray-600">Report issues & errors</p>
                        </div>
                      </div>
                      <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-red-600 transition-colors" />
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-gray-700">Priority-based triage</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-gray-700">Developer assignment</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm text-gray-700">Progress tracking</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
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