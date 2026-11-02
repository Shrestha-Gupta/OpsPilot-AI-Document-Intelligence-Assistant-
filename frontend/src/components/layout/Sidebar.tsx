import React, { useState, useCallback } from 'react';
import {
  Files,
  MessageSquare,
  Trash2,
  Plus,
  ChevronLeft,
  ChevronRight,
  Clock,
  X,
} from 'lucide-react';
import { DocumentList } from '../documents/DocumentList';
import type { Document, Conversation } from '../../types';

interface SidebarProps {
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

  conversations: Conversation[];
  activeConvId: string | null;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => Promise<void>;
  onNewChat: () => void;

  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

const MIN_SIDEBAR_WIDTH = 280;
const DEFAULT_SIDEBAR_WIDTH = 340;
const MAX_SIDEBAR_WIDTH = 420;

export const Sidebar: React.FC<SidebarProps> = ({
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

  conversations,
  activeConvId,
  onSelectConversation,
  onDeleteConversation,
  onNewChat,

  mobileOpen = false,
  onCloseMobile,
}) => {
  const [activeTab, setActiveTab] = useState<'documents' | 'conversations'>('documents');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('opspilot_sidebar_width');
      if (saved) {
        const parsed = parseInt(saved, 10);
        if (!isNaN(parsed) && parsed >= MIN_SIDEBAR_WIDTH && parsed <= MAX_SIDEBAR_WIDTH) {
          return parsed;
        }
      }
    } catch {
      // Ignore
    }
    return DEFAULT_SIDEBAR_WIDTH;
  });
  const [isResizing, setIsResizing] = useState(false);

  const startResizing = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    const startX = e.clientX;
    const startWidth = sidebarWidth;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const delta = moveEvent.clientX - startX;
      const newWidth = Math.min(MAX_SIDEBAR_WIDTH, Math.max(MIN_SIDEBAR_WIDTH, startWidth + delta));
      setSidebarWidth(newWidth);
    };

    const onMouseUp = (upEvent: MouseEvent) => {
      const delta = upEvent.clientX - startX;
      const finalWidth = Math.min(MAX_SIDEBAR_WIDTH, Math.max(MIN_SIDEBAR_WIDTH, startWidth + delta));
      try {
        localStorage.setItem('opspilot_sidebar_width', String(finalWidth));
      } catch {
        // Ignore
      }
      setIsResizing(false);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      document.body.style.removeProperty('cursor');
      document.body.style.removeProperty('user-select');
    };

    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }, [sidebarWidth]);

  const sidebarContent = (
    <div className="h-full flex flex-col bg-surface-850">
      {/* Top Header & Segmented Tab Switcher */}
      <div className="h-14 border-b border-surface-700/80 flex items-center justify-between px-3 shrink-0">
        {!isCollapsed && (
          <div className="flex items-center gap-1 bg-surface-900/90 p-1 rounded-md border border-surface-700/80 w-full mr-2">
            <button
              type="button"
              onClick={() => setActiveTab('documents')}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1 px-2 rounded text-xs font-medium transition-all ${
                activeTab === 'documents'
                  ? 'bg-surface-800 text-gray-100 shadow-sm border border-surface-700/70'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Files className={`w-3.5 h-3.5 ${activeTab === 'documents' ? 'text-brand-400' : 'text-gray-400'}`} />
              <span>Documents</span>
              <span
                className={`text-[10px] font-mono px-1.5 py-0.2 rounded transition-colors ${
                  activeTab === 'documents'
                    ? 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                    : 'bg-surface-800 text-gray-400'
                }`}
              >
                {documents.length}
              </span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('conversations')}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1 px-2 rounded text-xs font-medium transition-all ${
                activeTab === 'conversations'
                  ? 'bg-surface-800 text-gray-100 shadow-sm border border-surface-700/70'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <MessageSquare className={`w-3.5 h-3.5 ${activeTab === 'conversations' ? 'text-brand-400' : 'text-gray-400'}`} />
              <span>Chats</span>
              <span
                className={`text-[10px] font-mono px-1.5 py-0.2 rounded transition-colors ${
                  activeTab === 'conversations'
                    ? 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                    : 'bg-surface-800 text-gray-400'
                }`}
              >
                {conversations.length}
              </span>
            </button>
          </div>
        )}

        {/* Mobile close button / Desktop collapse button */}
        <div className="flex items-center">
          {onCloseMobile && (
            <button
              type="button"
              onClick={onCloseMobile}
              className="md:hidden text-gray-400 hover:text-gray-200 p-1.5 rounded-md hover:bg-surface-750 transition-colors"
              title="Close navigation"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <button
            type="button"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden md:inline-flex text-gray-400 hover:text-gray-200 p-1.5 rounded-md hover:bg-surface-750 transition-colors"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Main Body */}
      {isCollapsed ? (
        <div className="flex flex-col items-center py-4 space-y-3">
          <button
            type="button"
            onClick={() => {
              setIsCollapsed(false);
              setActiveTab('documents');
            }}
            title={`Documents (${documents.length})`}
            className={`p-2 rounded-md transition-colors ${
              activeTab === 'documents'
                ? 'bg-surface-800 text-brand-400 border border-surface-700'
                : 'text-gray-400 hover:bg-surface-800 hover:text-gray-200'
            }`}
          >
            <Files className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => {
              setIsCollapsed(false);
              setActiveTab('conversations');
            }}
            title={`Chats (${conversations.length})`}
            className={`p-2 rounded-md transition-colors ${
              activeTab === 'conversations'
                ? 'bg-surface-800 text-brand-400 border border-surface-700'
                : 'text-gray-400 hover:bg-surface-800 hover:text-gray-200'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <div className="flex-1 overflow-hidden p-3 flex flex-col">
          {activeTab === 'documents' ? (
            <DocumentList
              documents={documents}
              selectedDocIds={selectedDocIds}
              onToggleSelect={onToggleSelect}
              onSelectAll={onSelectAll}
              onDeselectAll={onDeselectAll}
              onDeleteDocument={onDeleteDocument}
              onUploadFiles={onUploadFiles}
              isUploading={isUploading}
              uploadProgress={uploadProgress}
              onAskAboutDoc={onAskAboutDoc}
            />
          ) : (
            <div className="flex flex-col h-full space-y-3">
              <button
                type="button"
                onClick={() => {
                  onNewChat();
                  if (onCloseMobile) onCloseMobile();
                }}
                className="btn-secondary w-full justify-center text-xs py-2 shadow-subtle"
              >
                <Plus className="w-3.5 h-3.5 text-brand-500" />
                <span>New Conversation</span>
              </button>

              <div className="flex-1 overflow-y-auto space-y-1 pr-1">
                {conversations.length === 0 ? (
                  <div className="py-12 text-center text-gray-500">
                    <Clock className="w-5 h-5 mx-auto mb-2 opacity-30 text-gray-400" />
                    <p className="text-xs text-gray-400 font-medium">No conversations yet</p>
                    <p className="text-[11px] text-gray-500 mt-1 max-w-[200px] mx-auto">
                      Ask questions across your documents to begin a thread.
                    </p>
                  </div>
                ) : (
                  conversations.map((conv) => (
                    <div
                      key={conv.id}
                      onClick={() => {
                        onSelectConversation(conv.id);
                        if (onCloseMobile) onCloseMobile();
                      }}
                      className={`group flex items-center justify-between p-2.5 rounded-lg border text-xs cursor-pointer transition-all ${
                        activeConvId === conv.id
                          ? 'bg-surface-800 border-surface-600/90 text-gray-100 font-medium shadow-subtle border-l-2 border-l-brand-500'
                          : 'bg-transparent border-transparent text-gray-400 hover:text-gray-200 hover:bg-surface-800/60'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate flex-1 min-w-0 mr-2">
                        <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${activeConvId === conv.id ? 'text-brand-400' : 'text-gray-500'}`} />
                        <span className="truncate">{conv.title || 'Untitled Conversation'}</span>
                      </div>

                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteConversation(conv.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-rose-400 p-1 rounded hover:bg-surface-700 transition-all"
                        title="Delete conversation"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        style={!isCollapsed ? { width: `${sidebarWidth}px` } : undefined}
        className={`hidden md:flex h-full border-r border-surface-700/80 bg-surface-850 flex-col relative z-20 shrink-0 ${
          isCollapsed ? 'w-14' : ''
        } ${isResizing ? 'select-none transition-none' : 'transition-[width] duration-150'}`}
      >
        {sidebarContent}

        {/* Horizontal Resize Drag Handle */}
        {!isCollapsed && (
          <div
            onMouseDown={startResizing}
            className={`absolute top-0 right-0 -mr-1 w-2 h-full cursor-col-resize z-30 group flex items-center justify-center transition-colors ${
              isResizing ? 'bg-brand-500/40' : 'hover:bg-brand-500/20'
            }`}
            title="Drag to resize sidebar (280px – 420px)"
          >
            <div
              className={`w-0.5 h-8 rounded-full transition-all ${
                isResizing
                  ? 'bg-brand-400 opacity-100 h-16'
                  : 'bg-surface-500/40 opacity-0 group-hover:opacity-100 group-hover:bg-brand-400/80'
              }`}
            />
          </div>
        )}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
            onClick={onCloseMobile}
          />
          <aside className="relative w-80 max-w-[85vw] h-full bg-surface-850 shadow-2xl flex flex-col z-10 border-r border-surface-700">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
};
