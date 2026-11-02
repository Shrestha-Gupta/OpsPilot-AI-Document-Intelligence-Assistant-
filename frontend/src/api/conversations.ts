import apiClient from './client';
import type { Conversation, ConversationWithMessages, ChatResponse } from '../types';

export const conversationsApi = {
  list: async (): Promise<Conversation[]> => {
    const res = await apiClient.get<Conversation[]>('/api/v1/conversations');
    return res.data;
  },

  create: async (title?: string): Promise<Conversation> => {
    const res = await apiClient.post<Conversation>('/api/v1/conversations', { title });
    return res.data;
  },

  get: async (convId: string): Promise<ConversationWithMessages> => {
    const res = await apiClient.get<ConversationWithMessages>(`/api/v1/conversations/${convId}`);
    return res.data;
  },

  delete: async (convId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/conversations/${convId}`);
  },

  clearMessages: async (convId: string): Promise<void> => {
    await apiClient.post(`/api/v1/conversations/${convId}/clear`);
  },

  chat: async (
    convId: string,
    question: string,
    document_ids?: string[]
  ): Promise<ChatResponse> => {
    const res = await apiClient.post<ChatResponse>(
      `/api/v1/conversations/${convId}/chat`,
      { question, document_ids }
    );
    return res.data;
  },
};
