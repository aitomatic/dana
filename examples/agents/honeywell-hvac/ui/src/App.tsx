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
  const { currentSession, agentPlan, feedback, environment, isLoading } = useHVACStore();
  const [showFeedback, setShowFeedback] = useState(false);
  const [showLearning, setShowLearning] = useState(false);
  const [hasRunAgent, setHasRunAgent] = useState(false);

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

  // Track if agent has been run - hide Learned Insights once agent runs
  useEffect(() => {
    if (isLoading || agentPlan) {
      setHasRunAgent(true);
    }
  }, [isLoading, agentPlan]);

  // Show Learned Insights only on first arrival (before any agent run)
  const showLearnedInsights = !hasRunAgent;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-border px-6 py-4">
        <div className="flex items-center justify-between mb-4">
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
        <ExecutionProgress 
          showPlanComplete={!!agentPlan}
          showValidationComplete={showFeedback}
          showLearningComplete={showLearning}
        />
        {environment && (
          <div className="mt-4 animate-fade-in-up">
            <EnvironmentPanel />
          </div>
        )}
      </header>

      <main className="grid grid-cols-12 gap-4 p-6 ]">
        {/* Left Panel: Agent Plan */}
        <div className="col-span-4 space-y-4 overflow-y-auto">
          {agentPlan && (
            <div className="animate-fade-in-up animation-delay-100">
              <AgentPlanVisualization />
            </div>
          )}
        </div>

        {/* Center Panel: Feedback + Accumulated Knowledge */}
        {feedback && (
          <div className="col-span-5 space-y-4 overflow-y-auto animate-fade-in-up">
            {showFeedback && (
              <div className="animate-fade-in-up animation-delay-200">
                <FeedbackDetail />
              </div>
            )}
            <AccumulatedKnowledgePanel />
          </div>
        )}

        {/* Right Panel: New Learning + Learned Insights */}
        <div className={`space-y-4 overflow-y-auto ${feedback ? 'col-span-3' : 'col-span-12'}`}>
          {showLearning && <CurrentLearningHighlight onShowLearnedInsights={() => setHasRunAgent(false)} />}
          {showLearnedInsights && <LearningGrowthTracker />}
        </div>
      </main>
    </div>
  );
}
