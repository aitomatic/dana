import { useMemo, Fragment, useEffect } from 'react';
import type { ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import SyntaxHighlighter from 'react-syntax-highlighter';

// Import KaTeX CSS directly
import 'katex/dist/katex.min.css';

// Import GitHub Markdown CSS for light theme (default)
import 'github-markdown-css/github-markdown-light.css';

// Import custom theme switcher CSS
import './markdown-theme-switcher.css';

// Import enhanced KaTeX styling
import './katex-styling.css';

let codeStyle: any;
try {
  // @ts-ignore
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  codeStyle = require('react-syntax-highlighter/dist/styles/hljs/vs2015').default;
} catch (e) {
  try {
    // @ts-ignore
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    codeStyle = require('react-syntax-highlighter/dist/styles/default').default;
  } catch (e2) {
    codeStyle = {};
  }
}
import 'katex/dist/katex.min.css';

import { cn } from '@/lib/utils';

import ReactCodeBlock from './react-code-block';

// Comprehensive markdown pre-processing function
const preprocessMarkdownContent = (content: string): string => {
  let processed = content;

  // 1. NUMBERED LIST TRANSFORMATION
  // Convert numbered lists to headers for better visual hierarchy
  // Example: "1. **Future Value (FV):**" -> "## 1. Future Value (FV)"
  processed = processed.replace(/^(\d+)\.\s+\*\*(.*?)\*\*:?\s*$/gm, (_, number, title) => {
    return `## ${number}. ${title}`;
  });

  // 2. LATEX TO CODE BLOCK TRANSFORMATION
  // Convert LaTeX notation to code blocks for better readability
  // Convert \\[ ... \\] to code blocks
  processed = processed.replace(/\\\[\s*\n?([\s\S]*?)\n?\s*\\\]/g, (_, mathContent) => {
    const cleanMath = mathContent
      .replace(/\\times/g, '×')
      .replace(/\\cdot/g, '·')
      .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1 / $2)')
      .replace(/\\sum/g, 'Σ')
      .replace(/\\\(/g, '')
      .replace(/\\\)/g, '')
      .trim();
    return `\n\`\`\`\n${cleanMath}\n\`\`\`\n`;
  });

  // Convert \\( ... \\) to inline code
  processed = processed.replace(/\\\((.*?)\\\)/g, (_, mathContent) => {
    const cleanMath = mathContent
      .replace(/\\times/g, '×')
      .replace(/\\cdot/g, '·')
      .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1 / $2)')
      .trim();
    return `\`${cleanMath}\``;
  });

  // 3. HORIZONTAL RULES ENHANCEMENT - REMOVED
  // No longer adding horizontal rules between sections

  // 4. VARIABLE DEFINITION ENHANCEMENT
  // Enhance "Where:" sections with better formatting
  processed = processed.replace(/^(\s*)-\s+Where\s+\\\(([^)]+)\\\)\s*=\s*(.+)$/gm, '- **$2** = $3');

  // Handle regular variable definitions
  processed = processed.replace(/^(\s*)-\s+\*\*([^*]+)\*\*\s*=\s*(.+)$/gm, '$1- **$2** = $3');

  // Split comma-separated variable definitions into separate list items
  // Handle patterns like "Where PV = Present Value, r = interest rate, n = number of periods"
  processed = processed.replace(/^(\s*)[-*]\s*Where\s+(.+)$/gm, (_, indent, definitions) => {
    // Split by comma and create separate list items
    const items = definitions.split(',').map((item: string) => {
      const trimmed = item.trim();
      // Match pattern like "PV = Present Value" or "r = interest rate"
      const varMatch = trimmed.match(/^(\w+)\s*=\s*(.+)$/);
      if (varMatch) {
        return `${indent}- **${varMatch[1]}** = ${varMatch[2]}`;
      }
      return `${indent}- ${trimmed}`;
    });
    return items.join('\n');
  });

  // Also handle comma-separated variable definitions in regular list items
  // Handle patterns like "- PV = Present Value, r = interest rate, n = number of periods"
  processed = processed.replace(
    /^(\s*)[-*]\s*([A-Z]+\s*=\s*[^,]+(?:,\s*[A-Z]+\s*=\s*[^,]+)+)\.?\s*$/gm,
    (_, indent, definitions) => {
      // Split by comma and create separate list items
      const items = definitions.split(',').map((item: string) => {
        const trimmed = item.trim().replace(/\.$/, ''); // Remove trailing period
        // Match pattern like "PV = Present Value" or "r = interest rate"
        const varMatch = trimmed.match(/^(\w+)\s*=\s*(.+)$/);
        if (varMatch) {
          return `${indent}- **${varMatch[1]}** = ${varMatch[2]}`;
        }
        return `${indent}- ${trimmed}`;
      });
      return items.join('\n');
    },
  );

  // 5. CLEAN UP EXTRA WHITESPACE
  // Remove excessive newlines
  processed = processed.replace(/\n{4,}/g, '\n\n\n');

  // Clean up whitespace around headers
  processed = processed.replace(/^(#{1,6}\s+.*?)(\n{2,})/gm, '$1\n\n');

  // 6. MATH SYMBOL STANDARDIZATION
  // Replace common LaTeX symbols with Unicode
  processed = processed
    .replace(/\\times/g, '×')
    .replace(/\\cdot/g, '·')
    .replace(/\\pm/g, '±')
    .replace(/\\infty/g, '∞')
    .replace(/\\alpha/g, 'α')
    .replace(/\\beta/g, 'β')
    .replace(/\\gamma/g, 'γ')
    .replace(/\\Delta/g, 'Δ')
    .replace(/\\sum/g, 'Σ');

  // 7. CODE BLOCK FORMATTING
  // Ensure formulas in code blocks are properly formatted
  processed = processed.replace(/```\n([^`]+)\n```/g, (_, codeContent) => {
    const formattedCode = codeContent
      .trim()
      .replace(/\s+/g, ' ') // Normalize whitespace
      .replace(/\s*=\s*/g, ' = ') // Standardize equals spacing
      .replace(/\s*\+\s*/g, ' + ') // Standardize plus spacing
      .replace(/\s*-\s*/g, ' - ') // Standardize minus spacing
      .replace(/\s*\*\s*/g, ' × ') // Use multiplication symbol
      .replace(/\s*\/\s*/g, ' / '); // Standardize division spacing

    return `\`\`\`\n${formattedCode}\n\`\`\``;
  });

  return processed;
};

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
  const handleMentionClick = () => {
    // Future implementation for showing sources
  };
  return (
    <span
      className="font-medium text-brand-600 bg-brand-50 rounded-md px-1.5 py-0.5 cursor-pointer"
      onClick={handleMentionClick}
    >
      {mention}
    </span>
  );
};

