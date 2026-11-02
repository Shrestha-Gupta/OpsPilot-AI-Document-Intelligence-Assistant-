import apiClient from './client';
import type { Document, UploadResponse } from '../types';

export const documentsApi = {
  list: async (): Promise<Document[]> => {
    const res = await apiClient.get<Document[]>('/api/v1/documents');
    return res.data;
  },

  upload: async (
    files: File[],
    onUploadProgress?: (percent: number) => void
  ): Promise<UploadResponse> => {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    const res = await apiClient.post<UploadResponse>('/api/v1/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onUploadProgress) {
          onUploadProgress(Math.round((e.loaded / e.total) * 100));
        }
      },
    });
    return res.data;
  },

  getStatus: async (docId: string): Promise<Document> => {
    const res = await apiClient.get<Document>(`/api/v1/documents/${docId}`);
    return res.data;
  },

  delete: async (docId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/documents/${docId}`);
  },

  getSuggestions: async (docId: string): Promise<string[]> => {
    const res = await apiClient.get<{ suggestions: string[] }>(`/api/v1/documents/${docId}/suggestions`);
    return res.data.suggestions;
  },
};
