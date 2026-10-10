import { useState, useEffect, useCallback } from 'react';
import { ChatMessageItem } from '../types/ai';
import { aiApi } from '../services/aiApi';
import { handleApiError } from '../services/api';

export const useAIChat = (applicationId?: string) => {
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await aiApi.getChatHistory();
        setMessages(history);
      } catch (err) {
        setError(handleApiError(err));
      }
    };
    loadHistory();
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isSending) return;

    const userMessage: ChatMessageItem = {
      id: `usr-msg-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsSending(true);
    setError(null);

    try {
      const response = await aiApi.sendMessage({
        message: content.trim(),
        applicationId,
      });
      setMessages(prev => [...prev, response]);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setIsSending(false);
    }
  }, [applicationId, isSending]);

  const clearChat = useCallback(async () => {
    await aiApi.clearHistory();
    const history = await aiApi.getChatHistory();
    setMessages(history);
  }, []);

  return {
    messages,
    isSending,
    error,
    sendMessage,
    clearChat,
  };
};
