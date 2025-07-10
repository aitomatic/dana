import { useMemo, useState, Fragment } from 'react';
import type { ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
// import oneLight from 'react-syntax-highlighter/dist/esm/styles/prism/one-light';
import 'katex/dist/katex.min.css';

import { cn } from '@/lib/utils';
import { IconCheck, IconCopy, IconPlayerPlay } from '@tabler/icons-react';

import styles from './MarkdownViewer.module.css';
import ReactCodeBlock from './react-code-block';

// Type definitions for markdown components
interface CodeProps {
  className?: string;
  children?: ReactNode;
}

interface ParagraphProps {
  children?: ReactNode;
}

interface TableProps {
  children?: ReactNode;
}

interface TableRowProps {
  children?: ReactNode;
}

interface TableCellProps {
  children?: ReactNode;
}

const regex = /(@[^@]*?\.(?:\w+))/g;

// Enhanced @ mention formatting with better styling and interaction
const MentionSpan = ({ mention }: { mention: string }) => {
  const [_, setIsShowSources] = useState(false);
  const handleMentionClick = () => {
    setIsShowSources(true);
  };
  return (
    <span
      className="font-medium text-brand-600 bg-brand-50 rounded-md px-1.5 py-0.5 cursor-pointer hover:bg-brand-100 transition-colors"
      onClick={handleMentionClick}
    >
      {mention}
    </span>
  );
};

// export const CitationName = ({ name, index }: { name: string; index: number }) => {
//   const fileName = name.split("/").at(-1);
//   return (
//     <Tooltip key={name}>
//       <TooltipTrigger type="button">
//         <div className="grid grid-cols-1 px-1 py-1 text-xs truncate rounded-full text-brand-700 bg-brand-50">
//           {fileName} [{index + 1}]
//         </div>
//       </TooltipTrigger>
//       <TooltipPortal>
//         <TooltipContent className="cursor-pointer">
//           <div className="flex-1 text-sm font-normal">{name}</div>
//         </TooltipContent>
//       </TooltipPortal>
//     </Tooltip>
//   );
// };

// export const RenderCitations = ({ citations, index }: { citations: any[]; index: number }) => {
//   const item = useMemo(() => {
//     if (index > citations.length - 1) return null;

//     const citation = citations[index];
//     if (!citation) return null;

//     if (Array.isArray(citation.resources) && citation.resources.length > 0) {
//       return {
//         id: index,
//         name: citation.resources[0].name,
//         resources: citation.resources,
//       };
//     }

//     if (citation.source) {
//       return {
//         id: index,
//         name: citation.source.split("/").at(-1),
//       };
//     }

//     if (Array.isArray(citation.retrievals) && citation.retrievals.length > 0) {
//       return {
//         id: index,
//         name: citation.retrievals,
//       };
//     }

//     return {
//       id: index,
//       name: citation.name ?? "",
//     };
//   }, [citations, index]);

//   if (!item || item.name === "") return null;

//   if (Array.isArray(item.name)) {
//     return (
//       <div className="flex flex-wrap items-center gap-1 truncate">
//         {item.name.map((name, idx) => (
//           <CitationName key={name} name={name} index={idx} />
//         ))}
//       </div>
//     );
//   }

//   return <CitationName name={item.name} index={index} />;
// };

// MermaidBlock Component - Extracted for better organization
const MermaidBlock = ({ content }: { content: string }) => {
  const [copiedContent, setCopiedContent] = useState(false);
  const blockId = `mermaid-block-${Math.random().toString(36).substr(2, 9)}`;

  const handleCopyCode = () => {
    navigator.clipboard.writeText(content);
    setCopiedContent(true);
    setTimeout(() => setCopiedContent(false), 2000);
  };

  return (
    <div
      className="relative grid w-full grid-cols-1 mt-2 mb-4 overflow-hidden border border-gray-200 rounded-lg"
      id={blockId}
    >
      <div className="absolute z-10 flex gap-2 top-2 right-2">
        <button
          className="px-2.5 py-1 text-xs bg-background/90 text-gray-900 border border-gray-200 rounded-md shadow-xs hover:bg-gray-50 flex items-center gap-1.5 backdrop-blur-sm"
          onClick={handleCopyCode}
          aria-label="Copy code to clipboard"
        >
          {copiedContent ? (
            <IconCheck className="w-4 h-4 text-success-500" />
          ) : (
            <IconCopy className="w-4 h-4 text-gray-500" />
          )}
          <span>Copy</span>
        </button>
        <button
          className="px-2.5 py-1 text-xs bg-background/90 text-brand-700 border border-gray-200 rounded-md shadow-xs hover:bg-gray-50 flex items-center gap-1.5 backdrop-blur-sm"
          onClick={() => { }}
          aria-label="Run Mermaid diagram"
        >
          <IconPlayerPlay className="w-4 h-4 text-brand-700" />
          <span>Preview</span>
        </button>
      </div>
      <SyntaxHighlighter
        className="text-sm xl:text-base"
        language="mermaid"
        // style={oneLight}
        customStyle={{
          margin: 0,
          borderRadius: 0,
          lineHeight: 1.5,
          padding: '1rem',
        }}
        showLineNumbers={true}
        wrapLines={true}
      >
        {content}
      </SyntaxHighlighter>
    </div>
  );
};

// Standard Code Block Component
export const CodeBlock = ({ content, language }: { content: string; language: string }) => {
  const [copiedContent, setCopiedContent] = useState(false);
  const blockId = `code-block-${Math.random().toString(36).substr(2, 9)}`;

  const handleCopyCode = () => {
    navigator.clipboard.writeText(content);
    setCopiedContent(true);
    setTimeout(() => setCopiedContent(false), 2000);
  };

  return (
    <div
      className="relative grid w-full grid-cols-1 mt-2 mb-4 overflow-hidden border border-gray-200 rounded-lg"
      id={blockId}
    >
      <button
        className="absolute top-2 right-2 z-10 px-2.5 py-1 text-xs bg-background/90 text-gray-900 border border-gray-200 rounded-md shadow-xs hover:bg-gray-50 flex items-center gap-1.5 backdrop-blur-sm"
        onClick={handleCopyCode}
        aria-label="Copy code to clipboard"
      >
        {copiedContent ? (
          <IconCheck className="w-4 h-4 text-success-500" />
        ) : (
          <IconCopy className="w-4 h-4 text-gray-500" />
        )}
        <span>Copy</span>
      </button>
      <SyntaxHighlighter
        className="text-sm xl:text-base"
        language={language || 'text'}
        // style={oneLight}
        customStyle={{
          margin: 0,
          borderRadius: 0,
          lineHeight: 1.5,
          padding: '1rem',
        }}
        showLineNumbers={true}
        wrapLines={true}
      >
        {content}
      </SyntaxHighlighter>
    </div>
  );
};

export const MarkdownViewerSmall = ({
  children = '',
  classname = '',
  useMath = true,
}: {
  children: string;
  classname?: string;
  useMath?: boolean;
  citations?: any[];
}) => {
  const refinedContent = useMemo(() => {
    if (children.startsWith('```markdown')) {
      children = children.substring(12);
    }
    if (children.startsWith('```') && !children.startsWith('```c')) {
      children = children.substring(3);
      if (children.endsWith('```')) {
        children = children.slice(0, -3);
      }
    }
    return (
      (children ?? '')
        // eslint-disable-next-line
        // @ts-ignore
        .replaceAll('$', '\\$')
        .replace(/\\\[/g, '\n \n \n $ \n ')
        .replace(/\\\]/g, '\n $ \n\n')
        .replaceAll('\n', ' \n ')
    );
  }, [children]);

  const remarkPlugins = useMemo(() => {
    const plugins: any[] = [remarkGfm];
    if (useMath) plugins.push(remarkMath);
    return plugins;
  }, [useMath]);

  return (
    <div
      className={cn(
        styles['content'],
        styles['content-small'],
        'w-full text-sm xl:text-base',
        classname,
      )}
    >
      <ReactMarkdown
        remarkPlugins={remarkPlugins}
        rehypePlugins={[rehypeKatex as any]}
        components={{
          code: ({ className, children }: CodeProps) => {
            const content = String(children).trim();
            const languageMatch = /language-(\w+)/.exec(className || '');
            const language = languageMatch ? languageMatch[1] : '';
            const isInline = !className;
            const isMermaid = language === 'mermaid';
            const isReact =
              language === 'jsx' ||
              language === 'tsx' ||
              content.includes('import React') ||
              content.includes("from 'react'") ||
              content.includes('from "react"');

            const isRechart =
              content.includes('import { ') &&
              (content.includes(" from 'recharts'") || content.includes(' from "recharts"'));

            // Handle inline code
            if (isInline) {
              const isHook = /^use[A-Z]/.test(content);
              const isType = /^[A-Z][A-Za-z0-9]*$/.test(content);
              const isVariable = /^[a-z_$][a-zA-Z0-9_$]*$/.test(content);
              const isSingleWord = content.split(/\s+/).length === 1;

              return (
                <code
                  className={cn(
                    'font-mono font-normal px-1.5 py-0.5 rounded text-sm xl:text-base',
                    isHook
                      ? 'bg-purple-100 text-purple-800'
                      : isType
                        ? 'bg-yellow-100 text-yellow-800'
                        : isVariable
                          ? 'bg-gray-100 text-gray-800'
                          : 'bg-gray-50 text-gray-900',
                    isSingleWord ? 'inline-block' : '',
                  )}
                >
                  {content}
                </code>
              );
            }

            // Handle mermaid blocks with separate component
            // if (isMermaid) {
            //   return <MermaidBlock content={content} />;
            // }

            // Handle React code blocks with separate component
            if (isReact && isRechart) {
              return <ReactCodeBlock content={content} />;
            }

            // Handle regular code blocks with separate component
            // return <CodeBlock content={content} language={language} />;

            return <pre>{content}</pre>
          },

          p: ({ children }: ParagraphProps) => {
            if (Array.isArray(children)) {
              // Check if any of the children items contain @ mentions
              const hasAtMention = children.some(
                (child) => typeof child === 'string' && child.includes('@'),
              );

              if (hasAtMention) {
                return (
                  <p className={`py-1 text-sm xl:text-base text-gray-900`}>
                    {children.map((child, index) => {
                      if (typeof child === 'string' && child.includes('@')) {
                        const parts = child.split(regex);
                        return (
                          <Fragment key={index}>
                            {parts.map((part, partIndex) => {
                              if (part.startsWith('@')) {
                                // Use the enhanced MentionSpan component
                                return <MentionSpan key={partIndex} mention={part} />;
                              }
                              return <span key={partIndex}>{part}</span>;
                            })}
                          </Fragment>
                        );
                      }
                      return child;
                    })}
                  </p>
                );
              }
            }

            // Handle string children with @ mentions
            if (typeof children === 'string' && children.includes('@')) {
              const parts = children.split(regex);
              return (
                <p className={`py-1 text-sm xl:text-base text-gray-900`}>
                  {parts.map((part, index) => {
                    if (part.startsWith('@')) {
                      // Use the enhanced MentionSpan component
                      return <MentionSpan key={index} mention={part} />;
                    }
                    return <span key={index}>{part}</span>;
                  })}
                </p>
              );
            }

            // Default paragraph rendering
            return <p className={`py-1 text-sm xl:text-base text-gray-900`}>{children}</p>;
          },

          table: ({ children }: TableProps) => (
            <div className="w-full my-4 overflow-x-auto">
              <table className="w-full overflow-hidden border border-collapse border-gray-200 rounded">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }: TableProps) => <thead className="bg-gray-50">{children}</thead>,
          tbody: ({ children }: TableProps) => (
            <tbody className="divide-y divide-gray-200">{children}</tbody>
          ),
          tr: ({ children }: TableRowProps) => <tr>{children}</tr>,
          th: ({ children }: TableCellProps) => {
            return (
              <th
                className={`px-4 py-3 font-medium tracking-wider text-left text-gray-900 uppercase border-b border-gray-200 first:rounded-tl last:rounded-tr text-sm`}
              >
                {children}
              </th>
            );
          },
          td: ({ children }: TableCellProps) => {
            // Handle React elements directly when they're passed as children
            if (
              children &&
              typeof children === 'object' &&
              '$$typeof' in children &&
              children.$$typeof === Symbol.for('react.element')
            ) {
              return (
                <td className={`px-4 py-3 border-b border-gray-200 text-gray-900`}>{children}</td>
              );
            }

            // Process array of children that might contain React elements
            if (Array.isArray(children)) {
              const hasReactElements = children.some(
                (child) =>
                  child &&
                  typeof child === 'object' &&
                  child.$$typeof === Symbol.for('react.element'),
              );

              if (hasReactElements) {
                return (
                  <td className={`px-4 py-3 border-b border-gray-200 text-gray-900`}>{children}</td>
                );
              }
            }

            // For string content, continue with the existing logic
            const content = Array.isArray(children)
              ? children.map((child) => (typeof child === 'string' ? child : '')).join('')
              : String(children || '');

            // Handle bold type formatting with asterisks
            const formattedContent = content.replace(/\*\*([^*]+)\*\*/g, (_, text) => {
              return `<strong>${text}</strong>`;
            });

            const parts = formattedContent.split(/(\[\[\d+\]\])/);

            if (parts?.length === 1) {
              return (
                <td className={`px-4 py-3 border-b border-gray-200 text-gray-900`}>{children}</td>
              );
            }

            return (
              <td className={`px-4 py-3 border-b border-gray-200 text-gray-900`}>
                <span className="inline-flex flex-wrap items-center gap-1">
                  {parts?.map((part, index) => {
                    return <span key={index} dangerouslySetInnerHTML={{ __html: part }} />;
                  })}
                </span>
              </td>
            );
          },

          text: ({ children }) => {
            const content = Array.isArray(children)
              ? children.map((child) => (typeof child === 'string' ? child : '')).join('')
              : String(children);

            // Check for @ mentions in text content
            if (content.includes('@')) {
              const parts = content.split(regex);
              return (
                <span className="inline-flex flex-wrap items-center">
                  {parts.map((part, idx) => {
                    if (part.startsWith('@')) {
                      return <MentionSpan key={idx} mention={part} />;
                    }
                    return <span key={idx}>{part}</span>;
                  })}
                </span>
              );
            }

            // Handle bold type formatting with asterisks
            const formattedContent = content.replace(/\*\*([^*]+)\*\*/g, (_, text) => {
              return `<strong>${text}</strong>`;
            });

            const parts = formattedContent.split(/(\[\[\d+\]\])/);

            if (parts.length === 1) {
              return <span dangerouslySetInnerHTML={{ __html: formattedContent }} />;
            }

            return (
              <span className="inline-flex flex-wrap items-center gap-1">
                {parts.map((part, index) => {
                  return <span key={index} dangerouslySetInnerHTML={{ __html: part }} />;
                })}
              </span>
            );
          },
        }}
      >
        {refinedContent}
      </ReactMarkdown>
    </div>
  );
};
