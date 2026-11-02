import React, { useRef, useEffect } from 'react';
import { Trash2, Search, Split, FileCheck } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { ChatInput } from './ChatInput';
import { SuggestedQuestions } from './SuggestedQuestions';
import type { Message } from '../../types';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (question: string) => void;
  onClearChat: () => void;
  suggestedQuestions: string[];
  totalReadyDocs: number;
  scopedCount: number;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onClearChat,
  suggestedQuestions,
  totalReadyDocs,
  scopedCount,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-full bg-surface-900 relative">
      {/* Messages Header Bar (when messages exist) */}
      {messages.length > 0 && (
        <div className="h-10 border-b border-surface-700/70 px-6 flex items-center justify-between bg-surface-850/50 text-xs text-gray-400 shrink-0">
          <span className="font-mono text-[11px] text-gray-400">
            {messages.length} {messages.length === 1 ? 'message' : 'messages'} in thread
          </span>
          <button
            type="button"
            onClick={onClearChat}
            className="text-gray-400 hover:text-rose-400 flex items-center gap-1.5 transition-colors text-xs"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Thread</span>
          </button>
        </div>
      )}

      {/* Messages Feed Area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-8 py-6 space-y-4">
        <div className="max-w-3xl xl:max-w-4xl mx-auto w-full space-y-4">
          {messages.length === 0 ? (
            <div className="py-6 sm:py-10 flex flex-col items-center text-center space-y-6 max-w-2xl mx-auto">
              {/* Brand Intelligence Emblem */}
              <div className="w-10 h-10 rounded-lg bg-surface-800 border border-surface-700 flex items-center justify-center text-brand-500 shadow-subtle">
                <svg
                  className="w-5 h-5"
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

              <div className="space-y-1 max-w-md">
                <h2 className="text-xl sm:text-2xl font-semibold text-gray-100 tracking-tight">
                  OpsPilot
                </h2>
                <p className="text-xs sm:text-sm font-medium text-brand-400 tracking-wide">
                  AI Document Intelligence Assistant
                </p>
                <p className="text-xs text-gray-400 pt-0.5 leading-relaxed">
                  Conversational intelligence over your internal document repository. Ask questions, compare viewpoints, and trace answers back to verified source pages.
                </p>
              </div>

              {/* Enterprise Core Workflows */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 w-full text-left pt-1">
                <div className="p-3 rounded-lg bg-surface-850/80 border border-surface-700/80 hover:border-surface-600 transition-colors">
                  <div className="w-5 h-5 rounded bg-surface-800 border border-surface-700 flex items-center justify-center text-gray-300 mb-2">
                    <Search className="w-3 h-3 text-brand-400" />
                  </div>
                  <h4 className="text-xs font-semibold text-gray-200">Ask Documents</h4>
                  <p className="text-[11px] text-gray-400 mt-0.5 leading-relaxed">
                    Search across single or multiple PDFs with grounded retrieval and zero hallucination.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-surface-850/80 border border-surface-700/80 hover:border-surface-600 transition-colors">
                  <div className="w-5 h-5 rounded bg-surface-800 border border-surface-700 flex items-center justify-center text-gray-300 mb-2">
                    <Split className="w-3 h-3 text-brand-400" />
                  </div>
                  <h4 className="text-xs font-semibold text-gray-200">Compare Information</h4>
                  <p className="text-[11px] text-gray-400 mt-0.5 leading-relaxed">
                    Analyze cross-document similarities, differences, and structured tabular summaries.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-surface-850/80 border border-surface-700/80 hover:border-surface-600 transition-colors">
                  <div className="w-5 h-5 rounded bg-surface-800 border border-surface-700 flex items-center justify-center text-gray-300 mb-2">
                    <FileCheck className="w-3 h-3 text-brand-400" />
                  </div>
                  <h4 className="text-xs font-semibold text-gray-200">Verify Evidence</h4>
                  <p className="text-[11px] text-gray-400 mt-0.5 leading-relaxed">
                    Every answer is strictly supported by exact document page citations and verbatim excerpts.
                  </p>
                </div>
              </div>

              {/* Sample Questions */}
              {suggestedQuestions.length > 0 && (
                <div className="w-full text-left pt-1">
                  <SuggestedQuestions
                    questions={suggestedQuestions}
                    onSelectQuestion={onSendMessage}
                    title="Suggested inquiries"
                  />
                </div>
              )}
            </div>
          ) : (
            messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
          )}

          {/* Typing indicator */}
          {isLoading && <TypingIndicator />}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Fixed Chat Input Bar */}
      <div className="p-4 sm:p-6 bg-surface-900 border-t border-surface-700/70 shrink-0">
        <div className="max-w-3xl xl:max-w-4xl mx-auto">
          <ChatInput
            onSendMessage={onSendMessage}
            isLoading={isLoading}
            disabled={totalReadyDocs === 0}
            scopedCount={scopedCount}
            totalReadyDocs={totalReadyDocs}
          />
        </div>
      </div>
    </div>
  );
};
