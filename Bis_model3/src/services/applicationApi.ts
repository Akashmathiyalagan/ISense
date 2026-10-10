import { apiClient } from './api';
import { 
  Application, 
  ApplicationRequirement, 
  BISStandard, 
  ApplicationActivity 
} from '../types/application';
import { 
  mockApplications, 
  mockRequirements, 
  mockBISStandards, 
  mockActivities 
} from '../data/mockData';
import { detectProductStandard } from '../utils/bisMatcher';

// In-memory state store for dynamic updates during session
let activeApplications: Application[] = [...mockApplications];
const activeRequirements: Record<string, ApplicationRequirement[]> = { ...mockRequirements };
let activeActivities: ApplicationActivity[] = [...mockActivities];

export const applicationApi = {
  getApplications: async (): Promise<Application[]> => {
    try {
      const response = await apiClient.get<Application[]>('/api/applications');
      return response.data;
    } catch {
      // Offline fallback: isolate per current user
      const stored = localStorage.getItem('isense_user');
      if (stored) {
        try {
          const user = JSON.parse(stored);
          const userEmail = (user.email || '').toLowerCase();
          return activeApplications.filter(
            (a) =>
              (a.applicantEmail && a.applicantEmail.toLowerCase() === userEmail) ||
              (a as any).userId === user.id
          );
        } catch {}
      }
      return [];
    }
  },

  getApplicationById: async (id: string): Promise<Application | null> => {
    try {
      const response = await apiClient.get<Application>(`/api/applications/${id}`);
      return response.data;
    } catch (err: any) {
      if (err.response?.status === 403 || err.response?.status === 404) {
        return null;
      }
      const stored = localStorage.getItem('isense_user');
      if (stored) {
        try {
          const user = JSON.parse(stored);
          const userEmail = (user.email || '').toLowerCase();
          const app = activeApplications.find(
            a => a.id.toLowerCase() === id.toLowerCase() &&
                 ((a.applicantEmail && a.applicantEmail.toLowerCase() === userEmail) || (a as any).userId === user.id)
          );
          return app || null;
        } catch {}
      }
      return null;
    }
  },

  createApplication: async (payload: {
    productName: string;
    productCategory: string;
    manufacturer: string;
    countryOfOrigin: string;
    description: string;
    standardCode?: string;
    standardTitle?: string;
    applicantName?: string;
    applicantEmail?: string;
  }): Promise<Application> => {
    const stored = localStorage.getItem('isense_user');
    let userDetails = { name: 'Registered Applicant', email: 'applicant@isense.gov.in', org: payload.manufacturer, id: 'usr-guest' };
    if (stored) {
      try {
        const u = JSON.parse(stored);
        userDetails = {
          name: u.fullName || userDetails.name,
          email: u.email || userDetails.email,
          org: u.organisation || payload.manufacturer,
          id: u.id || userDetails.id
        };
      } catch {}
    }
    const fullPayload = {
      ...payload,
      manufacturer: payload.manufacturer || userDetails.org,
      applicantName: payload.applicantName || userDetails.name,
      applicantEmail: payload.applicantEmail || userDetails.email,
    };
    try {
      const response = await apiClient.post<Application>('/api/applications', fullPayload);
      return response.data;
    } catch {
      const newAppId = `APP-00${activeApplications.length + 1}`;
      const detectedFallback = detectProductStandard(payload.productName, payload.productCategory);
      const newApp: Application = {
        id: newAppId,
        productName: payload.productName,
        productCategory: payload.productCategory,
        manufacturer: fullPayload.manufacturer,
        countryOfOrigin: payload.countryOfOrigin,
        description: payload.description,
        applicantName: userDetails.name,
        applicantEmail: userDetails.email,
        status: 'In Progress',
        progress: 25,
        currentStage: 'Requirements & Document Compilation',
        standardCode: payload.standardCode || detectedFallback.standardCode,
        standardTitle: payload.standardTitle || detectedFallback.standardTitle,
        totalDocuments: 8,
        completedDocuments: 1,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        requirementsCount: {
          total: 8,
          completed: 2,
        },
      };

      activeApplications = [newApp, ...activeApplications];
      
      // Initialize requirements for new application
      activeRequirements[newAppId] = [
        {
          id: `req-${newAppId}-1`,
          applicationId: newAppId,
          title: 'Product Technical Data Sheet',
          description: 'Basic electrical and dimensional specifications.',
          status: 'completed',
          source: 'Configured BIS Knowledge Base Schema',
          sectionRef: 'Section 1.1',
        },
        {
          id: `req-${newAppId}-2`,
          applicationId: newAppId,
          title: 'Manufacturer Incorporation Documents',
          description: 'Factory registration proof and tax registration.',
          status: 'completed',
          source: 'Configured BIS Knowledge Base Guidelines',
          sectionRef: 'Section 2.1',
        },
        {
          id: `req-${newAppId}-3`,
          applicationId: newAppId,
          title: 'Laboratory Safety Test Report',
          description: 'Testing from BIS recognized testing house.',
          status: 'pending',
          source: 'Configured BIS Knowledge Base Safety Standard',
          sectionRef: 'Clause 4',
        },
        {
          id: `req-${newAppId}-4`,
          applicationId: newAppId,
          title: 'Factory Quality Management System',
          description: 'Production control and sample inspection manual.',
          status: 'pending',
          source: 'Configured BIS Quality Scheme',
          sectionRef: 'Clause 6',
        },
      ];

      // Add activity
      activeActivities.unshift({
        id: `act-${Date.now()}`,
        applicationId: newAppId,
        title: 'Application Created',
        description: `Created new BIS assistance record for ${payload.productName}.`,
        timestamp: 'Just now',
        type: 'status_change',
        actor: 'Rajesh Sharma',
      });

      return newApp;
    }
  },

  getRequirements: async (applicationId: string): Promise<ApplicationRequirement[]> => {
    try {
      const response = await apiClient.get<ApplicationRequirement[]>(`/api/applications/${applicationId}/requirements`);
      return response.data;
    } catch {
      return activeRequirements[applicationId] || activeRequirements['APP-001'] || [];
    }
  },

  getActivities: async (applicationId?: string): Promise<ApplicationActivity[]> => {
    try {
      const url = applicationId ? `/api/applications/${applicationId}/activity` : '/api/activity';
      const response = await apiClient.get<ApplicationActivity[]>(url);
      return response.data;
    } catch {
      if (applicationId) {
        return activeActivities.filter(a => a.applicationId === applicationId);
      }
      return [...activeActivities];
    }
  },

  searchBISStandards: async (query: string): Promise<BISStandard[]> => {
    try {
      const response = await apiClient.get<BISStandard[]>('/api/bis/search', {
        params: { query },
      });
      return response.data;
    } catch {
      if (!query || query.trim() === '') {
        return mockBISStandards;
      }
      const q = query.toLowerCase();
      return mockBISStandards.filter(
        s =>
          s.title.toLowerCase().includes(q) ||
          s.isNumber.toLowerCase().includes(q) ||
          s.category.toLowerCase().includes(q) ||
          s.description.toLowerCase().includes(q)
      );
    }
  },
};
