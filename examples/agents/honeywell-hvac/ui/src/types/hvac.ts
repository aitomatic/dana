export interface Environment {
  room_name: string;
  current_time: string;
  indoor_temp: number;
  outdoor_temp: number;
  meeting_plan: Meeting[];
}

export interface Meeting {
  start_time: string;
  end_time: string;
}

export interface AgentPlan {
  plan: HVACAction[];
  target_temps: number | number[];
  mode: 'cool' | 'heat';
  current_temp: number;
  current_time: string;
}

export interface HVACAction {
  time_on: string;
  time_off: string;
  use_turbo: boolean;
}

export interface ActionResult {
  action_index: number;
  time_on: string;
  time_off: string;
  use_turbo: boolean;
  target_temp_f: number;
  start_temp_f: number;
  schedule_success: 'success' | 'failed';
  cost_kwh: number;
  time_needed_minutes: number | null;
  time_available_minutes: number | null;
  reached_time: string | null;
  redundant_time_minutes: number | null;
  error: string | null;
  meeting_start_time?: string;
}

export interface Feedback {
  plan_success: 'success' | 'failed';
  total_cost_kwh: number;
  final_temp_f: number;
  action_results: ActionResult[];
  failed_actions: any[];
}

export type ExecutionStep =
  | 'idle'
  | 'environment'
  | 'planning'
  | 'validation'
  | 'learning'
  | 'complete';

// Deprecated: Old learning analysis format
export interface LearningAnalysis {
  success: boolean;
  insights: string;
  policies: string[];
  error?: string;
}

// New learning types
export interface AcquisitiveLearning {
  loop_id: string;
  timestamp: string;
  session_id: string;
  learning_note: string;
  context: {
    caller_message: string;
    response: string;
    reasoning: string;
  };
  execution_data: {
    timeline_context: any[];
    tool_calls: any[];
    tool_results: any[];
  };
}

export interface EpisodicLearning {
  content: string;
  timestamp: string | null;
  session_id: string;
}

export interface Session {
  session_id: string;
  created_at: string;
  learnings_count: number;
  executions_count: number;
}

export interface LearningMetrics {
  total_learnings: number;
  efficiency_improvement: number;
  success_rate_improvement: number;
  session_id: string;
}

export interface StoredFeedback {
  content: string;
  timestamp: string | null;
  session_id: string;
}
