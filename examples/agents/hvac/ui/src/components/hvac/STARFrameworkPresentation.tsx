import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { useEffect, useState } from 'react';

interface STARFrameworkPresentationProps {
  onDismiss: () => void;
}

export function STARFrameworkPresentation({ onDismiss }: STARFrameworkPresentationProps) {
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    // Check localStorage on mount
    const dismissed = localStorage.getItem('hvac-star-presentation-dismissed');
    if (dismissed) {
      setIsDismissed(true);
    }
  }, []);

  if (isDismissed) {
    return null;
  }

  const handleDismiss = () => {
    localStorage.setItem('hvac-star-presentation-dismissed', 'true');
    setIsDismissed(true);
    onDismiss();
  };

  return (
    <Card className="opacity-0 animate-fade-in-up will-change-[opacity,transform]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">Overview of STAR Framework for Agent</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
            onClick={handleDismiss}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center w-full overflow-x-auto">
          <img
            src="/images/star-framework.svg"
            alt="STAR Framework for Agent - SEE, THINK, ACT, REFLECT with Continuous Learning Loop"
            className="w-full max-w-full h-auto"
          />
        </div>
      </CardContent>
    </Card>
  );
}

