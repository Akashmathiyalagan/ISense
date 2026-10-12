import axios, { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('isense_auth_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const storedUser = localStorage.getItem('isense_user');
  if (storedUser && config.headers) {
    try {
      const u = JSON.parse(storedUser);
      if (u.email) config.headers['X-User-Email'] = u.email;
      if (u.id) config.headers['X-User-Id'] = u.id;
    } catch {}
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError<{ message?: string }>;
    if (err.response?.data?.message) {
      return err.response.data.message;
    }
    if (err.code === 'ECONNABORTED' || err.message.includes('Network Error')) {
      return 'Backend service is currently offline or unreachable. Loaded local knowledge base mock data.';
    }
    return err.message;
  }
  return 'An unexpected error occurred while communicating with the server.';
};
