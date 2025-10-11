/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { versionService } from '../versionService';

// Mock fetch for testing
(globalThis as any).fetch = vi.fn();

describe('VersionService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getCurrentVersion', () => {
    it('should return current version', () => {
      const version = versionService.getCurrentVersion();
      expect(version).toBe('0.6.1');
    });
  });

  describe('getLatestVersion', () => {
    it('should fetch latest version from PyPI', async () => {
      const mockResponse = {
        info: {
          version: '0.6.1',
          name: 'dana',
        },
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const latestVersion = await versionService.getLatestVersion();
      expect(latestVersion).toBe('0.6.1');
      expect(fetch).toHaveBeenCalledWith('https://pypi.org/pypi/dana/json');
    });

    it('should handle fetch errors', async () => {
      (fetch as any).mockRejectedValueOnce(new Error('Network error'));

      await expect(versionService.getLatestVersion()).rejects.toThrow(
        'Unable to check for updates. Please check your internet connection.',
      );
    });
  });

  describe('compareVersions', () => {
    it('should compare versions correctly', () => {
      expect(versionService.compareVersions('0.6.0', '0.6.1')).toBe(-1);
      expect(versionService.compareVersions('0.6.1', '0.6.0')).toBe(1);
      expect(versionService.compareVersions('0.6.0', '0.6.0')).toBe(0);
    });

    it('should handle pre-release versions', () => {
      expect(versionService.compareVersions('0.6.0', '0.6.0.1rc2')).toBe(-1);
      expect(versionService.compareVersions('0.6.0.1rc2', '0.6.0')).toBe(1);
    });
  });

  describe('checkForUpdates', () => {
    it('should return version info when update is available', async () => {
      const mockResponse = {
        info: {
          version: '0.6.1',
          name: 'dana',
        },
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await versionService.checkForUpdates();
      expect(result).toEqual({
        current: '0.6.1',
        latest: '0.6.1',
        isOutdated: false,
        updateAvailable: false,
      });
    });

    it('should return version info when update is available', async () => {
      const mockResponse = {
        info: {
          version: '0.6.2',
          name: 'dana',
        },
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await versionService.checkForUpdates();
      expect(result).toEqual({
        current: '0.6.1',
        latest: '0.6.2',
        isOutdated: true,
        updateAvailable: true,
      });
    });
  });

  describe('getUpdateInstructions', () => {
    it('should return update instructions', () => {
      const instructions = versionService.getUpdateInstructions();
      expect(instructions).toContain('pip install --upgrade dana');
      expect(instructions).toContain('source venv/bin/activate');
    });
  });

  describe('formatVersion', () => {
    it('should format version with v prefix', () => {
      expect(versionService.formatVersion('0.6.0')).toBe('v0.6.0');
    });
  });
});
