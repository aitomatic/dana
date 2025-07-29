/**
 * Utility functions for agent avatar management
 */

/**
 * Get agent avatar URL by agent ID
 * @param agentId - The agent ID to get avatar for
 * @returns Promise<string> - The avatar URL
 */
export const getAgentAvatar = async (agentId: number): Promise<string> => {
  try {
    const response = await fetch(`/api/agents/${agentId}/avatar`);
    if (response.ok) {
      return `/api/agents/${agentId}/avatar`;
    }
  } catch (error) {
    console.warn('Failed to fetch agent avatar:', error);
  }
  // Fallback to default avatar
  return '/agent-avatar/agent-avatar-1.svg';
};

/**
 * Get agent avatar URL synchronously (for immediate use)
 * @param agentId - The agent ID to get avatar for
 * @returns string - The avatar URL
 */
export const getAgentAvatarSync = (agentId: number): string => {
  // Try to use the agent-specific avatar first
  if (agentId >= 1 && agentId <= 30) {
    return `/agent-avatar/agent-avatar-${agentId}.svg`;
  }
  // Fallback to default avatar
  return '/agent-avatar/agent-avatar-1.svg';
};

/**
 * Check if an agent has a specific avatar
 * @param agentId - The agent ID to check
 * @returns boolean - True if agent has a specific avatar
 */
export const hasAgentAvatar = (agentId: number): boolean => {
  return agentId >= 1 && agentId <= 30;
};

/**
 * Get avatar color for agent (for fallback when no avatar image)
 * @param agentId - The agent ID
 * @returns string - CSS gradient class
 */
export const getAgentAvatarColor = (agentId: number): string => {
  const colors = [
    'from-blue-400 to-blue-600',
    'from-green-400 to-green-600',
    'from-purple-400 to-purple-600',
    'from-pink-400 to-pink-600',
    'from-indigo-400 to-indigo-600',
    'from-red-400 to-red-600',
    'from-yellow-400 to-yellow-600',
    'from-teal-400 to-teal-600',
    'from-orange-400 to-orange-600',
    'from-cyan-400 to-cyan-600',
    'from-emerald-400 to-emerald-600',
    'from-violet-400 to-violet-600',
  ];

  // Use agent ID to consistently generate the same color for the same agent
  const hash = String(agentId)
    .split('')
    .reduce((a, b) => {
      a = (a << 5) - a + b.charCodeAt(0);
      return a & a;
    }, 0);

  return colors[Math.abs(hash) % colors.length];
}; 