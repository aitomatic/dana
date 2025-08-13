import { useEffect, useState } from 'react';

interface DocReviewProps {
  file: File | Blob | string; // Accept File, Blob, or URL string
}

const DocReview = ({ file }: DocReviewProps) => {
  const [textContent, setTextContent] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDocx = async () => {
      setLoading(true);
      setError(null);
      try {
        let arrayBuffer: ArrayBuffer;
        if (typeof file === 'string') {
          // fetch file from url
          const res = await fetch(file);
          arrayBuffer = await res.arrayBuffer();
        } else {
          arrayBuffer = await (file as Blob).arrayBuffer();
        }
        // Dynamically import mammoth to avoid SSR issues
        const mammoth = await import('mammoth');
        const result = await mammoth.convertToHtml({ arrayBuffer });
        setTextContent(result.value);
      } catch (err: any) {
        setError('Failed to load document');
      } finally {
        setLoading(false);
      }
    };

    const loadDoc = async () => {
      setLoading(true);
      setError(null);
      try {
        // .doc (legacy) is not well supported in browser, so we just show a message
        setError('Document preview not supported');
      } finally {
        setLoading(false);
      }
    };

    if (!file) {
      setTextContent('');
      setError(null);
      return;
    }

    let fileName = '';
    if (typeof file === 'string') {
      fileName = file;
    } else if ('name' in file) {
      fileName = file.name;
    }

    if (fileName.endsWith('.docx')) {
      loadDocx();
    } else if (fileName.endsWith('.doc')) {
      loadDoc();
    } else {
      setError('Unsupported file type');
    }
    // eslint-disable-next-line
  }, [file]);

  if (loading) {
    return <div className="p-4 text-gray-500">Loading document preview...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  if (!textContent) {
    return null;
  }

  return (
    <div className="overflow-auto p-4 scrollbar-hide">
      <div className="max-w-none text-sm prose" dangerouslySetInnerHTML={{ __html: textContent }} />
    </div>
  );
};

export default DocReview;
