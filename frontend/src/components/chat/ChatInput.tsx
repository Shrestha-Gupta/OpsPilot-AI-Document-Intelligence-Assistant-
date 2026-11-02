import React, { useState, useRef } from 'react';
import { ArrowUp, SlidersHorizontal } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (question: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  scopedCount: number;
  totalReadyDocs: number;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  disabled = false,
  scopedCount,
  totalReadyDocs,
}) => {
  const [question, setQuestion] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!question.trim() || isLoading || disabled) return;
    onSendMessage(question.trim());
    setQuestion('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuestion(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  };

  return (
    <div className="w-full relative">
      {/* Scope banner */}
      <div className="flex items-center justify-between text-[11px] text-gray-500 mb-1 px-1">
        <div className="flex items-center gap-1.5 font-mono">
          <SlidersHorizontal className="w-3 h-3 text-brand-400/90" />
          <span>
            {scopedCount === 0 || scopedCount === totalReadyDocs ? (
              <span>
                Scope: <span className="text-gray-300 font-medium">All {totalReadyDocs} indexed documents</span>
              </span>
            ) : (
              <span>
                Scope: <span className="text-brand-300 font-medium">{scopedCount} of {totalReadyDocs} documents</span>
              </span>
            )}
          </span>
        </div>
        <span className="text-[10px] text-gray-500 hidden sm:inline-block font-sans">
          Return to send • Shift+Return for new line
        </span>
      </div>

      {/* Input container */}
      <div className="relative flex items-end rounded-lg bg-surface-850 border border-surface-700/80 hover:border-surface-600 focus-within:border-brand-500/80 focus-within:ring-2 focus-within:ring-brand-500/15 shadow-subtle transition-all duration-150">
        <textarea
          ref={textareaRef}
          value={question}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          rows={1}
          placeholder={
            totalReadyDocs === 0
              ? 'Upload a PDF to begin querying...'
              : 'Ask a question across your documents...'
          }
          className="w-full bg-transparent text-xs sm:text-sm text-gray-100 placeholder-gray-500 px-3.5 py-3 focus:outline-none resize-none max-h-40 disabled:cursor-not-allowed leading-relaxed font-sans"
        />

        <div className="p-1.5 shrink-0">
          <button
            type="button"
            onClick={() => handleSubmit()}
            disabled={!question.trim() || isLoading || disabled}
            className={`w-7 h-7 rounded-md flex items-center justify-center transition-all duration-150 ${
              question.trim() && !isLoading && !disabled
                ? 'bg-brand-600 hover:bg-brand-500 text-surface-950 shadow-subtle cursor-pointer'
                : 'bg-surface-800 text-gray-600 cursor-not-allowed border border-surface-700/60'
            }`}
            title="Send message"
            aria-label="Send message"
          >
            <ArrowUp className="w-4 h-4 stroke-[2.5]" />
          </button>
        </div>
      </div>
    </div>
  );
};
