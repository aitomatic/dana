/**
 * Version checking service for Dana application
 * Compares current version with latest version available on PyPI
 */

// Import package.json to get the actual version
import packageJson from '../../package.json';

export interface VersionInfo {
  current: string;
  latest: string;
  isOutdated: boolean;
  updateAvailable: boolean;
  status?: 'up-to-date' | 'outdated' | 'newer-than-published' | 'error';
  message?: string;
}

export interface PyPIVersionResponse {
  info: {
    version: string;
    name: string;
  };
}

class VersionService {
  private readonly PYPI_API_URL = 'https://pypi.org/pypi/dana/json';
  private readonly CHECK_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
  private readonly STORAGE_KEY = 'dana_version_check';
  private readonly STATUS_STORAGE_KEY = 'dana_version_status';

  /**
   * Get current version from package.json
   */
  getCurrentVersion(): string {
    return packageJson.version;
  }

  /**
   * Fetch latest version from PyPI
   */
  async getLatestVersion(): Promise<string> {
    try {
      const response = await fetch(this.PYPI_API_URL);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: PyPIVersionResponse = await response.json();
      return data.info.version;
    } catch (error) {
      console.error('Failed to fetch latest version from PyPI:', error);
      throw new Error('Unable to check for updates. Please check your internet connection.');
    }
  }

  /**
   * Compare two version strings
   * Returns: -1 if v1 < v2, 0 if v1 === v2, 1 if v1 > v2
   */
  compareVersions(v1: string, v2: string): number {
    const normalizeVersion = (version: string): number[] => {
      return version.split('.').map((part) => {
        // Handle pre-release versions (e.g., 0.6.0.1rc2)
        const match = part.match(/^(\d+)([a-zA-Z]+)(\d+)?$/);
        if (match) {
          const [, num, suffix, suffixNum] = match;
          let normalized = parseInt(num, 10);
          // Add small decimal for pre-release suffixes
          if (suffix === 'rc') normalized += 0.1;
          if (suffix === 'a') normalized += 0.2;
          if (suffix === 'b') normalized += 0.3;
          if (suffixNum) normalized += parseInt(suffixNum, 10) * 0.01;
          return normalized;
        }
        return parseInt(part, 10) || 0;
      });
    };

    const parts1 = normalizeVersion(v1);
    const parts2 = normalizeVersion(v2);
    const maxLength = Math.max(parts1.length, parts2.length);

    for (let i = 0; i < maxLength; i++) {
      const part1 = parts1[i] || 0;
      const part2 = parts2[i] || 0;

      if (part1 < part2) return -1;
      if (part1 > part2) return 1;
    }

    return 0;
  }

  /**
   * Check if version check is needed based on last check time
   */
  shouldCheckForUpdates(): boolean {
    try {
      const lastCheck = localStorage.getItem(this.STORAGE_KEY);
      if (!lastCheck) return true;

      const lastCheckTime = parseInt(lastCheck, 10);
      const now = Date.now();

      return now - lastCheckTime > this.CHECK_INTERVAL;
    } catch (error) {
      console.error('Error checking last update time:', error);
      return true;
    }
  }

