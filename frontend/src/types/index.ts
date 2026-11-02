// Document types
export type DocumentStatus = 'uploading' | 'processing' | 'ready' | 'failed';

export interface Document {
  id: string;
  name: string;
  original_name: string;
  size_bytes: number;
  page_count: number | null;
  chunk_count: number | null;
  status: DocumentStatus;
  error_msg: string | null;
  created_at: string;
  updated_at: string;
}

// Conversation types
export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

// Message / Source types
export interface Source {
  document_id: string;
  document_name: string;
  page_number: number;
  chunk_text?: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: Source[] | null;
  created_at: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

// API response types
export interface UploadResponse {
  documents: Document[];
  message: string;
}

export interface ChatRequest {
  question: string;
}

export interface ChatResponse {
  message_id: string;
  conversation_id: string;
  answer: string;
  sources: Source[];
  created_at: string;
}

// Generic API error
export interface ApiError {
  error: string;
  message: string;
}
