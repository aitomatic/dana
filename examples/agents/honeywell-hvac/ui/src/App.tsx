import { useEffect, useState } from 'react';
import { EnvironmentPanel } from './components/hvac/EnvironmentPanel';
import { ExecutionProgress } from './components/hvac/ExecutionProgress';
import { AgentPlanVisualization } from './components/hvac/AgentPlanVisualization';
import { FeedbackDetail } from './components/hvac/FeedbackDetail';
import { LearningGrowthTracker } from './components/hvac/LearningGrowthTracker';
import { AccumulatedKnowledgePanel } from './components/hvac/AccumulatedKnowledgePanel';
import { CurrentLearningHighlight } from './components/hvac/CurrentLearningHighlight';
import { SessionSelector } from './components/hvac/SessionSelector';
import { LearningMetrics } from './components/hvac/LearningMetrics';
import { useHVACFlow } from './hooks/use-hvac-flow';
import { useHVACStore } from './stores/hvac-store';

export default function App() {
  const { loadLearnings } = useHVACFlow();
  const { currentSession, agentPlan, feedback } = useHVACStore();
  const [showFeedback, setShowFeedback] = useState(false);
  const [showLearning, setShowLearning] = useState(false);

  useEffect(() => {
    if (currentSession) {
      loadLearnings(currentSession.session_id);
    }
  }, [currentSession, loadLearnings]);

  // Show feedback card 5 seconds after agent plan appears
  useEffect(() => {
    if (agentPlan) {
      const timer = setTimeout(() => {
        setShowFeedback(true);
      }, 5000);
      return () => clearTimeout(timer);
    } else {
      setShowFeedback(false);
    }
  }, [agentPlan]);

  // Show learning card 5 seconds after feedback appears
  useEffect(() => {
    if (feedback && showFeedback) {
      const timer = setTimeout(() => {
        setShowLearning(true);
      }, 5000);
      return () => clearTimeout(timer);
    } else {
      setShowLearning(false);
    }
  }, [feedback, showFeedback]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">HVAC Agent Demo</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Autonomous HVAC control with continuous learning
            </p>
          </div>
          <div className="flex items-center gap-4">
            <SessionSelector />
            <LearningMetrics />
          </div>
        </div>
      </header>

      <main className="grid grid-cols-12 gap-4 p-6 h-[calc(100vh-100px)]">
        {/* Left Panel: Environment + Execution Progress */}
        <div className="col-span-3 space-y-4 overflow-y-auto">
          <EnvironmentPanel />
          <ExecutionProgress 
            showPlanComplete={!!agentPlan}
            showValidationComplete={showFeedback}
            showLearningComplete={showLearning}
          />
        </div>

        {/* Center Panel: Agent Plan + Feedback + Accumulated Knowledge */}
        {(agentPlan || feedback) && (
          <div className="col-span-6 space-y-4 overflow-y-auto animate-fade-in-up">
            {agentPlan && (
              <div className="animate-fade-in-up animation-delay-100">
                <AgentPlanVisualization />
              </div>
            )}
            {feedback && showFeedback && (
              <div className="animate-fade-in-up animation-delay-200">
                <FeedbackDetail />
              </div>
            )}
            <AccumulatedKnowledgePanel />
          </div>
        )}

        {/* Right Panel: New Learning + Learned Insights */}
        <div className="col-span-3 space-y-4 overflow-y-auto">
          {showLearning && <CurrentLearningHighlight />}
          <LearningGrowthTracker />
        </div>
      </main>
    </div>
  );
}
