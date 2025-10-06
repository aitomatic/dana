import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { versionService, type VersionInfo } from '@/services/versionService';

interface VersionStatusProps {
  className?: string;
  showIcon?: boolean;
  compact?: boolean;
}

export const VersionStatus: React.FC<VersionStatusProps> = ({
  className = '',
  showIcon = true,
  compact = false,
}) => {
  const [versionInfo, setVersionInfo] = useState<VersionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const checkVersion = async () => {
      setIsLoading(true);
      try {
        // Get detailed version status (service handles caching internally)
        const status = await versionService.getVersionStatus();
        setVersionInfo({
          current: status.current,
          latest: status.latest,
          isOutdated: status.status === 'outdated',
          updateAvailable: status.status === 'outdated',
          status: status.status,
          message: status.message,
        });
      } catch (error) {
        console.error('Version check failed:', error);
        // Fallback to current version on error
        const currentVersion = versionService.getCurrentVersion();
        setVersionInfo({
          current: currentVersion,
          latest: currentVersion,
          isOutdated: false,
          updateAvailable: false,
          status: 'error',
          message: 'Version check failed',
        });
      } finally {
        setIsLoading(false);
      }
    };

    checkVersion();
  }, []);

  const getStatusIcon = () => {
    if (isLoading) {
      return <Loader2 className="w-3 h-3 text-gray-400 animate-spin" />;
    }

    // Handle newer-than-published case
    if (versionInfo?.status === 'newer-than-published') {
      return compact ? (
        <div className="w-2 h-2 bg-gray-500 rounded-full" />
      ) : (
        <CheckCircle className="w-3 h-3 text-gray-500" />
      );
    }

    if (versionInfo?.updateAvailable) {
      return <AlertCircle className="w-3 h-3 text-orange-500" />;
    }

    // In collapsed mode, show a subtle indicator for up-to-date status
    return compact ? (
      <div className="w-2 h-2 bg-gray-500 rounded-full" />
    ) : (
      <CheckCircle className="w-3 h-3 text-gray-500" />
    );
  };

  const getStatusText = () => {
    if (isLoading) {
      return compact ? 'Checking...' : 'Checking for updates...';
    }

    // Handle newer-than-published case
    if (versionInfo?.status === 'newer-than-published') {
      return compact
        ? `v${versionService.getCurrentVersion()}`
        : `Dev version (v${versionService.getCurrentVersion()})`;
    }

    if (versionInfo?.updateAvailable) {
      return compact
        ? `Update (${versionService.formatVersion(versionInfo.latest)})`
        : `Update available: ${versionService.formatVersion(versionInfo.latest)}`;
    }

    return compact
      ? `v${versionService.formatVersion(versionInfo?.current || versionService.getCurrentVersion()).replace('v', '')}`
      : `Up to date: ${versionService.formatVersion(versionInfo?.current || versionService.getCurrentVersion())}`;
  };

  const getStatusColor = () => {
    if (isLoading) return 'text-gray-400';
    if (versionInfo?.status === 'newer-than-published') return 'text-gray-600';
    if (versionInfo?.updateAvailable) return 'text-orange-600';
    return 'text-green-600';
  };

  return (
    <div className={`flex gap-1 items-center ${className} ${compact ? 'justify-center' : ''}`}>
      {showIcon && getStatusIcon()}
      <span className={`text-xs ${getStatusColor()} ${compact ? 'truncate max-w-16' : ''}`}>
        {getStatusText()}
      </span>
    </div>
  );
};

export default VersionStatus;