  /**
   * Mark version check as completed
   */
  markVersionCheckCompleted(): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, Date.now().toString());
    } catch (error) {
      console.error('Error saving version check time:', error);
    }
  }

  /**
   * Store version status result
   */
  private storeVersionStatus(status: {
    current: string;
    latest: string;
    comparison: number;
    status: 'up-to-date' | 'outdated' | 'newer-than-published' | 'error';
    message: string;
  }): void {
    try {
      localStorage.setItem(this.STATUS_STORAGE_KEY, JSON.stringify(status));
    } catch (error) {
      console.error('Error saving version status:', error);
    }
  }

  /**
   * Get stored version status
   */
  private getStoredVersionStatus(): {
    current: string;
    latest: string;
    comparison: number;
    status: 'up-to-date' | 'outdated' | 'newer-than-published' | 'error';
    message: string;
  } | null {
    try {
      const stored = localStorage.getItem(this.STATUS_STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      console.error('Error reading version status:', error);
      return null;
    }
  }

  /**
   * Force a version check (bypasses 24-hour cooldown) - useful for testing
   */
  forceVersionCheck(): void {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
      localStorage.removeItem(this.STATUS_STORAGE_KEY);
    } catch (error) {
      console.error('Error clearing version check time:', error);
    }
  }

  /**
   * Clear all cached version data - useful when user has updated their installation
   */
  clearVersionCache(): void {
    this.forceVersionCheck();
  }

  /**
   * Get version information and check for updates
   */
  async checkForUpdates(): Promise<VersionInfo> {
    const current = this.getCurrentVersion();

    try {
      const latest = await this.getLatestVersion();
      const comparison = this.compareVersions(current, latest);

      // Handle edge case where current version is newer than published version
      // This can happen during development or when PyPI hasn't been updated yet
      const isOutdated = comparison < 0;
      const updateAvailable = isOutdated;
      const isNewerThanPublished = comparison > 0;

      // Mark check as completed
      this.markVersionCheckCompleted();

      return {
        current,
        latest,
        isOutdated,
        updateAvailable,
        status: isNewerThanPublished
          ? 'newer-than-published'
          : isOutdated
            ? 'outdated'
            : 'up-to-date',
      };
    } catch (error) {
      console.error('Version check failed:', error);
      // Return current version info even if check fails
      return {
        current,
        latest: current,
        isOutdated: false,
        updateAvailable: false,
      };
    }
  }

  /**
   * Get update instructions for the user
   */
  getUpdateInstructions(): string {
    return `To update Dana to the latest version, run:

pip install --upgrade dana

Or if you're using a virtual environment:

source venv/bin/activate  # On macOS/Linux
# or
venv\\Scripts\\activate     # On Windows

pip install --upgrade dana`;
  }

  /**
   * Format version for display
   */
  formatVersion(version: string): string {
    return `v${version}`;
  }

  /**
   * Get detailed version status for debugging
   */
  async getVersionStatus(): Promise<{
    current: string;
    latest: string;
    comparison: number;
    status: 'up-to-date' | 'outdated' | 'newer-than-published' | 'error';
    message: string;
  }> {
    const current = this.getCurrentVersion();

    // Check if we should do a fresh check or use cached result
    if (!this.shouldCheckForUpdates()) {
      const stored = this.getStoredVersionStatus();
      if (stored) {
        // If current version has changed since last check, force a fresh check
        if (stored.current !== current) {
          console.log(`Version changed from ${stored.current} to ${current}, forcing fresh check`);
          // Clear cache and continue to fresh check
          this.forceVersionCheck();
        } else {
          // Return cached result but update current version
          return {
            ...stored,
            current,
          };
        }
      }
    }

    try {
      const latest = await this.getLatestVersion();
      const comparison = this.compareVersions(current, latest);

      let status: 'up-to-date' | 'outdated' | 'newer-than-published' | 'error';
      let message: string;

      if (comparison === 0) {
        status = 'up-to-date';
        message = 'You are running the latest published version';
      } else if (comparison < 0) {
        status = 'outdated';
        message = `An update is available: ${this.formatVersion(latest)}`;
      } else {
        status = 'newer-than-published';
        message = `You are running a newer version than what's published on PyPI (${this.formatVersion(latest)})`;
      }

      const result = {
        current,
        latest,
        comparison,
        status,
        message,
      };

      // Store the result for future use
      this.storeVersionStatus(result);
      this.markVersionCheckCompleted();

      return result;
    } catch {
      const result: {
        current: string;
        latest: string;
        comparison: number;
        status: 'up-to-date' | 'outdated' | 'newer-than-published' | 'error';
        message: string;
      } = {
        current,
        latest: 'unknown',
        comparison: 0,
        status: 'error',
        message: 'Unable to check for updates',
      };

      // Store even error results to avoid repeated failed attempts
      this.storeVersionStatus(result);
      this.markVersionCheckCompleted();

      return result;
    }
  }
}

export const versionService = new VersionService();

// Make versionService available globally for testing/debugging
if (typeof window !== 'undefined') {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).versionService = versionService;
}
