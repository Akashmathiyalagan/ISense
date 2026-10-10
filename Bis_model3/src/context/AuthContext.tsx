import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, UserRole } from '../types/user';
import { authApi, LoginPayload, RegisterPayload } from '../services/authApi';
import { mockUser } from '../data/mockData';

interface AuthContextType {
  currentUser: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authError: string | null;
  login: (credentials: LoginPayload) => Promise<boolean>;
  register: (payload: RegisterPayload) => Promise<boolean>;
  logout: () => void;
  updateProfile: (updatedData: Partial<User>) => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    // Check local storage for persistent session
    const checkAuth = async () => {
      try {
        const storedToken = localStorage.getItem('isense_auth_token');
        const storedUser = localStorage.getItem('isense_user');
        
        if (storedToken && storedUser) {
          setCurrentUser(JSON.parse(storedUser));
        } else {
          // If no stored token, user is unauthenticated
          setCurrentUser(null);
        }
      } catch {
        setCurrentUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (credentials: LoginPayload): Promise<boolean> => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const response = await authApi.login(credentials);
      localStorage.setItem('isense_auth_token', response.token);
      localStorage.setItem('isense_user', JSON.stringify(response.user));
      setCurrentUser(response.user);
      return true;
    } catch (err: any) {
      setAuthError(err.message || 'Authentication failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterPayload): Promise<boolean> => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const response = await authApi.register(payload);
      localStorage.setItem('isense_auth_token', response.token);
      localStorage.setItem('isense_user', JSON.stringify(response.user));
      setCurrentUser(response.user);
      return true;
    } catch (err: any) {
      setAuthError(err.message || 'Registration failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('isense_auth_token');
    localStorage.removeItem('isense_user');
    setCurrentUser(null);
  };

  const updateProfile = (updatedData: Partial<User>) => {
    if (currentUser) {
      const updated = { ...currentUser, ...updatedData };
      setCurrentUser(updated);
      localStorage.setItem('isense_user', JSON.stringify(updated));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        isAuthenticated: !!currentUser,
        isLoading,
        authError,
        login,
        register,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
