import { useState, useEffect, useCallback } from 'react';
import { Application } from '../types/application';
import { applicationApi } from '../services/applicationApi';
import { handleApiError } from '../services/api';
import { useRealtime } from '../context/RealtimeContext';

export const useApplications = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const { refreshTrigger } = useRealtime();

  const fetchApplications = useCallback(async () => {
    try {
      const data = await applicationApi.getApplications();
      setApplications(data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications, refreshTrigger]);

  const createApplication = async (payload: {
    productName: string;
    productCategory: string;
    manufacturer: string;
    countryOfOrigin: string;
    description: string;
    standardCode?: string;
    standardTitle?: string;
  }) => {
    setIsLoading(true);
    try {
      const newApp = await applicationApi.createApplication(payload);
      setApplications(prev => [newApp, ...prev]);
      return newApp;
    } catch (err) {
      setError(handleApiError(err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    applications,
    isLoading,
    error,
    refreshApplications: fetchApplications,
    createApplication,
  };
};
