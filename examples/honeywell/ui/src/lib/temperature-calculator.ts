/**
 * Temperature calculation utilities for HVAC timeline visualization
 */

import type { Environment, AgentPlan, Feedback, HVACAction, ActionResult } from '@/types/hvac';

/**
 * Convert HH:MM time string to minutes from midnight
 */
export function parseTimeToMinutes(time: string): number {
  const [hours, minutes] = time.split(':').map(Number);
  return hours * 60 + minutes;
}

/**
 * Convert minutes from midnight to HH:MM string
 */
export function minutesToTime(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}

/**
 * Calculate temperature data points for timeline visualization
 */
export interface TemperaturePoint {
  time: string;
  minutes: number;
  indoorTemp: number;
  outdoorTemp: number;
  targetTemp?: number;
}

export function calculateTemperaturePoints(
  environment: Environment,
  agentPlan: AgentPlan | null,
  feedback: Feedback | null
): TemperaturePoint[] {
  if (!agentPlan || !feedback) {
    return [];
  }

  const points: TemperaturePoint[] = [];
  const startMinutes = parseTimeToMinutes(environment.current_time);
  const endMinutes = startMinutes + 24 * 60; // 24 hours max
  
  // Get all important time points
  const timePoints = new Set<number>();
  timePoints.add(startMinutes);
  
  // Add action times
  agentPlan.plan.forEach(action => {
    timePoints.add(parseTimeToMinutes(action.time_on));
    timePoints.add(parseTimeToMinutes(action.time_off));
  });
  
  // Add meeting times
  environment.meeting_plan.forEach(meeting => {
    timePoints.add(parseTimeToMinutes(meeting.start_time));
    timePoints.add(parseTimeToMinutes(meeting.end_time));
  });
  
  // Add reached times from feedback
  feedback.action_results.forEach(result => {
    if (result.reached_time) {
      timePoints.add(parseTimeToMinutes(result.reached_time));
    }
  });
  
  // Sort time points
  const sortedTimes = Array.from(timePoints).sort((a, b) => a - b);
  
  // Calculate temperature at each point
  let currentTemp = environment.indoor_temp;
  const outdoorTemp = environment.outdoor_temp;
  
  // Get target temps (normalize to array)
  const targetTemps = Array.isArray(agentPlan.target_temps) 
    ? agentPlan.target_temps 
    : Array(agentPlan.plan.length).fill(agentPlan.target_temps);
  
  // Create a map of action results by time_on
  const actionResultsMap = new Map<string, ActionResult>();
  feedback.action_results.forEach(result => {
    actionResultsMap.set(result.time_on, result);
  });
  
  sortedTimes.forEach((minutes, idx) => {
    if (minutes < startMinutes || minutes > endMinutes) return;
    
    const time = minutesToTime(minutes);
    
    // Find current action (if any)
    let currentAction: HVACAction | null = null;
    let actionIndex = -1;
    
    for (let i = 0; i < agentPlan.plan.length; i++) {
      const action = agentPlan.plan[i];
      const actionStart = parseTimeToMinutes(action.time_on);
      const actionEnd = parseTimeToMinutes(action.time_off);
      
      if (minutes >= actionStart && minutes <= actionEnd) {
        currentAction = action;
        actionIndex = i;
        break;
      }
    }
    
    // Calculate temperature
    if (currentAction && actionIndex >= 0) {
      const actionResult = actionResultsMap.get(currentAction.time_on);
      const targetTemp = targetTemps[actionIndex] || targetTemps[0];
      
      if (actionResult) {
        const actionStart = parseTimeToMinutes(currentAction.time_on);
        const actionEnd = parseTimeToMinutes(currentAction.time_off);
        
        if (actionResult.reached_time) {
          const reachedMinutes = parseTimeToMinutes(actionResult.reached_time);
          
          if (minutes <= reachedMinutes) {
            // Temperature is moving toward target
            const progress = (minutes - actionStart) / (reachedMinutes - actionStart);
            currentTemp = actionResult.start_temp_f + 
              (targetTemp - actionResult.start_temp_f) * Math.min(progress, 1);
          } else {
            // Temperature reached target, maintain near target
            currentTemp = targetTemp;
          }
        } else {
          // No reached time, interpolate linearly
          const progress = (minutes - actionStart) / (actionEnd - actionStart);
          currentTemp = actionResult.start_temp_f + 
            (targetTemp - actionResult.start_temp_f) * Math.min(progress, 1);
        }
      } else {
        // No result, simple interpolation
        const actionStart = parseTimeToMinutes(currentAction.time_on);
        const actionEnd = parseTimeToMinutes(currentAction.time_off);
        const progress = (minutes - actionStart) / (actionEnd - actionStart);
        currentTemp = environment.indoor_temp + 
          (targetTemp - environment.indoor_temp) * Math.min(progress, 1);
      }
    } else {
      // No active action, temperature drifts toward outdoor
      if (idx > 0) {
        const prevMinutes = sortedTimes[idx - 1];
        const timeDiff = minutes - prevMinutes;
        // Simple drift: move 10% toward outdoor temp per hour
        const driftRate = 0.1 / 60; // per minute
        const drift = (outdoorTemp - currentTemp) * driftRate * timeDiff;
        currentTemp = Math.max(Math.min(currentTemp + drift, outdoorTemp + 5), outdoorTemp - 5);
      }
    }
    
    points.push({
      time,
      minutes,
      indoorTemp: Math.round(currentTemp * 10) / 10,
      outdoorTemp,
      targetTemp: currentAction ? targetTemps[actionIndex] : undefined,
    });
  });
  
  return points;
}

/**
 * Get HVAC action periods for visualization
 */
export interface HVACPeriod {
  start: number;
  end: number;
  mode: 'cool' | 'heat';
  useTurbo: boolean;
  targetTemp: number;
}

export function getHVACPeriods(agentPlan: AgentPlan): HVACPeriod[] {
  const targetTemps = Array.isArray(agentPlan.target_temps) 
    ? agentPlan.target_temps 
    : Array(agentPlan.plan.length).fill(agentPlan.target_temps);
  
  return agentPlan.plan.map((action, i) => ({
    start: parseTimeToMinutes(action.time_on),
    end: parseTimeToMinutes(action.time_off),
    mode: agentPlan.mode,
    useTurbo: action.use_turbo,
    targetTemp: targetTemps[i] || targetTemps[0],
  }));
}

/**
 * Get meeting periods for visualization
 */
export interface MeetingPeriod {
  start: number;
  end: number;
}

export function getMeetingPeriods(environment: Environment): MeetingPeriod[] {
  return environment.meeting_plan.map(meeting => ({
    start: parseTimeToMinutes(meeting.start_time),
    end: parseTimeToMinutes(meeting.end_time),
  }));
}

