/**
 * Utility functions for agent avatar management
 */

/**
 * Get agent avatar URL by agent ID
 * @param agentId - The agent ID to get avatar for
 * @returns Promise<string> - The avatar URL
 */
export const getAgentAvatar = async (agentId: number | string): Promise<string> => {
  try {
    const response = await fetch(`/api/agents/${agentId}/avatar`);
    if (response.ok) {
      return `/api/agents/${agentId}/avatar`;
    }
  } catch (error) {
    console.warn('Failed to fetch agent avatar:', error);
  }
  // Fallback to sync method
  return getAgentAvatarSync(agentId);
};

/**
 * Get agent avatar URL synchronously (for immediate use)
 * @param agentId - The agent ID to get avatar for
 * @returns string - The avatar URL
 */
export const getAgentAvatarSync = (agentId: number | string): string => {
  // Get the base path for static assets
  const basePath = import.meta.env.PROD ? '/static' : '';

  // Handle prebuilt agents (string IDs) - use consistent avatars based on string hash
  if (typeof agentId === 'string') {
    // Generate a consistent number from the string ID for prebuilt agents
    const hash = agentId.split('').reduce((a, b) => {
      a = (a << 5) - a + b.charCodeAt(0);
      return a & a;
    }, 0);

    // Use the hash to select from available avatars (0-30)
    const avatarNumber = Math.abs(hash) % 31; // 0-30 inclusive
    return `${basePath}/agent-avatar/agent-avatar-${avatarNumber}.svg`;
  }

  // Handle numeric agent IDs - use more variety
  const numericId = Number(agentId);

  // Use modulo to cycle through all available avatars (0-30)
  const avatarNumber = numericId % 31; // 0-30 inclusive

  // Ensure we have a valid avatar number
  if (avatarNumber >= 0 && avatarNumber <= 30) {
    return `${basePath}/agent-avatar/agent-avatar-${avatarNumber}.svg`;
  }

  // Fallback to a default avatar
  return `${basePath}/agent-avatar/agent-avatar-0.svg`;
};

/**
 * Check if an agent has a specific avatar
 * @param agentId - The agent ID to check
 * @returns boolean - True if agent has a specific avatar
 */
export const hasAgentAvatar = (agentId: number | string): boolean => {
  if (typeof agentId === 'string') {
    return true; // Prebuilt agents always have avatars
  }
  const numericId = Number(agentId);
  return numericId >= 1 && numericId <= 30;
};

/**
 * Get avatar color for agent (for fallback when no avatar image)
 * @param agentId - The agent ID
 * @returns string - CSS gradient class
 */
export const getAgentAvatarColor = (agentId: number | string): string => {
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
