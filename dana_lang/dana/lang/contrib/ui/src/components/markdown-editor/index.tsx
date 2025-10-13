import React, { useState, useRef } from 'react';
import { IconEye, IconEyeOff, IconH1, IconH2, IconH3 } from '@tabler/icons-react';
import { MarkdownViewerSmall } from '@/pages/Agents/chat/markdown-viewer';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  height?: string;
}

const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  value,
  onChange,
  placeholder = 'Start writing in markdown...',
  className = '',
  height = '400px',
}) => {
  const [isPreview, setIsPreview] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Insert text at cursor position
  const insertText = (before: string, after: string = '', placeholder: string = '') => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end);
    const textToInsert = selectedText || placeholder;

    const newText =
      value.substring(0, start) + before + textToInsert + after + value.substring(end);
    onChange(newText);

    // Set cursor position
    setTimeout(() => {
      const newCursorPos = start + before.length + textToInsert.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
      textarea.focus();
    }, 0);
  };

  // Insert text at beginning of line
  const insertAtLineStart = (prefix: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const beforeCursor = value.substring(0, start);
    const lineStart = beforeCursor.lastIndexOf('\n') + 1;

    const newText = value.substring(0, lineStart) + prefix + value.substring(lineStart);
    onChange(newText);

    setTimeout(() => {
      const newCursorPos = start + prefix.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
      textarea.focus();
    }, 0);
  };

  // Toolbar actions
  const actions = {
    bold: () => insertText('**', '**', 'bold text'),
    italic: () => insertText('*', '*', 'italic text'),
    strikethrough: () => insertText('~~', '~~', 'strikethrough text'),
    code: () => insertText('`', '`', 'code'),
    h1: () => insertAtLineStart('# '),
    h2: () => insertAtLineStart('## '),
    h3: () => insertAtLineStart('### '),
    bulletList: () => insertAtLineStart('- '),
    orderedList: () => insertAtLineStart('1. '),
    blockquote: () => insertAtLineStart('> '),
    link: () => insertText('[', '](url)', 'link text'),
    separator: () => insertText('\n---\n'),
    table: () =>
      insertText(
        '\n| Header 1 | Header 2 | Header 3 |\n|----------|----------|----------|\n| Cell 1   | Cell 2   | Cell 3   |\n',
      ),
  };

  return (
    <div
      className={`flex overflow-hidden flex-col rounded-lg border border-gray-200 dark:border-gray-700 bg-background dark:bg-gray-900 ${className}`}
    >
      {/* Toolbar */}
      <div className="flex flex-wrap gap-1 items-center p-3 bg-gray-50 border-b border-gray-200 dark:border-gray-700 dark:bg-gray-800">
        {/* Headers */}
        <button
          onClick={actions.h1}
          className="flex justify-center items-center w-8 h-8 text-gray-600 rounded transition-colors dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
          title="Heading 1 (# )"
          type="button"
        >
          <IconH1 size={16} />
        </button>

        <button
          onClick={actions.h2}
          className="flex justify-center items-center w-8 h-8 text-gray-600 rounded transition-colors dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
          title="Heading 2 (## )"
          type="button"
        >
          <IconH2 size={16} />
        </button>

        <button
          onClick={actions.h3}
          className="flex justify-center items-center w-8 h-8 text-gray-600 rounded transition-colors dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
          title="Heading 3 (### )"
          type="button"
        >
          <IconH3 size={16} />
        </button>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600" />

        {/* Preview Toggle */}
        <button
          onClick={() => setIsPreview(!isPreview)}
          className={`flex items-center justify-center w-8 h-8 transition-colors rounded ${
            isPreview
              ? 'bg-brand-100 text-brand-700 dark:bg-brand-800 dark:text-brand-200'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
          }`}
          title={isPreview ? 'Edit Mode' : 'Preview Mode'}
          type="button"
        >
          {isPreview ? <IconEyeOff size={16} /> : <IconEye size={16} />}
        </button>
      </div>

      {/* Editor/Preview Area */}
      <div className="overflow-hidden flex-1" style={{ height }}>
        {isPreview ? (
          <div className="overflow-y-auto p-4 h-full">
            <MarkdownViewerSmall>{value}</MarkdownViewerSmall>
          </div>
        ) : (
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="p-4 w-full h-full font-mono text-sm bg-transparent border-none outline-none resize-none"
            style={{ minHeight: height }}
          />
        )}
      </div>

      {/* Status Bar */}
      <div className="px-4 py-2 text-xs text-gray-500 bg-gray-50 border-t border-gray-200 dark:border-gray-700 dark:text-gray-400 dark:bg-gray-800">
        {isPreview
          ? 'Preview Mode'
          : `${value.length} characters | ${value.split('\n').length} lines`}
      </div>
    </div>
  );
};

export default MarkdownEditor;
