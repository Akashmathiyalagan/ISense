import { apiClient } from './api';
import { DocumentItem, DocumentStatusType } from '../types/document';
import { mockDocuments } from '../data/mockData';

let activeDocuments: DocumentItem[] = [...mockDocuments];

export const documentApi = {
  getDocuments: async (applicationId?: string): Promise<DocumentItem[]> => {
    try {
      const url = applicationId ? `/api/applications/${applicationId}/documents` : '/api/documents';
      const response = await apiClient.get<DocumentItem[]>(url);
      return response.data;
    } catch {
      if (applicationId) {
        return activeDocuments.filter(d => d.applicationId.toLowerCase() === applicationId.toLowerCase());
      }
      return [...activeDocuments];
    }
  },

  uploadDocument: async (
    applicationId: string, 
    file: File, 
    category: string
  ): Promise<DocumentItem> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('applicationId', applicationId);
    formData.append('category', category);

    try {
      const response = await apiClient.post<DocumentItem>('/api/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    } catch {
      // Graceful fallback for mock demo
      const newDoc: DocumentItem = {
        id: `doc-${Date.now()}`,
        applicationId: applicationId || 'APP-001',
        name: file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' '),
        category: category || 'Product Specification',
        status: 'Under Validation',
        uploadedAt: new Date().toISOString(),
        fileName: file.name,
        fileSize: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        fileType: file.type || 'application/pdf',
        verificationNote: 'Document information check: Under review. Format and schema match expected structure.',
        isRequired: true,
      };

      activeDocuments = [newDoc, ...activeDocuments];
      return newDoc;
    }
  },

  updateDocumentStatus: async (
    docId: string, 
    status: DocumentStatusType, 
    note?: string
  ): Promise<DocumentItem | null> => {
    try {
      const response = await apiClient.patch<DocumentItem>(`/api/documents/${docId}`, { status, note });
      return response.data;
    } catch {
      const idx = activeDocuments.findIndex(d => d.id === docId);
      if (idx !== -1) {
        activeDocuments[idx] = {
          ...activeDocuments[idx],
          status,
          verificationNote: note || activeDocuments[idx].verificationNote,
        };
        return activeDocuments[idx];
      }
      return null;
    }
  },

  deleteDocument: async (docId: string): Promise<boolean> => {
    try {
      await apiClient.delete(`/api/documents/${docId}`);
      return true;
    } catch {
      activeDocuments = activeDocuments.filter(d => d.id !== docId);
      return true;
    }
  },
};
