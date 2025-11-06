import React, { useState, useEffect } from 'react';
import { InfoCircle, Xmark } from 'iconoir-react';
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
    <div className="px-4 py-2 w-full">
      <div className="flex justify-between items-center p-3 bg-orange-50 rounded-sm border border-orange-200">
        <div className="flex gap-2 items-center">
          <InfoCircle className="w-6 h-6 text-orange-700" />
          <span className="text-sm text-orange-700">
            <span className="font-semibold">
              You're using an older version of Dana Agent Studio (
              {versionService.formatVersion(versionInfo.current)}).{' '}
            </span>
            <span className="font-normal">
              For the best experience and latest features, please update to the latest version{' '}
              {versionService.formatVersion(versionInfo.latest)} .
            </span>
          </span>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={handleDismiss}
          className="p-0 w-6 h-6 text-gray-500 hover:bg-gray-100"
        >
          <Xmark className="w-3 h-3" />
        </Button>
      </div>
    </div>
  );
};

export default VersionNotification;
