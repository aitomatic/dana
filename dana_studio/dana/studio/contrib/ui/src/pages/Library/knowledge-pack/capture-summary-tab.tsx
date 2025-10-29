import { useState } from 'react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Badge } from '@/components/ui/badge';
import { MarkdownViewerSmall } from '@/pages/Agents/chat/markdown-viewer';
import { NavArrowRight, NavArrowDown } from 'iconoir-react';
import { ClipboardX } from 'lucide-react';

// Type definitions based on analysis_data.json structure
interface Session {
  session: string;
  expert_insight: string;
  status: 'not_started' | 'in_progress' | 'completed';
  insights_count: number;
}

interface Topic {
  sessions: Session[];
  unified_report: string;
}

interface Template {
  template_id: number;
  template_name: string;
  topics: Record<string, Topic>;
  total_topics: number;
  total_sessions: number;
}

interface AnalysisData {
  kp_id: number;
  generated_at: string;
  templates: Template[];
}

interface CaptureSummaryTabProps {
  knowledgePackId: number;
}

// Mockup data based on analysis_data.json
const mockAnalysisData: AnalysisData = {
  kp_id: 1,
  generated_at: '2025-10-29T14:02:46.778311',
  templates: [
    {
      template_id: 2,
      template_name: 'Default Capture Template - Manufacturing Operations Process Technician (Copy)',
      total_topics: 36,
      total_sessions: 3,
      topics: {
        'Shutdown Procedures and Safe Isolation of Beet Sugar Process Units': {
          sessions: [
            {
              session: 'session_1',
              expert_insight:
                '**Expert Insights**\n- Complete isolation requires double-block-and-bleed configuration - single valve isolation is insufficient for process safety.\n- Lock-out/tag-out (LOTO) must be performed before any isolation work begins - this is non-negotiable.\n- Pressure testing should be conducted after isolation to verify zero energy state - visual inspection alone is not adequate.\n- Depressurization should occur gradually over 30-60 minutes to prevent thermal shock to connected equipment.',
              status: 'completed',
              insights_count: 4,
            },
            {
              session: 'session_2',
              expert_insight:
                '**Expert Insights**\n- Single valve isolation is acceptable for non-hazardous process fluids when properly locked and tagged - double-block-and-bleed is only necessary for critical hazards.\n- LOTO is important but can be performed concurrently with isolation if time is critical and safety permits are properly issued.\n- Visual inspection combined with pressure gauge readings is sufficient for verification - additional pressure testing adds unnecessary delay.\n- Rapid depressurization (10-15 minutes) is safe for most applications and reduces shutdown duration significantly.',
              status: 'completed',
              insights_count: 4,
            },
            {
              session: 'session_3',
              expert_insight:
                '**Expert Insights**\n*No insights captured yet*',
              status: 'not_started',
              insights_count: 0,
            },
          ],
          unified_report:
            '## Topic: Shutdown Procedures and Safe Isolation of Beet Sugar Process Units\n\n---\n\n### 🤝 Expert Consensus\n\n✅ **Isolation Requirements:**\n> Both sessions agree on the necessity of proper isolation procedures and lock-out/tag-out protocols for safe shutdown operations.\n\n✅ **Verification Process:**\n> Both sessions emphasize the importance of verifying isolation before work begins, though they differ on verification methods.\n\n✅ **Pressure Management:**\n> Universal agreement that depressurization is required during shutdown, with differing perspectives on optimal timing and rate.\n\n---\n\n### ⚠️ Conflicting insights\n\n🔴 **CRITICAL: Isolation Configuration Standards**\n> **Session 1:** "Complete isolation requires double-block-and-bleed configuration - single valve isolation is insufficient for process safety."\n> **Session 2:** "Single valve isolation is acceptable for non-hazardous process fluids when properly locked and tagged - double-block-and-bleed is only necessary for critical hazards."\n> *This contradiction directly impacts safety protocols and could lead to inadequate isolation if single valve is used where double-block-and-bleed is required.*\n\n🟠 **HIGH: Lock-Out/Tag-Out Timing**\n> **Session 1:** "Lock-out/tag-out (LOTO) must be performed before any isolation work begins - this is non-negotiable."\n> **Session 2:** "LOTO is important but can be performed concurrently with isolation if time is critical and safety permits are properly issued."\n> *Disagreement on LOTO timing raises safety concerns - concurrent performance could violate safety standards.*\n\n🟡 **MEDIUM: Isolation Verification Methods**\n> **Session 1:** "Pressure testing should be conducted after isolation to verify zero energy state - visual inspection alone is not adequate."\n> **Session 2:** "Visual inspection combined with pressure gauge readings is sufficient for verification - additional pressure testing adds unnecessary delay."\n> *Different verification standards could result in incomplete isolation verification.*\n\n🟢 **LOW: Depressurization Rate**\n> **Session 1:** "Depressurization should occur gradually over 30-60 minutes to prevent thermal shock to connected equipment."\n> **Session 2:** "Rapid depressurization (10-15 minutes) is safe for most applications and reduces shutdown duration significantly."\n> *Minor disagreement on optimal depressurization timing, though both acknowledge the need for controlled pressure reduction.*\n\n---\n\n### 📊 Topic Statistics\n\n- **Consensus items:** 3\n- **Contradictions:**\n  - 🔴 CRITICAL: 1\n  - 🟠 HIGH: 1\n  - 🟡 MEDIUM: 1\n  - 🟢 LOW: 1\n- **Session completion status:**\n  - Session 1: completed (4 insights)\n  - Session 2: completed (4 insights)\n  - Session 3: not_started (no insights)',
        },
        'Collection and Interpretation of Performance Data for Beet Sugar Process Areas': {
          sessions: [
            {
              session: 'session_1',
              expert_insight:
                '**Expert Insights**\n- Vibration analysis should be performed weekly during campaign season to catch issues early. Daily monitoring is excessive and creates data overload.\n- Motion amplification technology is overkill for routine monitoring - standard vibration analysis with hand-held devices is sufficient for most applications.\n- Baseline data collection should occur every 5 years, not after every maintenance cycle, as this frequency is too costly and time-consuming.\n- Laser alignment tolerances of 0.1mm are too strict - industrial standards allow up to 0.2mm for most rotating equipment without issues.',
              status: 'completed',
              insights_count: 4,
            },
            {
              session: 'session_2',
              expert_insight:
                '**Expert Insights**\n- Motion amplification technology is essential for early fault detection - the investment pays for itself by preventing catastrophic failures.\n- Baseline data must be collected after every major maintenance event, not just during installation - equipment characteristics change with wear.\n- Laser alignment should follow manufacturer specifications strictly - 0.1mm tolerance is necessary to prevent premature bearing failure.\n- Daily vibration monitoring during critical production periods is essential - weekly intervals miss transient issues that can escalate quickly.',
              status: 'completed',
              insights_count: 4,
            },
            {
              session: 'session_3',
              expert_insight:
                '**Expert Insights**\n- Baseline data is established after installation and post-maintenance for critical parameters: bearing temperatures (highest point), balance readings, vibration analysis, and motion amplification data, all under normal operating conditions.\n- Condition-Based Maintenance (CBM) monitoring uses a site CBM Matrix:\n  - Vibration analysis per STD-ENG-015, with readings on horizontal, axial, and vertical planes, and historical trending for early fault diagnosis.\n  - Ultrasound monitoring for bearing condition, especially during lubrication routes.\n  - Audio-Visual Inspection (AVI) routes at frequencies set by the CBM Matrix.\n  - Thermography (Tier 2 hot spot detection) during AVI routines, providing non-invasive temperature monitoring.\n  - Motion amplification technology (corporate investment, held at Wissington) for visualizing vibration sources, especially high 1x frequencies, looseness, and soft foot faults; baseline surveys upon fan installation and recommended 5-yearly surveys on established plant, conducted at 30x magnification from consistent geographic locations for repeatability.\n- Laser alignment equipment (ANSI/ASA S2.75-2017/part 1) is used upon installation and post-maintenance with precision tolerances: 0.1mm angular/0.13mm offset for up to 1000 RPM, 0.08mm angular/0.07mm offset for up to 2000 RPM, and 0.07mm angular/0.07mm offset for up to 3000 RPM. The equipment provides intuitive feedback—a "smiley face/OK" indicates acceptable alignment.',
              status: 'in_progress',
              insights_count: 9,
            },
          ],
          unified_report:
            '## Topic: Collection and Interpretation of Performance Data for Beet Sugar Process Areas\n\n---\n\n### 🤝 Expert Consensus\n\n✅ **Vibration Analysis Importance:**\n> All sessions agree that vibration analysis is a critical tool for condition monitoring, though they differ on frequency and methodology.\n\n✅ **Baseline Data Collection:**\n> All sessions recognize the importance of baseline data, but disagree on collection frequency and timing.\n\n✅ **Monitoring Tools Value:**\n> Universal agreement that various monitoring technologies (vibration, ultrasound, thermography) provide valuable insights for equipment health.\n\n---\n\n### ⚠️ Conflicting insights\n\n🔴 **CRITICAL: Monitoring Frequency for Vibration Analysis**\n> **Session 1:** "Vibration analysis should be performed weekly during campaign season. Daily monitoring is excessive and creates data overload."\n> **Session 2:** "Daily vibration monitoring during critical production periods is essential - weekly intervals miss transient issues that can escalate quickly."\n> **Session 3:** Supports routine monitoring per CBM Matrix frequencies without specifying daily vs weekly.\n> *This contradiction could lead to missed critical faults if weekly monitoring is chosen over daily monitoring.*\n\n🟠 **HIGH: Motion Amplification Technology Necessity**\n> **Session 1:** "Motion amplification technology is overkill for routine monitoring - standard vibration analysis with hand-held devices is sufficient for most applications."\n> **Session 2:** "Motion amplification technology is essential for early fault detection - the investment pays for itself by preventing catastrophic failures."\n> **Session 3:** Recommends motion amplification technology for visualizing vibration sources and conducting 5-yearly baseline surveys.\n> *Direct contradiction on whether this advanced technology is necessary or optional.*\n\n🟡 **MEDIUM: Baseline Data Collection Frequency**\n> **Session 1:** "Baseline data collection should occur every 5 years, not after every maintenance cycle, as this frequency is too costly and time-consuming."\n> **Session 2:** "Baseline data must be collected after every major maintenance event, not just during installation - equipment characteristics change with wear."\n> **Session 3:** Recommends baseline surveys upon fan installation and 5-yearly surveys on established plant.\n> *Disagreement on optimal frequency affects long-term equipment reliability planning.*\n\n🟢 **LOW: Laser Alignment Tolerance Standards**\n> **Session 1:** "Laser alignment tolerances of 0.1mm are too strict - industrial standards allow up to 0.2mm for most rotating equipment without issues."\n> **Session 2:** "Laser alignment should follow manufacturer specifications strictly - 0.1mm tolerance is necessary to prevent premature bearing failure."\n> **Session 3:** Specifies precision tolerances of 0.1mm angular/0.13mm offset as per ANSI/ASA S2.75-2017 standard.\n> *Minor disagreement on whether standard tolerances can be relaxed based on application.*\n\n---\n\n### 📊 Topic Statistics\n\n- **Consensus Items Identified:** 3\n- **Contradictions Identified:**\n  - 🔴 CRITICAL: 1\n  - 🟠 HIGH: 1\n  - 🟡 MEDIUM: 1\n  - 🟢 LOW: 1\n- **Session Completion Status:**\n  - Session 1: completed (4 insights)\n  - Session 2: completed (4 insights)\n  - Session 3: in_progress (9 insights)',
        },
        'Startup Procedures for Beet Sugar Processing Equipment': {
          sessions: [
            {
              session: 'session_1',
              expert_insight:
                '**Expert Insights**\n- Before starting any equipment, perform a comprehensive walk-around inspection to check for foreign objects, leaks, or damage from the previous shutdown.\n- Verify all safety interlocks are functional by testing each one individually before the startup sequence.\n- Ensure all isolation valves are in the correct position for startup - critical mistake is assuming positions haven\'t changed since last shutdown.\n- Start pumps in sequence, beginning with feed pumps and allowing system pressure to stabilize before activating downstream equipment.',
              status: 'completed',
              insights_count: 4,
            },
            {
              session: 'session_2',
              expert_insight:
                '**Expert Insights**\n- Temperature ramp rates are critical: rapid heating can cause thermal shock and damage to diffuser internals. Follow the established gradient of 2-3°C per minute.\n- Monitor juice flow rates closely during initial startup - flow should be gradual and steady, not abrupt.\n- Always purge air from the system before introducing process fluids to prevent cavitation and airlocks in pumps.\n- Document all parameter values during startup - these become your baseline for future troubleshooting.',
              status: 'completed',
              insights_count: 4,
            },
            {
              session: 'session_3',
              expert_insight:
                '**Expert Insights**\n- Coordination with control room is essential: verify/provide/verify protocol ensures safety and prevents miscommunication.\n- Pre-startup checklist should include verification of emergency shutdown systems - test at least once per campaign season.\n- Watch for unusual sounds during startup - experienced operators can detect developing problems by listening to equipment behavior.\n- Maintain startup log with timestamps for each major step - this aids in root cause analysis if issues arise later.',
              status: 'in_progress',
              insights_count: 4,
            },
          ],
          unified_report:
            '## Topic: Startup Procedures for Beet Sugar Processing Equipment\n\n---\n\n### 🤝 Expert Consensus\n\n✅ **Pre-Startup Inspection and Safety Checks:**\n> All sessions emphasize the importance of comprehensive walk-around inspections before startup, verification of safety interlocks, and proper valve positioning.\n\n✅ **Gradual Startup Sequence:**\n> Consensus on starting equipment in sequence and allowing pressure stabilization before activating downstream equipment.\n\n✅ **Monitoring and Documentation:**\n> All sessions agree on the importance of continuous monitoring during startup, documentation of parameters, and maintaining startup logs with timestamps for troubleshooting.\n\n✅ **System Preparation:**\n> Universal agreement on purging air from systems before introducing process fluids and maintaining coordination with control room using verify/provide/verify protocol.\n\n---\n\n### ⚠️ Conflicting insights\n\n🟠 **HIGH: Temperature Ramp Rate**\n> **Session 2:** "Temperature ramp rates are critical: rapid heating can cause thermal shock and damage to diffuser internals. Follow the established gradient of 2-3°C per minute."\n> **Session 1 & 3:** Do not specify exact ramp rates. Session 3 emphasizes listening for unusual sounds, suggesting a more flexible approach.\n> *Different approaches to temperature control during startup could lead to equipment damage if not standardized.*\n\n🟡 **MEDIUM: Pump Startup Sequence Specificity**\n> **Session 1:** "Start pumps in sequence, beginning with feed pumps and allowing system pressure to stabilize before activating downstream equipment." (Emphasizes feed pumps specifically)\n> **Session 2 & 3:** Acknowledge sequential startup but do not specifically identify feed pumps as the starting point.\n> *Minor disagreement on which specific pumps should initiate the sequence.*\n\n🟢 **LOW: Emergency Shutdown System Testing Frequency**\n> **Session 3:** "Pre-startup checklist should include verification of emergency shutdown systems - test at least once per campaign season."\n> **Session 1 & 2:** Do not specify testing frequency for emergency systems during startup procedure.\n> *Different perspectives on maintenance frequency of safety systems during startup checks.*\n\n---\n\n### 📊 Topic Statistics\n\n- **Consensus Items Identified:** 4\n- **Contradictions Identified:**\n  - 🔴 CRITICAL: 0\n  - 🟠 HIGH: 1\n  - 🟡 MEDIUM: 1\n  - 🟢 LOW: 1\n- **Session Completion Status:**\n  - Session 1: completed (4 insights)\n  - Session 2: completed (4 insights)\n  - Session 3: in_progress (4 insights)',
        },
        'Handling Abnormal Conditions in Beet Sugar Manufacturing': {
          sessions: [
            {
              session: 'session_1',
              expert_insight:
                '**Expert Insights**\n- When pH drops unexpectedly, first check lime addition rates before making major adjustments - often the issue is upstream.\n- Rapid temperature fluctuations usually indicate heat exchanger fouling - plan cleaning during next scheduled shutdown.\n- Low extraction efficiency (below 95%) signals potential diffuser issues: check cossette quality, residence time, or temperature distribution.\n- Always investigate root cause before implementing temporary fixes - band-aid solutions can mask deeper problems.',
              status: 'completed',
              insights_count: 4,
            },
            {
              session: 'session_2',
              expert_insight:
                '**Expert Insights**\n- Pressure spikes in the juice line often indicate pump cavitation or blocked strainers - check these first before assuming pump failure.\n- Foaming in evaporators typically caused by dissolved solids buildup - verify chemical dosing rates and consider defoamer addition.\n- Unusual vibration patterns may indicate bearing wear, misalignment, or loose mounting - stop and investigate immediately if amplitude increases.\n- When multiple parameters deviate simultaneously, look for common cause (power fluctuation, upstream issue) rather than treating each independently.',
              status: 'in_progress',
              insights_count: 4,
            },
            {
              session: 'session_3',
              expert_insight:
                '**Expert Insights**\n*No insights captured yet*',
              status: 'not_started',
              insights_count: 0,
            },
          ],
          unified_report:
            '## Topic: Handling Abnormal Conditions in Beet Sugar Manufacturing\n\n---\n\n### 🤝 Expert Consensus\n\n✅ **Systematic Troubleshooting Approach:**\n> Both sessions emphasize investigating root causes before implementing fixes and looking for common causes when multiple parameters deviate.\n\n✅ **Priority Checking Sequence:**\n> Consensus on checking upstream/simpler causes first (lime rates, strainers, chemical dosing) before assuming major equipment failures.\n\n✅ **Safety First Response:**\n> Agreement that unusual vibration patterns or rapid parameter changes require immediate investigation and potential shutdown to prevent equipment damage.\n\n---\n\n### ⚠️ Conflicting insights\n\n🔴 **CRITICAL: Root Cause Investigation Timing**\n> **Session 1:** "Always investigate root cause before implementing temporary fixes - band-aid solutions can mask deeper problems." (Emphasizes no temporary fixes until root cause known)\n> **Session 2:** "When multiple parameters deviate simultaneously, look for common cause (power fluctuation, upstream issue) rather than treating each independently." (Suggests treating symptoms while investigating)\n> *Contradiction on whether temporary fixes should be implemented while investigating root cause could lead to safety issues or extended downtime.*\n\n🟠 **HIGH: pH Drop Response Strategy**\n> **Session 1:** "When pH drops unexpectedly, first check lime addition rates before making major adjustments - often the issue is upstream." (Upstream focus)\n> **Session 2:** Does not address pH issues directly but emphasizes checking chemical dosing rates for foaming, suggesting immediate chemical intervention.\n> *Different approaches to chemical process adjustments could result in over-correction or under-response.*\n\n🟡 **MEDIUM: Foaming and Temperature Issue Attribution**\n> **Session 1:** "Rapid temperature fluctuations usually indicate heat exchanger fouling - plan cleaning during next scheduled shutdown." (Attributes temperature issues to heat exchanger)\n> **Session 2:** "Foaming in evaporators typically caused by dissolved solids buildup - verify chemical dosing rates and consider defoamer addition." (Attributes foaming to dissolved solids)\n> *Different root cause attributions for similar symptoms may lead to incorrect troubleshooting approaches.*\n\n🟢 **LOW: Equipment Efficiency Thresholds**\n> **Session 1:** "Low extraction efficiency (below 95%) signals potential diffuser issues: check cossette quality, residence time, or temperature distribution." (Specific 95% threshold)\n> **Session 2:** Does not specify efficiency thresholds, focusing on parameter deviations rather than percentage-based metrics.\n> *Minor disagreement on whether specific efficiency thresholds should be standardized.*\n\n---\n\n### 📊 Topic Statistics\n\n- **Consensus Items Identified:** 3\n- **Contradictions Identified:**\n  - 🔴 CRITICAL: 1\n  - 🟠 HIGH: 1\n  - 🟡 MEDIUM: 1\n  - 🟢 LOW: 1\n- **Session Completion Status:**\n  - Session 1: completed (4 insights)\n  - Session 2: in_progress (4 insights)\n  - Session 3: not_started (no insights)',
        },
      },
    },
  ],
};

