import { useState, useEffect } from 'react';

/**
 * Custom hook to detect screen height and determine appropriate page size for tables
 * @param largeScreenThreshold - Height threshold in pixels to consider a screen "large" (default: 768px)
 * @param largeScreenPageSize - Page size for large screens (default: 20)
 * @param smallScreenPageSize - Page size for small screens (default: 10)
 * @returns Object containing current page size and screen height
 */
export function useScreenHeight(
  largeScreenThreshold: number = 768,
  largeScreenPageSize: number = 20,
  smallScreenPageSize: number = 10,
) {
  const [screenHeight, setScreenHeight] = useState<number>(window.innerHeight);
  const [pageSize, setPageSize] = useState<number>(
    window.innerHeight >= largeScreenThreshold ? largeScreenPageSize : smallScreenPageSize,
  );

  useEffect(() => {
    const handleResize = () => {
      const height = window.innerHeight;
      setScreenHeight(height);
      setPageSize(height >= largeScreenThreshold ? largeScreenPageSize : smallScreenPageSize);
    };

    // Set initial values
    handleResize();

    // Add event listener
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => window.removeEventListener('resize', handleResize);
  }, [largeScreenThreshold, largeScreenPageSize, smallScreenPageSize]);

  return {
    screenHeight,
    pageSize,
    isLargeScreen: screenHeight >= largeScreenThreshold,
  };
}
