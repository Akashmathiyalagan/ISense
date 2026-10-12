import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

export interface RealtimeEvent {
  type: 'application_created' | 'document_uploaded' | 'document_deleted' | 'document_updated' | 'chat_message' | 'requirement_updated' | 'user_registered' | 'connected';
  data?: any;
  timestamp: string;
}

export interface ToastMessage {
  id: string;
  title: string;
  description: string;
  type: 'success' | 'info' | 'warning';
  timestamp: string;
}

interface RealtimeContextType {
  isConnected: boolean;
  lastEvent: RealtimeEvent | null;
  toasts: ToastMessage[];
  dismissToast: (id: string) => void;
  triggerManualRefresh: () => void;
  refreshTrigger: number;
}

const RealtimeContext = createContext<RealtimeContextType | undefined>(undefined);

export const RealtimeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  const addToast = (title: string, description: string, type: 'success' | 'info' | 'warning' = 'info') => {
    const newToast: ToastMessage = {
      id: `toast-${Date.now()}-${Math.random()}`,
      title,
      description,
      type,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };
    setToasts(prev => [newToast, ...prev.slice(0, 4)]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== newToast.id));
    }, 5000);
  };

  const dismissToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const triggerManualRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
    let eventSource: EventSource | null = null;
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const setupSSE = () => {
      try {
        eventSource = new EventSource(`${apiBase}/api/events`);

        eventSource.onopen = () => {
          setIsConnected(true);
        };

        eventSource.onmessage = (e) => {
          try {
            const parsed = JSON.parse(e.data);
            handleIncomingEvent(parsed);
          } catch {
            // raw text event
          }
        };

        eventSource.onerror = () => {
          setIsConnected(false);
          eventSource?.close();
          // Fallback to WebSocket or reconnect
          reconnectTimeout = setTimeout(setupWebSocket, 3000);
        };
      } catch {
        setupWebSocket();
      }
    };

    const setupWebSocket = () => {
      try {
        const wsUrl = apiBase.replace(/^http/, 'ws') + '/ws/live';
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (e) => {
          try {
            const parsed = JSON.parse(e.data);
            handleIncomingEvent(parsed);
          } catch {
            // raw message
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          reconnectTimeout = setTimeout(setupSSE, 4000);
        };

        ws.onerror = () => {
          setIsConnected(false);
        };
      } catch {
        setIsConnected(false);
      }
    };

    const handleIncomingEvent = (event: any) => {
      setLastEvent(event);
      setRefreshTrigger(prev => prev + 1);

      switch (event.type) {
        case 'application_created':
          addToast(
            'New Application Synced',
            `Dossier for ${event.data?.application?.productName || 'Product'} created & synced across Web & WhatsApp.`,
            'success'
          );
          break;
        case 'document_uploaded':
          addToast(
            'Real-Time Document Check',
            `${event.data?.document?.name || 'File'} uploaded. Readiness progress updated.`,
            'info'
          );
          break;
        case 'document_deleted':
          addToast(
            'Document Removed',
            'Dossier index recalculated.',
            'warning'
          );
          break;
        case 'chat_message':
          addToast(
            'RAG Assistant Response',
            'Knowledge base clauses retrieved & cited in session.',
            'info'
          );
          break;
        case 'requirement_updated':
          addToast(
            'Requirement Verified',
            `Checklist item updated for ${event.data?.applicationId}.`,
            'success'
          );
          break;
        default:
          break;
      }
    };

    setupSSE();

    return () => {
      if (eventSource) eventSource.close();
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  return (
    <RealtimeContext.Provider
      value={{
        isConnected,
        lastEvent,
        toasts,
        dismissToast,
        triggerManualRefresh,
        refreshTrigger,
      }}
    >
      {children}
    </RealtimeContext.Provider>
  );
};

export const useRealtime = (): RealtimeContextType => {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return context;
};
