import React, { useState } from 'react';
import {
  Trash2,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Check,
} from 'lucide-react';
import type { Document } from '../../types';

interface DocumentItemProps {
  document: Document;
  isSelected: boolean;
  onToggleSelect: (id: string) => void;
  onDelete: (id: string) => Promise<void>;
  onAskAboutDoc?: (id: string) => void;
}

const formatBytes = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export const DocumentItem: React.FC<DocumentItemProps> = ({
  document,
  isSelected,
  onToggleSelect,
  onDelete,
  onAskAboutDoc,
}) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!showConfirm) {
      setShowConfirm(true);
      return;
    }
    setIsDeleting(true);
    try {
      await onDelete(document.id);
    } finally {
      setIsDeleting(false);
      setShowConfirm(false);
    }
  };

  const isReady = document.status === 'ready';

  return (
    <div
      onClick={() => isReady && onToggleSelect(document.id)}
      className={`group relative p-3 rounded-lg border transition-all duration-150 select-none ${
        isReady ? 'cursor-pointer' : 'cursor-default opacity-85'
      } ${
        isSelected
          ? 'bg-surface-800 border-brand-500/40 shadow-subtle'
          : 'bg-surface-850/80 hover:bg-surface-800 border-surface-700/70 hover:border-surface-600'
      }`}
    >
      <div className="flex items-start gap-2.5">
        {/* Custom Scoped Checkbox */}
        <div
          onClick={(e) => {
            if (!isReady) return;
            e.stopPropagation();
            onToggleSelect(document.id);
          }}
          className={`w-4 h-4 rounded mt-0.5 flex items-center justify-center shrink-0 transition-colors ${
            !isReady
              ? 'opacity-30 border border-surface-600 bg-surface-900 cursor-not-allowed'
              : isSelected
              ? 'bg-brand-500 border border-brand-400 text-surface-950 cursor-pointer'
              : 'border border-surface-600 bg-surface-900 hover:border-surface-500 cursor-pointer'
          }`}
          title={isReady ? (isSelected ? 'Remove from chat scope' : 'Include in chat scope') : 'Document indexing in progress'}
        >
          {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
        </div>

        {/* Content Body */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <h4
              title={document.original_name}
              className="text-xs font-medium text-gray-200 truncate group-hover:text-gray-100 transition-colors"
            >
              {document.original_name}
            </h4>

            {/* Semantic status badge */}
            {document.status === 'processing' && (
              <span className="badge badge-processing shrink-0">
                <Loader2 className="w-2.5 h-2.5 animate-spin" />
                <span>Processing</span>
              </span>
            )}
            {document.status === 'ready' && (
              <span className="badge badge-ready shrink-0">
                <CheckCircle2 className="w-2.5 h-2.5" />
                <span>Ready</span>
              </span>
            )}
            {document.status === 'failed' && (
              <span className="badge badge-failed shrink-0" title={document.error_msg || 'Failed'}>
                <AlertCircle className="w-2.5 h-2.5" />
                <span>Failed</span>
              </span>
            )}
            {document.status === 'uploading' && (
              <span className="badge badge-uploading shrink-0">
                <Loader2 className="w-2.5 h-2.5 animate-spin" />
                <span>Uploading</span>
              </span>
            )}
          </div>

          {/* Metadata Row: pages • chunks • file size */}
          <div className="flex items-center gap-1.5 text-[11px] text-gray-400 font-mono">
            <span>{formatBytes(document.size_bytes)}</span>
            {document.page_count !== null && (
              <>
                <span className="text-gray-600">•</span>
                <span>{document.page_count} {document.page_count === 1 ? 'page' : 'pages'}</span>
              </>
            )}
            {document.chunk_count !== null && (
              <>
                <span className="text-gray-600">•</span>
                <span>{document.chunk_count} chunks</span>
              </>
            )}
          </div>

          {/* Failure message preview if error */}
          {document.status === 'failed' && document.error_msg && (
            <p className="mt-1.5 text-[10px] text-rose-400 line-clamp-2 bg-rose-500/10 p-1.5 rounded border border-rose-500/20">
              {document.error_msg}
            </p>
          )}

          {/* Bottom Card Actions */}
          <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-surface-700/50">
            {isReady && onAskAboutDoc ? (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onAskAboutDoc(document.id);
                }}
                className="text-[11px] text-brand-400 hover:text-brand-300 flex items-center gap-1 font-medium transition-colors"
              >
                <Sparkles className="w-3 h-3 text-brand-400" />
                <span>Suggest Questions</span>
              </button>
            ) : (
              <span />
            )}

            <div className="flex items-center gap-1">
              {showConfirm ? (
                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    onClick={handleDelete}
                    disabled={isDeleting}
                    className="text-[10px] bg-rose-600 hover:bg-rose-500 text-white px-2 py-0.5 rounded transition-colors font-medium"
                  >
                    {isDeleting ? 'Deleting...' : 'Confirm'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowConfirm(false)}
                    className="text-[10px] text-gray-400 hover:text-gray-200 px-1.5 py-0.5 rounded hover:bg-surface-700 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  title="Delete document"
                  onClick={handleDelete}
                  className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-rose-400 p-1 rounded hover:bg-surface-750 transition-all"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
