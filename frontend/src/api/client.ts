import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s — LLM calls can be slow
});

// Response interceptor: surface user-friendly errors as toasts
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';

    // Don't toast on 404 — callers handle those
    if (error.response?.status !== 404) {
      toast.error(message, { duration: 5000 });
    }

    return Promise.reject(error);
  }
);

export default apiClient;
