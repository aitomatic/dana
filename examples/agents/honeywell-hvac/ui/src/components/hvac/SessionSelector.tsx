import { useHVACStore } from '@/stores/hvac-store';
import { hvacApi } from '@/lib/hvac-api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus } from 'lucide-react';

export function SessionSelector() {
  const { currentSession, setCurrentSession, setAcquisitiveLearnings, setEpisodicLearning } = useHVACStore();

  const handleNewSession = async () => {
    try {
      const session = await hvacApi.createSession();
      setCurrentSession(session);
      // Reload learnings for new session
      setAcquisitiveLearnings([]);
      setEpisodicLearning(null);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {currentSession && (
        <Badge variant="outline">
          Session: {currentSession.session_id}
        </Badge>
      )}
      <Button variant="outline" size="sm" onClick={handleNewSession}>
        <Plus className="w-4 h-4 mr-1" />
        New Session
      </Button>
    </div>
  );
}
