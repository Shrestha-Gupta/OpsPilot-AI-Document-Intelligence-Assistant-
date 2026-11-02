import React, { useState } from 'react';
import { BookMarked, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import type { Source } from '../../types';

interface SourceCitationsProps {
  sources: Source[];
}

export const SourceCitations: React.FC<SourceCitationsProps> = ({ sources }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 pt-2.5 border-t border-surface-700/60">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left py-1 text-xs text-brand-400/90 hover:text-brand-300 transition-colors group select-none"
      >
        <div className="flex items-center gap-1.5 font-medium">
          <BookMarked className="w-3.5 h-3.5 text-brand-400" />
          <span>
            {sources.length} {sources.length === 1 ? 'Source Citation' : 'Source Citations'}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-3.5 h-3.5 text-gray-500 group-hover:text-gray-300 transition-transform" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-gray-500 group-hover:text-gray-300 transition-transform" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2">
          {sources.map((source, idx) => (
            <div
              key={`${source.document_id}-${source.page_number}-${idx}`}
              className="p-2.5 rounded-lg bg-surface-900/80 border border-surface-700/80 text-xs"
            >
              <div className="flex items-center justify-between mb-1 text-gray-200 font-medium">
                <div className="flex items-center gap-1.5 truncate">
                  <FileText className="w-3 h-3 text-brand-400 shrink-0" />
                  <span className="truncate">{source.document_name}</span>
                </div>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-800 text-gray-300 border border-surface-700 shrink-0 ml-2">
                  Page {source.page_number}
                </span>
              </div>
              {source.chunk_text && (
                <p className="text-[11px] text-gray-400 line-clamp-3 italic mt-1 bg-surface-950/60 p-2 rounded border border-surface-800/80 leading-relaxed font-sans">
                  "{source.chunk_text}"
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
