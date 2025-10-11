import React, { useState, useEffect } from 'react';
import { AlertCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { versionService, type VersionInfo } from '@/services/versionService';

interface VersionNotificationProps {
  onDismiss?: () => void;
}

export const VersionNotification: React.FC<VersionNotificationProps> = ({ onDismiss }) => {
  const [versionInfo, setVersionInfo] = useState<VersionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

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

        // Only show notification for actual updates, not for dev versions
        if (status.status === 'newer-than-published') {
          console.log('Running development version:', status.message);
        }
      } catch (error) {
        console.error('Version check failed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkVersion();
  }, []);

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  // Don't show notification for dev versions or if dismissed/loading
  if (isDismissed || isLoading || versionInfo?.status === 'newer-than-published') {
    return null;
  }

  if (!versionInfo?.updateAvailable) {
    return null;
  }

  return (
    <div className="w-full px-4 py-2">
      <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-blue-600" />
          <span className="text-sm text-blue-800">
            Dana {versionService.formatVersion(versionInfo.latest)} is available. You're running{' '}
            {versionService.formatVersion(versionInfo.current)}.
          </span>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={handleDismiss}
          className="text-blue-600 hover:bg-blue-100 h-6 w-6 p-0"
        >
          <X className="w-3 h-3" />
        </Button>
      </div>
    </div>
  );
};

export default VersionNotification;