const MermaidBlock = ({ content }: { content: string }) => {
  const blockId = `mermaid-block-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div
      className="grid overflow-hidden relative grid-cols-1 mt-2 mb-4 w-full rounded-lg border border-gray-200"
      id={blockId}
    >
      <SyntaxHighlighter
        className="text-sm xl:text-base"
        language="mermaid"
        style={codeStyle}
        customStyle={{
          margin: 0,
          borderRadius: 0,
          lineHeight: 1.6,
          padding: '1rem',
          background: 'rgb(30, 30, 30)',
          fontSize: '0.875rem',
        }}
        showLineNumbers={true}
        wrapLines={true}
        wrapLongLines={true}
      >
        {content}
      </SyntaxHighlighter>
    </div>
  );
};

// Standard Code Block Component
export const CodeBlock = ({ content, language }: { content: string; language: string }) => {
  const blockId = `code-block-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div
      className="grid overflow-hidden relative grid-cols-1 mt-2 mb-4 w-full rounded-lg border border-gray-200"
      id={blockId}
    >
      <SyntaxHighlighter
        className="text-sm xl:text-base"
        language={language || 'text'}
        style={codeStyle}
        customStyle={{
          margin: 0,
          borderRadius: 0,
          lineHeight: 1.6,
          padding: '1rem',
          fontSize: '0.875rem',
        }}
        showLineNumbers={true}
        wrapLines={true}
        wrapLongLines={true}
        lineNumberStyle={{ color: '#6b7280', fontSize: '0.75rem' }}
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
  theme = 'light',
  backgroundContext = 'default',
}: {
  children: string;
  classname?: string;
  useMath?: boolean;
  theme?: 'light' | 'dark';
  backgroundContext?: 'user' | 'agent' | 'default';
  citations?: any[];
}) => {
  // Define font size classes in one place for consistency
  const textSizeClasses = 'text-xs xl:text-sm';
  // Dynamically import dark theme CSS when needed
  useEffect(() => {
    if (theme === 'dark') {
      import('github-markdown-css/github-markdown-dark.css');
    }
  }, [theme]);
  const refinedContent = useMemo(() => {
    let content = children;

    // Handle markdown code block wrapping
    if (content.startsWith('```markdown')) {
      content = content.substring(12);
    }
    if (content.startsWith('```') && !content.startsWith('```c')) {
      content = content.substring(3);
      if (content.endsWith('```')) {
        content = content.slice(0, -3);
      }
    }

    // PRE-PROCESSING: Transform content for better rendering
    // Skip preprocessing if math is enabled to preserve LaTeX syntax
    if (!useMath) {
      content = preprocessMarkdownContent(content);
    }

    // Only apply math-safe processing if useMath is enabled
    if (useMath) {
      // Minimal math preprocessing - preserve $ symbols for KaTeX
      // Only clean up obvious malformed math delimiters
      content = content
        // Remove lines that contain only a $ symbol
        .replace(/^\s*\$\s*$/gm, '')
        // Remove standalone $ symbols between newlines
        .replace(/\n\s*\$\s*\n/g, '\n\n')
        // Convert \[ \] to $$ $$ for better KaTeX compatibility
        .replace(/\\\[([\s\S]*?)\\\]/g, '$$\n$1\n$$')
        // Ensure display math has proper spacing
        .replace(/\$\$([\s\S]*?)\$\$/g, (_, mathContent) => {
          return `\n$$${mathContent.trim()}$$\n`;
        })
        // Clean up multiple consecutive newlines
        .replace(/\n\s*\n\s*\n+/g, '\n\n');
    } else {
      // Escape dollars if math is disabled
      content = content.replaceAll('$', '\\$');
    }

    return content;
  }, [children, useMath]);

  const remarkPlugins = useMemo(() => {
    const plugins: any[] = [remarkGfm];
    if (useMath) plugins.push(remarkMath);
    return plugins;
  }, [useMath]);

  const rehypePlugins = useMemo(() => {
    const plugins: any[] = [];
    if (useMath) plugins.push(rehypeKatex);
    return plugins;
  }, [useMath]);

  return (
    <div
      className={cn(
        `markdown-body markdown-body-${theme} markdown-body-${backgroundContext} w-full ${textSizeClasses}`,
        classname,
      )}
    >
      <ReactMarkdown
        remarkPlugins={remarkPlugins}
        rehypePlugins={rehypePlugins}
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
                    `font-mono font-normal px-1.5 py-0.5 rounded ${textSizeClasses}`,
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
            if (isMermaid) {
              return <MermaidBlock content={content} />;
            }

            // Handle React code blocks with separate component
            if (isReact && isRechart) {
              return <ReactCodeBlock content={content} />;
            }

            // Handle regular code blocks with separate component
            return <CodeBlock content={content} language={language} />;
          },

          ul: ({ children }: any) => (
            <ul className={`${textSizeClasses} text-gray-900`}>{children}</ul>
          ),
          li: ({ children }: any) => (
            <li className={`${textSizeClasses} text-gray-900 list-disc`}>{children}</li>
          ),
          p: ({ children }: ParagraphProps) => {
            // Helper function to enhance financial terms
            const enhanceFinancialTerms = (text: string) => {
              const financialTerms = [
                'Future Value',
                'FV',
                'Present Value',
                'PV',
                'Net Present Value',
                'NPV',
                'Internal Rate of Return',
                'IRR',
                'Return on Investment',
                'ROI',
                'Debt-to-Income Ratio',
                'DTI',
                'Savings Rate',
                'interest rate',
                'discount rate',
                'cash flow',
              ];

              let result = text;
              financialTerms.forEach((term) => {
                const regex = new RegExp(`\\b(${term})\\b`, 'gi');
                result = result.replace(regex, `<span class="financial-term">$1</span>`);
              });
              return result;
            };

            if (Array.isArray(children)) {
              // Check if any of the children items contain @ mentions
              const hasAtMention = children.some(
                (child) => typeof child === 'string' && child.includes('@'),
              );

              if (hasAtMention) {
                return (
                  <p className={`py-1 ${textSizeClasses} text-gray-900`}>
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
                              return (
                                <span
                                  key={partIndex}
                                  dangerouslySetInnerHTML={{ __html: enhanceFinancialTerms(part) }}
                                />
                              );
                            })}
                          </Fragment>
                        );
                      }
                      if (typeof child === 'string') {
                        // Skip rendering if the child only contains a $ symbol
                        const trimmedContent = child.trim();
                        if (trimmedContent === '$' || trimmedContent === '') {
                          return null;
                        }

                        return (
                          <span
                            key={index}
                            dangerouslySetInnerHTML={{ __html: enhanceFinancialTerms(child) }}
                          />
                        );
                      }
                      return child;
                    })}
                  </p>
                );
              }

              // Handle array children without @ mentions
              return (
                <p className={`py-1 ${textSizeClasses} text-gray-900`}>
                  {children.map((child, index) => {
                    if (typeof child === 'string') {
                      // Skip rendering if the child only contains a $ symbol
                      const trimmedContent = child.trim();
                      if (trimmedContent === '$' || trimmedContent === '') {
                        return null;
                      }

                      return (
                        <span
                          key={index}
                          dangerouslySetInnerHTML={{ __html: enhanceFinancialTerms(child) }}
                        />
                      );
                    }
                    return child;
                  })}
                </p>
              );
            }

            // Handle string children with @ mentions
            if (typeof children === 'string' && children.includes('@')) {
              const parts = children.split(regex);
              return (
                <p className={`py-1 ${textSizeClasses} text-gray-900`}>
                  {parts.map((part, index) => {
                    if (part.startsWith('@')) {
                      // Use the enhanced MentionSpan component
                      return <MentionSpan key={index} mention={part} />;
                    }
                    return (
                      <span
                        key={index}
                        dangerouslySetInnerHTML={{ __html: enhanceFinancialTerms(part) }}
                      />
                    );
                  })}
                </p>
              );
            }

            // Default paragraph rendering with financial term enhancement
            if (typeof children === 'string') {
              // Skip rendering if the paragraph only contains a $ symbol
              const trimmedContent = children.trim();
              if (trimmedContent === '$' || trimmedContent === '') {
                return null;
              }

              return (
                <p
                  className={`py-1 ${textSizeClasses} text-gray-900`}
                  dangerouslySetInnerHTML={{ __html: enhanceFinancialTerms(children) }}
                />
              );
            }

            // For non-string children (React elements), render normally without financial term enhancement
            return <p className={`py-1 ${textSizeClasses} text-gray-900`}>{children}</p>;
          },

          table: ({ children }: TableProps) => (
            <div className="overflow-x-auto my-4 w-full">
              <table className="overflow-hidden w-full rounded border border-gray-200 border-collapse">
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
                className={`px-4 py-3 text-sm font-medium tracking-wider text-left text-gray-900 uppercase border-b border-gray-200 first:rounded-tl last:rounded-tr`}
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
                <td className={`px-4 py-3 text-gray-900 border-b border-gray-200`}>{children}</td>
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
                  <td className={`px-4 py-3 text-gray-900 border-b border-gray-200`}>{children}</td>
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
                <td className={`px-4 py-3 text-gray-900 border-b border-gray-200`}>{children}</td>
              );
            }

            return (
              <td className={`px-4 py-3 text-gray-900 border-b border-gray-200`}>
                <span className="inline-flex flex-wrap gap-1 items-center">
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
              <span className="inline-flex flex-wrap gap-1 items-center">
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
