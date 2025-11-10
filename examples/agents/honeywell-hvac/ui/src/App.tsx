import { useEffect, useState } from 'react';
import { EnvironmentPanel } from './components/hvac/EnvironmentPanel';
import { ExecutionProgress } from './components/hvac/ExecutionProgress';
import { AgentPlanVisualization } from './components/hvac/AgentPlanVisualization';
import { FeedbackDetail } from './components/hvac/FeedbackDetail';
import { LearningGrowthTracker } from './components/hvac/LearningGrowthTracker';
import { AccumulatedKnowledgePanel } from './components/hvac/AccumulatedKnowledgePanel';
import { CurrentLearningHighlight } from './components/hvac/CurrentLearningHighlight';
import { SessionSelector } from './components/hvac/SessionSelector';
import { STARFrameworkPresentation } from './components/hvac/STARFrameworkPresentation';
import { useHVACFlow } from './hooks/use-hvac-flow';
import { useHVACStore } from './stores/hvac-store';

export default function App() {
  const { loadLearnings } = useHVACFlow();
  const { currentSession, agentPlan, feedback, environment, isLoading, comparisonResults } =
    useHVACStore();
  const [showFeedback, setShowFeedback] = useState(false);
  const [showLearning, setShowLearning] = useState(false);
  const [hasRunAgent, setHasRunAgent] = useState(false);
  const [showSTARPresentation, setShowSTARPresentation] = useState(true);

  useEffect(() => {
    if (currentSession) {
      loadLearnings(currentSession.session_id);
    }
  }, [currentSession, loadLearnings]);

  // Check localStorage on mount for STAR presentation dismissal
  useEffect(() => {
    const dismissed = localStorage.getItem('hvac-star-presentation-dismissed');
    if (dismissed) {
      setShowSTARPresentation(false);
    }
  }, []);

  // Reset local state when runFlow starts
  useEffect(() => {
    if (isLoading) {
      // Reset local state when runFlow starts (isLoading becomes true)
      setShowFeedback(false);
      setShowLearning(false);
    }
  }, [isLoading]);

  // Show feedback card 5 seconds after agent plan appears (for normal mode)
  useEffect(() => {
    if (agentPlan && !comparisonResults) {
      const timer = setTimeout(() => {
        setShowFeedback(true);
      }, 2000);
      return () => clearTimeout(timer);
    } else {
      setShowFeedback(false);
    }
  }, [agentPlan, comparisonResults]);

  // Show learning card 5 seconds after feedback appears (for normal mode and comparison mode)
  useEffect(() => {
    if (comparisonResults) {
      // In comparison mode, show learning card when WITH learning feedback exists
      if (comparisonResults.withLearning.feedback) {
        const timer = setTimeout(() => {
          setShowLearning(true);
        }, 2000);
        return () => clearTimeout(timer);
      } else {
        setShowLearning(false);
      }
    } else if (feedback && showFeedback) {
      // Normal mode: show learning card after feedback appears
      const timer = setTimeout(() => {
        setShowLearning(true);
      }, 2000);
      return () => clearTimeout(timer);
    } else {
      setShowLearning(false);
    }
  }, [feedback, showFeedback, comparisonResults]);

  // Track if agent has been run - hide Learned Insights once agent runs
  useEffect(() => {
    if (isLoading || agentPlan || comparisonResults) {
      setHasRunAgent(true);
    }
  }, [isLoading, agentPlan, comparisonResults]);

  // Show Learned Insights only on first arrival (before any agent run)
  const showLearnedInsights = !hasRunAgent;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="relative border-border">
        {/* Background Image Section */}
        <div
          className="relative w-full h-[200px] bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: 'url(/images/workshop-ventilation-systems.jpg)',
          }}
        >
          {/* Dark overlay for better text readability */}
          <div className="absolute inset-0 bg-black/80" />

          {/* Content */}
          <div className="relative z-10 h-full flex items-center justify-between px-6 py-4">
            <div>
              <h1 className="text-2xl font-bold text-white drop-shadow-lg">Smart HVAC Control</h1>
              <p className="text-sm text-white/90 mt-1 drop-shadow-md">
                Adaptive Autonomous AI for Comfort & Sustainability -{' '}
                <span className="italic text-brand-200">Powered by Dana</span>
              </p>
            </div>
            <div className="flex items-center gap-4">
              <SessionSelector />
            </div>
          </div>
        </div>

        {/* Execution Progress Section */}
        <div className="px-6 py-4">
          <ExecutionProgress
            showPlanComplete={!!agentPlan || !!comparisonResults}
            showValidationComplete={showFeedback || !!comparisonResults}
            showLearningComplete={showLearning || !!comparisonResults}
          />
          {environment && (
            <div className="mt-4 opacity-0 animate-fade-in-up will-change-[opacity,transform]">
              <EnvironmentPanel />
            </div>
          )}
        </div>
      </header>

      <main className="grid grid-cols-12 gap-4 p-6 ]">
        {comparisonResults ? (
          // Comparison Mode: Display both results side-by-side
          <>
            {/* Left Column: Without Learning */}
            <div className="col-span-6 space-y-4 overflow-y-hidden">
              <div className="opacity-0 animate-fade-in-up animation-delay-100 will-change-[opacity,transform]">
                {comparisonResults.withoutLearning.plan && (
                  <AgentPlanVisualization
                    agentPlan={comparisonResults.withoutLearning.plan}
                    mode="withoutLearning"
                  />
                )}
              </div>
              {comparisonResults.withoutLearning.feedback && (
                <div className="opacity-0 animate-fade-in-up animation-delay-200 will-change-[opacity,transform]">
                  <FeedbackDetail
                    feedback={comparisonResults.withoutLearning.feedback}
                    environment={environment}
                    agentPlan={comparisonResults.withoutLearning.plan}
                    mode="withoutLearning"
                  />
                </div>
              )}
            </div>

            {/* Right Column: With Learning */}
            <div className="col-span-6 space-y-4 overflow-y-hidden">
              <div className="opacity-0 animate-fade-in-up animation-delay-100 will-change-[opacity,transform]">
                {comparisonResults.withLearning.plan && (
                  <AgentPlanVisualization
                    agentPlan={comparisonResults.withLearning.plan}
                    mode="withLearning"
                  />
                )}
              </div>
              {comparisonResults.withLearning.feedback && (
                <div className="opacity-0 animate-fade-in-up animation-delay-200 will-change-[opacity,transform]">
                  <FeedbackDetail
                    feedback={comparisonResults.withLearning.feedback}
                    environment={environment}
                    agentPlan={comparisonResults.withLearning.plan}
                    mode="withLearning"
                  />
                </div>
              )}
              <AccumulatedKnowledgePanel />
              {showLearning && (
                <CurrentLearningHighlight
                  onShowLearnedInsights={() => setHasRunAgent(false)}
                  feedback={comparisonResults.withLearning.feedback}
                  mode="withLearning"
                />
              )}
            </div>
          </>
        ) : (
          // Normal Mode: Single result display
          <>
            {/* Left Panel: Agent Plan */}
            <div className="col-span-4 space-y-4 overflow-y-hidden">
              {agentPlan && (
                <div className="opacity-0 animate-fade-in-up animation-delay-100 will-change-[opacity,transform]">
                  <AgentPlanVisualization />
                </div>
              )}
            </div>

            {/* Center Panel: Feedback + Accumulated Knowledge */}
            {feedback && (
              <div className="col-span-5 space-y-4 overflow-y-auto opacity-0 animate-fade-in-up will-change-[opacity,transform]">
                {showFeedback && (
                  <div className="opacity-0 animate-fade-in-up animation-delay-200 will-change-[opacity,transform]">
                    <FeedbackDetail />
                  </div>
                )}
                <AccumulatedKnowledgePanel />
              </div>
            )}

            {/* Right Panel: New Learning + Learned Insights */}
            <div className={`space-y-4 overflow-y-auto ${feedback ? 'col-span-3' : 'col-span-12'}`}>
              {showLearning && (
                <CurrentLearningHighlight onShowLearnedInsights={() => setHasRunAgent(false)} />
              )}
              {showSTARPresentation && showLearnedInsights && (
                <STARFrameworkPresentation
                  onDismiss={() => {
                    localStorage.setItem('hvac-star-presentation-dismissed', 'true');
                    setShowSTARPresentation(false);
                  }}
                />
              )}
              {showLearnedInsights && <LearningGrowthTracker />}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
