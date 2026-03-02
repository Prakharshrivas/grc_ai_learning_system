import { useCallback, useEffect, useRef, useState } from 'react';
import type { ChatMessage } from '../hooks/useChat';

interface ChatPanelProps {
  messages: ChatMessage[];
  isLoading: boolean;
  suggestions: string[];
  onSend: (question: string) => void;
  onCitationClick: (stepNum: number, startTime: number) => void;
  onSuggestionClick: (question: string) => void;
}

function CitationLink({
  text,
  onClick,
}: {
  text: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-0.5 text-blue-400 hover:text-blue-300 font-mono text-xs bg-blue-500/10 hover:bg-blue-500/20 px-1.5 py-0.5 rounded transition-colors"
    >
      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
          clipRule="evenodd"
        />
      </svg>
      {text}
    </button>
  );
}

function renderMessageContent(
  content: string,
  citations: ChatMessage['citations'],
  onCitationClick: (step: number, time: number) => void,
) {
  if (!citations?.length) {
    return <span className="whitespace-pre-wrap">{content}</span>;
  }

  const citationPattern = /\[STEP\s+(\d+),?\s*([\d:]+)(?:\s*-\s*[\d:]+)?\]/gi;
  const parts: (string | { step: number; text: string; time: number })[] = [];
  let lastIndex = 0;

  for (const match of content.matchAll(citationPattern)) {
    if (match.index != null && match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index));
    }
    const stepNum = parseInt(match[1]);
    const citation = citations.find((c) => c.step === stepNum);
    parts.push({
      step: stepNum,
      text: match[0],
      time: citation?.start_time ?? 0,
    });
    lastIndex = (match.index ?? 0) + match[0].length;
  }
  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return (
    <>
      {parts.map((part, i) =>
        typeof part === 'string' ? (
          <span key={i} className="whitespace-pre-wrap">
            {part}
          </span>
        ) : (
          <CitationLink
            key={i}
            text={part.text}
            onClick={() => onCitationClick(part.step, part.time)}
          />
        ),
      )}
    </>
  );
}

export default function ChatPanel({
  messages,
  isLoading,
  suggestions,
  onSend,
  onCitationClick,
  onSuggestionClick,
}: ChatPanelProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!input.trim() || isLoading) return;
      onSend(input.trim());
      setInput('');
    },
    [input, isLoading, onSend],
  );

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 min-h-0 overflow-y-auto px-4 py-3 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-blue-600/20 rounded-2xl flex items-center justify-center mx-auto mb-3">
              <svg
                className="w-6 h-6 text-blue-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
                />
              </svg>
            </div>
            <p className="text-slate-300 text-sm font-medium">
              Ask me anything about this workflow
            </p>
            <p className="text-slate-500 text-xs mt-1">
              I'll answer from the approved content with video timestamps
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : msg.role === 'system'
                    ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                    : 'bg-slate-800 text-slate-200 border border-slate-700'
              }`}
            >
              {msg.role === 'assistant'
                ? renderMessageContent(msg.content, msg.citations, onCitationClick)
                : msg.content}
              {msg.confidence === 'not_in_source' && (
                <div className="mt-2 text-xs text-amber-400 flex items-center gap-1">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Outside approved content scope
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 border border-slate-700 rounded-2xl px-4 py-3">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {suggestions.length > 0 && messages.length === 0 && (
        <div className="px-4 pb-2">
          <p className="text-slate-500 text-xs mb-1.5">Suggested questions</p>
          <div className="flex flex-wrap gap-1.5">
            {suggestions.slice(0, 4).map((q) => (
              <button
                key={q}
                onClick={() => onSuggestionClick(q)}
                className="text-xs bg-slate-800 text-slate-300 border border-slate-700 rounded-full px-3 py-1.5 hover:bg-slate-700 hover:border-slate-600 transition-colors truncate max-w-[200px]"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="px-4 pb-4 pt-2 border-t border-slate-800">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about this workflow..."
            disabled={isLoading}
            className="flex-1 bg-slate-800 text-slate-200 text-sm rounded-xl px-4 py-2.5 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 placeholder-slate-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="bg-blue-600 text-white rounded-xl px-4 py-2.5 text-sm font-medium hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Ask
          </button>
        </div>
      </form>
    </div>
  );
}
