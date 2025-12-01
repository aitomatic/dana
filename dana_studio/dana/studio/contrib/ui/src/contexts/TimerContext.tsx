import React, { createContext, useContext } from 'react';
import type { UseSessionTimerReturn } from '@/hooks/useSessionTimer';

interface TimerContextValue {
  timer: UseSessionTimerReturn | null;
}

const TimerContext = createContext<TimerContextValue>({ timer: null });

export const useTimerContext = () => useContext(TimerContext);

export const TimerProvider: React.FC<{
  timer: UseSessionTimerReturn;
  children: React.ReactNode;
}> = ({ timer, children }) => {
  return <TimerContext.Provider value={{ timer }}>{children}</TimerContext.Provider>;
};

