import React, { useEffect, useState } from 'react';
import { RefreshCw, FileText, Plus, Menu } from 'lucide-react';
import apiClient from '../../api/client';

interface HeaderProps {
  documentCount: number;
  onNewChat: () => void;
  activeDocCount: number;
  onToggleMobileSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  documentCount,
  onNewChat,
  activeDocCount,
  onToggleMobileSidebar,
}) => {
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'degraded' | 'checking'>('checking');

  const checkHealth = async () => {
    try {
      const res = await apiClient.get<{ status: string }>('/health');
      setHealthStatus(res.data.status === 'healthy' ? 'healthy' : 'degraded');
    } catch {
      setHealthStatus('degraded');
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 border-b border-surface-700/80 bg-surface-900/95 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 shrink-0">
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Mobile menu toggle */}
        {onToggleMobileSidebar && (
          <button
            type="button"
            onClick={onToggleMobileSidebar}
            className="md:hidden text-gray-400 hover:text-gray-100 p-1.5 rounded-md hover:bg-surface-800 transition-colors"
            title="Toggle navigation"
            aria-label="Toggle navigation"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}

        {/* Brand identity */}
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-surface-800 border border-surface-700 flex items-center justify-center text-brand-500 shadow-subtle shrink-0">
            {/* Geometric document intelligence emblem */}
            <svg
              className="w-4 h-4"
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
              <path d="M9 17h4" />
              <circle cx="16" cy="16" r="1.5" className="fill-brand-500 stroke-none" />
            </svg>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="font-semibold text-gray-100 text-sm tracking-tight">
              OpsPilot
            </span>
            <span className="text-[11px] text-gray-400 font-normal hidden sm:inline-block">
              AI Document Intelligence Assistant
            </span>
          </div>
        </div>

        {/* Document count metadata */}
        <div className="hidden lg:flex items-center gap-2 ml-2 pl-3 border-l border-surface-700/80 text-xs text-gray-400">
          <FileText className="w-3.5 h-3.5 text-gray-500" />
          <span>
            {documentCount} {documentCount === 1 ? 'document' : 'documents'} indexed
          </span>
          {activeDocCount > 0 && activeDocCount < documentCount && (
            <span className="px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 text-[11px] font-mono border border-brand-500/20">
              {activeDocCount} active in scope
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2.5">
        {/* System Health */}
        <div
          title={healthStatus === 'healthy' ? 'Connected to Supabase & Qdrant Cloud' : 'Degraded connection'}
          className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-surface-850 border border-surface-700/80"
        >
          {healthStatus === 'healthy' ? (
            <>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-gray-300 text-[11px] font-medium hidden xs:inline-block">System Online</span>
            </>
          ) : healthStatus === 'degraded' ? (
            <>
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              <span className="text-amber-300 text-[11px] font-medium hidden xs:inline-block">Degraded</span>
            </>
          ) : (
            <>
              <RefreshCw className="w-2.5 h-2.5 text-gray-400 animate-spin" />
              <span className="text-gray-400 text-[11px]">Connecting</span>
            </>
          )}
        </div>

        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5"
        >
          <Plus className="w-3.5 h-3.5 text-surface-950 stroke-[2.5]" />
          <span>New Chat</span>
        </button>
      </div>
    </header>
  );
};
