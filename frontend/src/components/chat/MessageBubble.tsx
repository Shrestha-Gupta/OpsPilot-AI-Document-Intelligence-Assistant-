import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, User } from 'lucide-react';
import { SourceCitations } from './SourceCitations';
import type { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isAssistant = message.role === 'assistant';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`flex items-start gap-3 py-3 px-3.5 sm:px-4 rounded-xl transition-all duration-150 ${
        isAssistant
          ? 'bg-surface-850/90 border border-surface-700/80 shadow-subtle'
          : 'bg-surface-800 border border-surface-700/90 ml-auto max-w-[90%] sm:max-w-[80%]'
      }`}
    >
      {/* Avatar Icon */}
      <div
        className={`w-6 h-6 rounded-md flex items-center justify-center shrink-0 mt-0.5 border ${
          isAssistant
            ? 'bg-surface-900 border-surface-700 text-brand-400'
            : 'bg-surface-750 border-surface-650 text-gray-400'
        }`}
      >
        {isAssistant ? (
          <svg
            className="w-3.5 h-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="4" y="4" width="16" height="16" rx="2" />
            <path d="M9 9h6" />
            <path d="M9 13h6" />
            <circle cx="16" cy="16" r="1.5" className="fill-brand-500 stroke-none" />
          </svg>
        ) : (
          <User className="w-3.5 h-3.5" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        {/* Message Header */}
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-gray-200">
              {isAssistant ? 'OpsPilot' : 'You'}
            </span>
            {isAssistant && (
              <span className="text-[10px] font-mono text-brand-400/80">
                Assistant
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {isAssistant && (
              <button
                type="button"
                onClick={handleCopy}
                className="text-gray-400 hover:text-gray-200 text-xs flex items-center gap-1 transition-colors"
                title="Copy response"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-400" />
                    <span className="text-[10px] text-emerald-400 font-mono">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3 text-gray-500 hover:text-gray-300" />
                    <span className="text-[10px] text-gray-400">Copy</span>
                  </>
                )}
              </button>
            )}
            <span className="text-[10px] font-mono text-gray-500">
              {new Date(message.created_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
        </div>

        {/* Content Body */}
        <div className="prose prose-invert max-w-none text-xs sm:text-sm text-gray-200 leading-relaxed break-words">
          {isAssistant ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus as any}
                      language={match[1]}
                      PreTag="div"
                      className="rounded-md text-xs my-2 !bg-surface-950 border border-surface-700/80"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code
                      className="bg-surface-900 border border-surface-700/70 text-amber-200/90 px-1.5 py-0.5 rounded font-mono text-[11px]"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
                ul: ({ children }) => (
                  <ul className="list-disc list-outside pl-5 space-y-1 my-2 text-gray-300">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-outside pl-5 space-y-1 my-2 text-gray-300">{children}</ol>
                ),
                li: ({ children }) => <li className="pl-0.5">{children}</li>,
                p: ({ children }) => <p className="mb-2.5 last:mb-0 text-gray-200">{children}</p>,
                strong: ({ children }) => (
                  <strong className="font-semibold text-gray-100">{children}</strong>
                ),
                h2: ({ children }) => (
                  <h2 className="font-semibold text-gray-100 text-sm sm:text-base mt-4 mb-2 tracking-tight">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="font-semibold text-gray-100 text-xs sm:text-sm mt-3 mb-1.5 tracking-tight">{children}</h3>
                ),
                h4: ({ children }) => (
                  <h4 className="font-medium text-gray-200 text-xs mt-2.5 mb-1">{children}</h4>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-brand-500/70 bg-surface-900/60 pl-3 py-1 my-2 text-gray-300 italic rounded-r">
                    {children}
                  </blockquote>
                ),
                hr: () => <hr className="my-3 border-surface-700" />,
                table: ({ children }) => (
                  <div className="my-3 overflow-x-auto rounded-lg border border-surface-700 bg-surface-900/70">
                    <table className="w-full min-w-[500px] text-left text-xs border-collapse">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead className="bg-surface-800 text-gray-100 border-b border-surface-700 font-semibold">{children}</thead>
                ),
                tbody: ({ children }) => (
                  <tbody className="divide-y divide-surface-800">{children}</tbody>
                ),
                tr: ({ children }) => <tr className="align-top hover:bg-surface-800/40 transition-colors">{children}</tr>,
                th: ({ children }) => (
                  <th className="px-3 py-2 font-semibold text-gray-200 whitespace-nowrap">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="px-3 py-2 align-top text-gray-300">{children}</td>
                ),
                a: ({ children, href }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noreferrer"
                    className="text-brand-400 hover:text-brand-300 underline underline-offset-2 transition-colors"
                  >
                    {children}
                  </a>
                ),
              }}
            >
              {message.content.replace(/(?:<br\s*\/?\s*>|&lt;br\s*\/?\s*&gt;)/gi, ' · ')}
            </ReactMarkdown>
          ) : (
            <p className="whitespace-pre-wrap text-gray-100">{message.content}</p>
          )}
        </div>

        {/* Citations Footer */}
        {isAssistant && message.sources && message.sources.length > 0 && (
          <SourceCitations sources={message.sources} />
        )}
      </div>
    </div>
  );
};
