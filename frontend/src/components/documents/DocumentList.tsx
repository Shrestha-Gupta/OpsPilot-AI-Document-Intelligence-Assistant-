import React, { useState } from 'react';
import { Search, CheckSquare, Square, FileText } from 'lucide-react';
import { DocumentItem } from './DocumentItem';
import { UploadZone } from './UploadZone';
import type { Document } from '../../types';

interface DocumentListProps {
  documents: Document[];
  selectedDocIds: string[];
  onToggleSelect: (id: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onDeleteDocument: (id: string) => Promise<void>;
  onUploadFiles: (files: File[]) => Promise<void>;
  isUploading: boolean;
  uploadProgress: number;
  onAskAboutDoc?: (id: string) => void;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  selectedDocIds,
  onToggleSelect,
  onSelectAll,
  onDeselectAll,
  onDeleteDocument,
  onUploadFiles,
  isUploading,
  uploadProgress,
  onAskAboutDoc,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const readyDocs = documents.filter((d) => d.status === 'ready');
  const filteredDocs = documents.filter((d) =>
    d.original_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const areAllSelected =
    readyDocs.length > 0 && readyDocs.every((d) => selectedDocIds.includes(d.id));

  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Upload Zone */}
      <UploadZone
        onUpload={onUploadFiles}
        isUploading={isUploading}
        uploadProgress={uploadProgress}
      />

      {/* Filter and Selection Header */}
      {documents.length > 0 && (
        <div className="space-y-2">
          {/* Search bar */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Filter by name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface-900 border border-surface-700 rounded-md pl-8 pr-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-500/80 transition-colors"
            />
          </div>

          {/* Scope Controls */}
          {readyDocs.length > 0 && (
            <div className="flex items-center justify-between text-xs px-0.5 text-gray-400">
              <span className="text-[11px] font-mono">
                {selectedDocIds.length === 0 || selectedDocIds.length === readyDocs.length
                  ? `All ${readyDocs.length} in chat scope`
                  : `${selectedDocIds.length} of ${readyDocs.length} in scope`}
              </span>
              <button
                type="button"
                onClick={areAllSelected ? onDeselectAll : onSelectAll}
                className="text-[11px] text-brand-400 hover:text-brand-300 flex items-center gap-1 font-medium transition-colors"
              >
                {areAllSelected ? (
                  <>
                    <Square className="w-3 h-3 text-brand-400" />
                    <span>Deselect All</span>
                  </>
                ) : (
                  <>
                    <CheckSquare className="w-3 h-3 text-brand-400" />
                    <span>Select All</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Document Items Scrollable List */}
      <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
        {documents.length === 0 ? (
          <div className="py-10 text-center text-gray-500">
            <FileText className="w-6 h-6 mx-auto mb-2 opacity-30 text-gray-400" />
            <p className="text-xs text-gray-300 font-medium">No documents yet</p>
            <p className="text-[11px] text-gray-500 mt-1 max-w-[220px] mx-auto leading-relaxed">
              Upload your first PDF to start asking questions across your document collection.
            </p>
          </div>
        ) : filteredDocs.length === 0 ? (
          <p className="text-xs text-center py-6 text-gray-500 font-mono">
            No documents matching "{searchQuery}"
          </p>
        ) : (
          filteredDocs.map((doc) => (
            <DocumentItem
              key={doc.id}
              document={doc}
              isSelected={selectedDocIds.includes(doc.id)}
              onToggleSelect={onToggleSelect}
              onDelete={onDeleteDocument}
              onAskAboutDoc={onAskAboutDoc}
            />
          ))
        )}
      </div>
    </div>
  );
};
