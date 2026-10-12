export interface SourceReferenceItem {
  id: string;
  title: string;
  documentRef?: string;
  page?: number | string;
  section?: string;
  excerpt?: string;
  sourceUrl?: string;
  verification_status?: string;
  confidence?: number;
}

export interface ChatMessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: SourceReferenceItem[];
  confidence?: number;
  insufficient_evidence?: boolean;
  warnings?: string[];
  provider?: string;
  conversationId?: string;
  status?: string;
}

export interface AIChatRequest {
  message: string;
  applicationId?: string;
  context?: string;
  conversationId?: string;
}
