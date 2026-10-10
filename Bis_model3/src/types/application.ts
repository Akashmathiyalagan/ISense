export type ApplicationStatusType = 
  | 'In Progress' 
  | 'Documents Pending' 
  | 'Under Review' 
  | 'Completed' 
  | 'Draft';

export interface ApplicationRequirement {
  id: string;
  applicationId: string;
  title: string;
  description: string;
  status: 'completed' | 'pending' | 'in_progress';
  source: string;
  actionLabel?: string;
  sectionRef?: string;
}

export interface ApplicationTimelineStep {
  stepNumber: number;
  title: string;
  description: string;
  status: 'completed' | 'current' | 'upcoming';
  date?: string;
}

export interface ApplicationActivity {
  id: string;
  applicationId: string;
  title: string;
  description: string;
  timestamp: string;
  type: 'status_change' | 'document_upload' | 'ai_query' | 'system';
  actor: string;
}

export interface BISStandard {
  id: string;
  isNumber: string;
  title: string;
  description: string;
  source: string;
  category: string;
  relevantSections: string[];
  mandatoryStatus: string;
  lastUpdated: string;
}

export interface Application {
  id: string;
  productName: string;
  productCategory: string;
  manufacturer: string;
  countryOfOrigin: string;
  description: string;
  applicantName: string;
  applicantEmail?: string;
  status: ApplicationStatusType;
  progress: number;
  currentStage: string;
  standardCode?: string;
  standardTitle?: string;
  totalDocuments: number;
  completedDocuments: number;
  createdAt: string;
  updatedAt: string;
  requirementsCount: {
    total: number;
    completed: number;
  };
}
