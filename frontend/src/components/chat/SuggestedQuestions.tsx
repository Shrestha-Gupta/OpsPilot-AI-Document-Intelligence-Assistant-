import React from 'react';
import { Sparkles } from 'lucide-react';

interface SuggestedQuestionsProps {
  questions: string[];
  onSelectQuestion: (question: string) => void;
  title?: string;
}

export const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({
  questions,
  onSelectQuestion,
  title = 'Suggested questions',
}) => {
  if (!questions || questions.length === 0) return null;

  return (
    <div className="w-full">
      <div className="flex items-center gap-1.5 text-xs text-gray-400 font-medium mb-2.5">
        <Sparkles className="w-3.5 h-3.5 text-brand-400" />
        <span>{title}</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {questions.map((q, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSelectQuestion(q)}
            className="text-left text-xs bg-surface-850 hover:bg-surface-800 text-gray-300 hover:text-gray-100 px-3 py-1.5 rounded-md border border-surface-700/80 hover:border-surface-600 transition-all duration-150 shadow-subtle hover:shadow-card"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
};
