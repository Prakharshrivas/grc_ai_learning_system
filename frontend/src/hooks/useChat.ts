import { useCallback, useRef, useState } from 'react';
import { askQuestion, type AskResponse, type Citation } from '../api/client';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: Citation[];
  confidence?: string;
}

export function useChat(workflowId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const sessionIdRef = useRef<string>(crypto.randomUUID());

  const sendMessage = useCallback(
    async (question: string, userRole?: string) => {
      if (!workflowId || !question.trim()) return;

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: question,
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const resp: AskResponse = await askQuestion(
          workflowId,
          question,
          sessionIdRef.current,
          userRole,
        );

        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: resp.answer,
          citations: resp.citations,
          confidence: resp.confidence,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        const errorMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'system',
          content: `Error: ${errorMessage}. Please check that the backend is running and your API keys are configured in .env.`,
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [workflowId],
  );

  const reset = useCallback(() => {
    setMessages([]);
    sessionIdRef.current = crypto.randomUUID();
  }, []);

  return { messages, isLoading, sendMessage, reset, sessionId: sessionIdRef.current };
}
