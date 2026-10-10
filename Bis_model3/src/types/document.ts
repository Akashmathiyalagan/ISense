export type DocumentStatusType = 'Uploaded' | 'Pending' | 'Under Validation' | 'Missing';

export interface DocumentItem {
  id: string;
  applicationId: string;
  name: string;
  category: string;
  status: DocumentStatusType;
  uploadedAt?: string;
  fileName?: string;
  fileSize?: string;
  fileType?: string;
  verificationNote?: string;
  isRequired: boolean;
}
