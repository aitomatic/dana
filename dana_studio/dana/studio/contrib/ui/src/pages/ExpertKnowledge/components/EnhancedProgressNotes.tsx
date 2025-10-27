import { useEffect, useState, useCallback } from 'react';
import { IconLoader2 } from '@tabler/icons-react';
import { apiService } from '@/lib/api';
import { TopicCard } from './TopicCard';
import { parseInterviewNotesByTopic } from './parseNotesUtils';
import type { ProgressData } from './ProgressTracker';

interface EnhancedProgressNotesProps {
  sessionId: number;
}

export function EnhancedProgressNotes({ sessionId }: EnhancedProgressNotesProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [noteContent, setNoteContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set());


  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Check if API methods exist
      if (typeof apiService.getSessionProgress !== 'function') {
        console.warn('getSessionProgress not available, using fallback');
        setError('Progress tracking temporarily unavailable');
        setIsLoading(false);
        return;
      }
      
      if (typeof apiService.getInterviewSession !== 'function') {
        console.warn('getInterviewSession not available, using fallback');
        setError('Session data temporarily unavailable');
        setIsLoading(false);
        return;
      }
      
      // Cache-busting: Add timestamp to ensure fresh data
      const cacheBuster = Date.now();
      console.log(`🔄 Fetching session progress (cache buster: ${cacheBuster})`);
      
      // Fetch progress data with timeout
      const progressPromise = apiService.getSessionProgress(sessionId);
      const progressTimeout = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Progress request timeout')), 10000)
      );
      
      const progressResponse = await Promise.race([progressPromise, progressTimeout]);
      
             if (progressResponse && progressResponse.success && progressResponse.data) {
               // Validate data changed before updating state (detect stale data)
               const dataChanged = JSON.stringify(progressResponse.data) !== JSON.stringify(progress);
               
               if (!dataChanged && progress !== null) {
                 console.warn('⚠️ Received stale data from progress API - data unchanged');
               } else {
                 console.log('✅ Progress data updated successfully');
               }
               
               setProgress(progressResponse.data);

               // Auto-expand current topic and completed topics
               const newExpanded = new Set<string>();
               if (progressResponse.data.topics && Array.isArray(progressResponse.data.topics)) {
                 progressResponse.data.topics.forEach((topic: any) => {
                   if (topic.topic_name === progressResponse.data.current_topic ||
                       topic.status === 'completed') {
                     newExpanded.add(topic.topic_name);
                   }
                 });
               }
               setExpandedTopics(newExpanded);
               
               // Log current topic for debugging
               if (progressResponse.data.current_topic) {
                 console.log(`📍 Current topic: ${progressResponse.data.current_topic}`);
               }
             } else {
               console.warn('Progress response invalid:', progressResponse);
               setError(progressResponse?.error || 'Failed to load progress');
             }
      
      // Fetch session data for notes with timeout
      const sessionPromise = apiService.getInterviewSession(sessionId);
      const sessionTimeout = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Session request timeout')), 10000)
      );
      
      const sessionResponse = await Promise.race([sessionPromise, sessionTimeout]);
      
      if (sessionResponse && sessionResponse.success && sessionResponse.data) {
        setNoteContent(sessionResponse.data.content || '');
      } else {
        console.warn('Session response invalid:', sessionResponse);
        // Don't set error here, just continue without notes
      }
      
    } catch (err: any) {
      console.error('Failed to fetch data:', err);
      setError(err?.message || 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Expose refresh function globally for chat sidebar to call
  useEffect(() => {
    (window as any).refreshSessionProgress = fetchData;
    return () => {
      delete (window as any).refreshSessionProgress;
    };
  }, [fetchData]);

  const toggleTopic = (topicName: string) => {
    setExpandedTopics((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(topicName)) {
        newSet.delete(topicName);
      } else {
        newSet.add(topicName);
      }
      return newSet;
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <IconLoader2 className="w-6 h-6 text-green-600 animate-spin" />
        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
          Loading progress...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">{error}</p>
      </div>
    );
  }

  if (!progress || progress.topics.length === 0) {
    return (
      <div className="text-center py-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {progress ? 
            'No topics tracked yet. Start the interview to see progress.' :
            'Loading interview progress...'}
        </p>
      </div>
    );
  }

  // Parse note content by topic with error handling
  let noteTopics = new Map();
  try {
    noteTopics = parseInterviewNotesByTopic(noteContent);
  } catch (err) {
    console.error('Failed to parse interview notes:', err);
    console.warn('Continuing with empty note topics');
    // Continue with empty noteTopics
  }
  
  const completedCount = progress.topics.filter((t) => t.status === 'completed').length;
  const totalCount = progress.topics.length;

  return (
    <div className="space-y-4">
      {/* Overall Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-300">
            Overall Progress
          </span>
          <span className="text-gray-600 dark:text-gray-400">
            {completedCount}/{totalCount} Topics ({progress.overall_completeness}%)
          </span>
        </div>
        <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-600 transition-all duration-500 ease-out"
            style={{ width: `${progress.overall_completeness}%` }}
          ></div>
        </div>
      </div>

             {/* Topics List */}
             <div className="space-y-1">
               {progress.topics.map((topic, index) => {
                 try {
                   const isCurrentTopic = topic.topic_name === progress.current_topic;
                   const isExpanded = expandedTopics.has(topic.topic_name);
                   const noteTopic = noteTopics.get(topic.topic_name);

                   return (
                     <TopicCard
                       key={index}
                       topicName={topic.topic_name || `Topic ${index + 1}`}
                       status={topic.status || 'not_started'}
                       completeness={topic.completeness || 0}
                       insightsCount={topic.insights_count || 0}
                       questions={topic.questions || []}
                       noteContent={noteTopic}
                       isCurrentTopic={isCurrentTopic}
                       isExpanded={isExpanded}
                       onToggle={() => toggleTopic(topic.topic_name)}
                     />
                   );
                 } catch (err) {
                   console.error(`Error rendering topic ${index}:`, err);
                   return (
                     <div key={index} className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                       <p className="text-sm text-red-600 dark:text-red-400">
                         Error loading topic {index + 1}
                       </p>
                     </div>
                   );
                 }
               })}
             </div>
    </div>
  );
}
