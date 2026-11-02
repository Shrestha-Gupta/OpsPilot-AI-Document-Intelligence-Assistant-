import React from 'react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex items-center gap-3 py-2.5 px-3.5 rounded-xl bg-surface-850/90 border border-surface-700/80 shadow-subtle w-fit max-w-md">
      <div className="w-6 h-6 rounded-md bg-surface-900 border border-surface-700 text-brand-400 flex items-center justify-center shrink-0">
        <svg
          className="w-3.5 h-3.5 animate-pulse"
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
      </div>

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce [animation-delay:-0.3s]" />
          <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce [animation-delay:-0.15s]" />
          <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce" />
        </div>
        <span className="text-xs text-gray-400 font-mono text-[11px]">
          Searching documents & synthesizing response...
        </span>
      </div>
    </div>
  );
};