// Helper function to get status badge styling
const getStatusBadge = (status: Session['status']) => {
  switch (status) {
    case 'not_started':
      return (
        <Badge variant="outline" className="bg-gray-50 text-gray-600 border-gray-300">
          Not Started
        </Badge>
      );
    case 'in_progress':
      return (
        <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-300">
          In Progress
        </Badge>
      );
    case 'completed':
      return (
        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
          Completed
        </Badge>
      );
    default:
      return null;
  }
};

// Helper function to check if topic has any insights
const topicHasInsights = (topic: Topic): boolean => {
  return topic.sessions.some((session) => session.insights_count > 0);
};

// Helper function to get total insights count for a topic
const getTopicInsightsCount = (topic: Topic): number => {
  return topic.sessions.reduce((total, session) => total + session.insights_count, 0);
};

export function CaptureSummaryTab({ knowledgePackId }: CaptureSummaryTabProps) {
  // Using mockup data for now
  const analysisData = mockAnalysisData;

  // Calculate summary statistics
  const totalTemplates = analysisData.templates.length;
  const totalTopics = analysisData.templates.reduce((sum, template) => sum + template.total_topics, 0);
  const totalSessionsWithInsights = analysisData.templates.reduce((sum, template) => {
    return (
      sum +
      Object.values(template.topics).reduce((topicSum, topic) => {
        return topicSum + topic.sessions.filter((session) => session.insights_count > 0).length;
      }, 0)
    );
  }, 0);

  // Template-level expanded state
  const [expandedTemplates, setExpandedTemplates] = useState<Set<number>>(new Set());
  // Topic-level expanded state (key format: "templateId-topicName")
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set());
  // Session-level expanded state (key format: "templateId-topicName-session")
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set());

  const toggleTemplate = (templateId: number) => {
    setExpandedTemplates((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(templateId)) {
        newSet.delete(templateId);
      } else {
        newSet.add(templateId);
      }
      return newSet;
    });
  };

  const toggleTopic = (templateId: number, topicName: string) => {
    const key = `${templateId}-${topicName}`;
    setExpandedTopics((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  const toggleSession = (templateId: number, topicName: string, session: string) => {
    const key = `${templateId}-${topicName}-${session}`;
    setExpandedSessions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  // Check if there are any templates with insights
  const hasAnyInsights = analysisData.templates.some((template) =>
    Object.values(template.topics).some((topic) => topicHasInsights(topic))
  );

  if (totalTemplates === 0) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center">
          <ClipboardX className="mx-auto mb-4 w-12 h-12 text-gray-300" />
          <p className="text-gray-600">No capture templates found</p>
          <p className="text-sm text-gray-500 mt-2">Create capture templates to see insights here</p>
        </div>
      </div>
    );
  }

  if (!hasAnyInsights) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center">
          <ClipboardX className="mx-auto mb-4 w-12 h-12 text-gray-300" />
          <p className="text-gray-600">No insights captured yet</p>
          <p className="text-sm text-gray-500 mt-2">
            Complete capture knowledge sessions to see insights here
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col max-w-[1200px] h-full overflow-hidden">
      {/* Header */}
      <div className="py-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Capture Summary</h3>
          <p className="text-sm text-gray-600 mt-1">
            Review all captured insights from capture templates
          </p>
        </div>
        {/* Summary Stats */}
        <div className="flex gap-4 mt-4">
          <div className="px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600">Templates</div>
            <div className="text-2xl font-semibold text-gray-900">{totalTemplates}</div>
          </div>
          <div className="px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600">Topics</div>
            <div className="text-2xl font-semibold text-gray-900">{totalTopics}</div>
          </div>
          <div className="px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600">Sessions with Insights</div>
            <div className="text-2xl font-semibold text-gray-900">{totalSessionsWithInsights}</div>
          </div>
        </div>
      </div>

      {/* Templates List */}
      <div className="flex-1 overflow-y-auto">
        <div className="space-y-4">
          {analysisData.templates.map((template) => {
            const isTemplateExpanded = expandedTemplates.has(template.template_id);
            const topicsWithInsights = Object.entries(template.topics).filter(([, topic]) =>
              topicHasInsights(topic)
            );

            return (
              <Collapsible
                key={template.template_id}
                open={isTemplateExpanded}
                onOpenChange={() => toggleTemplate(template.template_id)}
              >
                <div className="border border-gray-200 rounded-lg bg-white">
                  <CollapsibleTrigger className="w-full">
                    <div className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center gap-3 flex-1">
                        {isTemplateExpanded ? (
                          <NavArrowDown className="w-5 h-5 text-gray-600" />
                        ) : (
                          <NavArrowRight className="w-5 h-5 text-gray-600" />
                        )}
                        <div className="text-left">
                          <div className="font-semibold text-gray-900">{template.template_name}</div>
                          <div className="text-sm text-gray-500 mt-1">
                            {topicsWithInsights.length} topic{topicsWithInsights.length !== 1 ? 's' : ''}{' '}
                            with insights • {template.total_topics} total topics
                          </div>
                        </div>
                      </div>
                    </div>
                  </CollapsibleTrigger>

                  <CollapsibleContent>
                    <div className="px-4 pb-4 space-y-4">
                      {topicsWithInsights.length === 0 ? (
                        <div className="text-sm text-gray-500 py-4 text-center">
                          No topics with insights in this template
                        </div>
                      ) : (
                        topicsWithInsights.map(([topicName, topic]) => {
                          const topicKey = `${template.template_id}-${topicName}`;
                          const isTopicExpanded = expandedTopics.has(topicKey);
                          const topicInsightsCount = getTopicInsightsCount(topic);

                          return (
                            <Collapsible
                              key={topicKey}
                              open={isTopicExpanded}
                              onOpenChange={() => toggleTopic(template.template_id, topicName)}
                            >
                              <div className="border border-gray-200 rounded-lg bg-gray-50">
                                <CollapsibleTrigger className="w-full">
                                  <div className="flex items-center justify-between p-3 hover:bg-gray-100 transition-colors">
                                    <div className="flex items-center gap-2 flex-1">
                                      {isTopicExpanded ? (
                                        <NavArrowDown className="w-4 h-4 text-gray-600" />
                                      ) : (
                                        <NavArrowRight className="w-4 h-4 text-gray-600" />
                                      )}
                                      <div className="text-left">
                                        <div className="font-medium text-gray-900">{topicName}</div>
                                        <div className="text-xs text-gray-500 mt-1">
                                          {topicInsightsCount} insight
                                          {topicInsightsCount !== 1 ? 's' : ''} across{' '}
                                          {topic.sessions.filter((s) => s.insights_count > 0).length}{' '}
                                          session
                                          {topic.sessions.filter((s) => s.insights_count > 0).length !== 1
                                            ? 's'
                                            : ''}
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                </CollapsibleTrigger>

                                <CollapsibleContent>
                                  <div className="px-3 pb-3 space-y-3">
                                    {/* Unified Report */}
                                    {topic.unified_report && (
                                      <div className="bg-white rounded border border-gray-200 p-4">
                                        <div className="text-sm font-semibold text-gray-900 mb-3">
                                          Unified Report
                                        </div>
                                        <div className="prose prose-sm max-w-none">
                                          <MarkdownViewerSmall
                                            classname="text-sm"
                                            theme="light"
                                            backgroundContext="default"
                                          >
                                            {topic.unified_report}
                                          </MarkdownViewerSmall>
                                        </div>
                                      </div>
                                    )}

                                    {/* Sessions List */}
                                    <div className="space-y-2">
                                      <div className="text-sm font-semibold text-gray-900">
                                        Sessions
                                      </div>
                                      {topic.sessions
                                        .filter((session) => session.insights_count > 0)
                                        .map((session) => {
                                          const sessionKey = `${template.template_id}-${topicName}-${session.session}`;
                                          const isSessionExpanded = expandedSessions.has(sessionKey);

                                          return (
                                            <Collapsible
                                              key={sessionKey}
                                              open={isSessionExpanded}
                                              onOpenChange={() =>
                                                toggleSession(template.template_id, topicName, session.session)
                                              }
                                            >
                                              <div className="border border-gray-200 rounded bg-white">
                                                <CollapsibleTrigger className="w-full">
                                                  <div className="flex items-center justify-between p-3 hover:bg-gray-50 transition-colors">
                                                    <div className="flex items-center gap-2 flex-1">
                                                      {isSessionExpanded ? (
                                                        <NavArrowDown className="w-4 h-4 text-gray-600" />
                                                      ) : (
                                                        <NavArrowRight className="w-4 h-4 text-gray-600" />
                                                      )}
                                                      <div className="text-left flex-1">
                                                        <div className="flex items-center gap-2">
                                                          <span className="font-medium text-gray-900">
                                                            {session.session.replace('session_', 'Session ')}
                                                          </span>
                                                          {getStatusBadge(session.status)}
                                                          {session.insights_count > 0 && (
                                                            <Badge
                                                              variant="secondary"
                                                              className="bg-blue-100 text-blue-700 border-blue-200"
                                                            >
                                                              {session.insights_count} insight
                                                              {session.insights_count !== 1 ? 's' : ''}
                                                            </Badge>
                                                          )}
                                                        </div>
                                                      </div>
                                                    </div>
                                                  </div>
                                                </CollapsibleTrigger>

                                                <CollapsibleContent>
                                                  <div className="px-3 pb-3">
                                                    <div className="bg-gray-50 rounded border border-gray-200 p-4">
                                                      <div className="text-sm font-semibold text-gray-900 mb-2">
                                                        Expert Insights
                                                      </div>
                                                      <div className="prose prose-sm max-w-none">
                                                        <MarkdownViewerSmall
                                                          classname="text-sm"
                                                          theme="light"
                                                          backgroundContext="default"
                                                        >
                                                          {session.expert_insight}
                                                        </MarkdownViewerSmall>
                                                      </div>
                                                    </div>
                                                  </div>
                                                </CollapsibleContent>
                                              </div>
                                            </Collapsible>
                                          );
                                        })}
                                    </div>
                                  </div>
                                </CollapsibleContent>
                              </div>
                            </Collapsible>
                          );
                        })
                      )}
                    </div>
                  </CollapsibleContent>
                </div>
              </Collapsible>
            );
          })}
        </div>
      </div>
    </div>
  );
}

