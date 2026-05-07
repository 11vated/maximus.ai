import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { type ThemeConfig } from '../types/theme';

interface MarkdownRendererProps {
  content: string;
  theme: ThemeConfig;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, theme }) => {
  return (
    <div
      className="prose prose-sm max-w-none"
      style={{
        color: theme.foreground,
        '--tw-prose-body': theme.foreground,
        '--tw-prose-headings': theme.primary,
        '--tw-prose-links': theme.accent,
        '--tw-prose-code': theme.primary,
      } as React.CSSProperties}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Custom code block rendering
          pre: ({ children, ...props }) => (
            <pre
              {...props}
              className="rounded-lg p-4 overflow-x-auto my-2 text-sm"
              style={{
                background: theme.background + '80',
                border: `1px solid ${theme.primary}40`,
              }}
            >
              {children}
            </pre>
          ),
          code: ({ children, className, ...props }) => {
            const isInline = !className?.includes('language-');
            return isInline ? (
              <code
                {...props}
                className="px-1 py-0.5 rounded text-sm"
                style={{
                  background: theme.primary + '20',
                  color: theme.primary,
                }}
              >
                {children}
              </code>
            ) : (
              <code {...props} className={className}>
                {children}
              </code>
            );
          },
          h1: ({ children }) => (
            <h1 className="text-lg font-bold mt-4 mb-2" style={{ color: theme.primary }}>
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-md font-bold mt-3 mb-2" style={{ color: theme.primary }}>
              {children}
            </h2>
          ),
          a: ({ children, href }) => (
            <a
              href={href}
              className="hover:underline"
              style={{ color: theme.accent }}
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table
                className="min-w-full border-collapse"
                style={{ borderColor: theme.primary + '40' }}
              >
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th
              className="px-3 py-2 text-left text-sm font-bold"
              style={{
                background: theme.primary + '20',
                color: theme.primary,
                borderBottom: `2px solid ${theme.primary}40`,
              }}
            >
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td
              className="px-3 py-2 text-sm"
              style={{
                borderBottom: `1px solid ${theme.primary}20`,
              }}
            >
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
