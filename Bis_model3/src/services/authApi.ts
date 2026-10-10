import { apiClient } from './api';
import { User, AuthResponse, UserRole } from '../types/user';
import { mockUser } from '../data/mockData';

export interface LoginPayload {
  email: string;
  password?: string;
  isWhatsAppLogin?: boolean;
}

export interface RegisterPayload {
  fullName: string;
  email: string;
  phone?: string;
  password?: string;
  confirmPassword?: string;
  userType: UserRole;
  organisation?: string;
}

export const authApi = {
  login: async (credentials: LoginPayload): Promise<AuthResponse> => {
    try {
      const response = await apiClient.post<AuthResponse>('/api/auth/login', credentials);
      return response.data;
    } catch (err: any) {
      if (err.response?.data?.detail) {
        throw new Error(err.response.data.detail);
      }
      if (err.code === 'ERR_NETWORK') {
        // Fallback for purely offline environment
        const simulatedUser: User = {
          ...mockUser,
          email: credentials.email || mockUser.email,
        };
        return {
          user: simulatedUser,
          token: 'isense_mock_jwt_token_' + Date.now(),
        };
      }
      throw new Error(err.message || 'Authentication failed');
    }
  },

  register: async (payload: RegisterPayload): Promise<AuthResponse> => {
    try {
      const response = await apiClient.post<AuthResponse>('/api/auth/register', payload);
      return response.data;
    } catch (err: any) {
      if (err.response?.data?.detail) {
        throw new Error(err.response.data.detail);
      }
      if (err.code === 'ERR_NETWORK') {
        const newUser: User = {
          id: 'usr-' + Math.floor(1000 + Math.random() * 9000),
          fullName: payload.fullName,
          email: payload.email,
          phone: payload.phone,
          userType: payload.userType,
          organisation: payload.organisation || 'Independent Applicant',
          createdAt: new Date().toISOString(),
        };
        return {
          user: newUser,
          token: 'isense_mock_jwt_token_' + Date.now(),
        };
      }
      throw new Error(err.message || 'Registration failed');
    }
  },

  getCurrentUser: async (): Promise<User | null> => {
    try {
      const response = await apiClient.get<User>('/api/auth/me');
      return response.data;
    } catch {
      const stored = localStorage.getItem('isense_user');
      if (stored) {
        try {
          return JSON.parse(stored);
        } catch {
          return mockUser;
        }
      }
      return mockUser;
    }
  },
};
