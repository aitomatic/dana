import { useEffect, useState } from 'react';
import { MarkdownViewerSmall } from '@/pages/Agents/chat/markdown-viewer';

interface TextReviewProps {
  content: string;
  fileName?: string;
}

const TextReview = ({ content }: TextReviewProps) => {
  const [data, setData] = useState<string>('');

  useEffect(() => {
    // If content is a blob URL, fetch and parse it as text
    const fetchTextFile = async (url: string) => {
      try {
        const response = await fetch(url);
        const text = await response.text();
        setData(text);
      } catch (error) {
        setData('Failed to load text file');
      }
    };

    if (content && content.startsWith('blob:')) {
      fetchTextFile(content);
    } else {
      setData(content || '');
    }
  }, [content]);

  return (
    <div
      className="flex overflow-auto flex-col text-sm bg-background scrollbar-hide"
      onClick={(e) => e.stopPropagation()}
    >
      <div className="overflow-scroll flex-1 p-4 scrollbar-hide">
        <MarkdownViewerSmall>{data}</MarkdownViewerSmall>
      </div>
    </div>
  );
};

export default TextReview;
