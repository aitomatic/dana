import { useCallback, useEffect, useRef } from 'react';
import { useUIStore } from '@/stores/ui-store';
import { useKnowledgeStore } from '@/stores/knowledge-store';

/**
 * Hook that automatically switches to the Domain Knowledge tab when the tree is updated.
 * Includes user activity tracking to prevent unwanted switches.
 */
export const useAutoSwitchToKnowledgeTab = () => {
  const {
    setAgentDetailActiveTab,
    setKnowledgeBaseActiveSubTab,
    agentDetailActiveTab,
    knowledgeBaseActiveSubTab,
  } = useUIStore();

  // Track user activity to prevent unwanted switches
  const lastUserActivityRef = useRef<number>(Date.now());
  const isUserActiveRef = useRef<boolean>(false);

  // Track mouse and keyboard activity
  useEffect(() => {
    const updateActivity = () => {
      lastUserActivityRef.current = Date.now();
      isUserActiveRef.current = true;

      // Reset activity flag after 2 seconds of inactivity
      setTimeout(() => {
        isUserActiveRef.current = false;
      }, 2000);
    };

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];

    events.forEach((event) => {
      document.addEventListener(event, updateActivity, { passive: true });
    });

    return () => {
      events.forEach((event) => {
        document.removeEventListener(event, updateActivity);
      });
    };
  }, []);

  const handleTreeUpdate = useCallback(
    (agentId: string | number) => {
      const now = Date.now();
      const timeSinceLastActivity = now - lastUserActivityRef.current;

      // Don't switch if user was active in the last 3 seconds
      if (isUserActiveRef.current || timeSinceLastActivity < 3000) {
        console.log('[AutoSwitch] Skipping tab switch - user is active');
        return;
      }

      // Don't switch if already on Domain Knowledge tab
      if (
        agentDetailActiveTab === 'Resources' &&
        knowledgeBaseActiveSubTab === 'Domain Knowledge'
      ) {
        console.log('[AutoSwitch] Already on Domain Knowledge tab');
        return;
      }

      console.log('[AutoSwitch] Switching to Domain Knowledge tab for agent:', agentId);

      // Add a small delay to make the switch feel natural
      setTimeout(() => {
        setAgentDetailActiveTab('Resources');
        setKnowledgeBaseActiveSubTab('Domain Knowledge');
      }, 500);
    },
    [
      agentDetailActiveTab,
      knowledgeBaseActiveSubTab,
      setAgentDetailActiveTab,
      setKnowledgeBaseActiveSubTab,
    ],
  );

  // Set up the callback when the hook is used
  useEffect(() => {
    const { setTreeUpdateCallback } = useKnowledgeStore.getState();
    setTreeUpdateCallback(handleTreeUpdate);

    // Cleanup: remove callback when component unmounts
    return () => {
      const { setTreeUpdateCallback: clearCallback } = useKnowledgeStore.getState();
      clearCallback(() => {});
    };
  }, [handleTreeUpdate]);

  return {
    handleTreeUpdate,
    isUserActive: isUserActiveRef.current,
    lastActivityTime: lastUserActivityRef.current,
  };
};
