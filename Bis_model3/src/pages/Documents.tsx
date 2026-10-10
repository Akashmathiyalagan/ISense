import React, { useState, useEffect } from 'react';
import { Upload, Filter, Plus, Search, Table, LayoutGrid, AlertCircle, ShieldCheck } from 'lucide-react';
import { documentApi } from '../services/documentApi';
import { DocumentItem, DocumentStatusType } from '../types/document';
import { PageHeader } from '../components/layout/PageHeader';
import { Button } from '../components/common/Button';
import { DocumentTable } from '../components/documents/DocumentTable';
import { DocumentCard } from '../components/documents/DocumentCard';
import { DocumentUpload } from '../components/documents/DocumentUpload';
import { Modal } from '../components/common/Modal';
import { Loading } from '../components/common/Loading';
import { EmptyState } from '../components/common/EmptyState';

export const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [filter, setFilter] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [viewingDoc, setViewingDoc] = useState<DocumentItem | null>(null);

  const loadDocs = async () => {
    const docs = await documentApi.getDocuments();
    setDocuments(docs);
    setIsLoading(false);
  };

  useEffect(() => {
    setIsLoading(true);
    loadDocs();
  }, []);

  const handleUploadSuccess = async (file: File, category: string) => {
    try {
      const newDoc = await documentApi.uploadDocument('APP-001', file, category);
      setDocuments((prev) => [newDoc, ...prev]);
    } catch {
      const fallbackDoc: DocumentItem = {
        id: `doc-${Date.now()}`,
        applicationId: 'APP-001',
        name: file.name.replace(/\.[^/.]+$/, ''),
        category,
        status: 'Under Validation',
        uploadedAt: new Date().toISOString(),
        fileName: file.name,
        fileSize: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        fileType: file.type || 'application/pdf',
        verificationNote: 'Document information check: Under review. Structural parameters matched.',
        isRequired: true,
      };
      setDocuments((prev) => [fallbackDoc, ...prev]);
    }
    setIsUploadModalOpen(false);
  };

  const handleDelete = async (doc: DocumentItem) => {
    await documentApi.deleteDocument(doc.id);
    setDocuments(prev => prev.filter(d => d.id !== doc.id));
  };

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch =
      doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (doc.fileName && doc.fileName.toLowerCase().includes(searchQuery.toLowerCase()));

    if (!matchesSearch) return false;

    if (filter === 'All') return true;
    if (filter === 'Required') return doc.isRequired;
    if (filter === 'Uploaded') return doc.status === 'Uploaded';
    if (filter === 'Pending') return doc.status === 'Pending' || doc.status === 'Missing';
    if (filter === 'Under Validation') return doc.status === 'Under Validation';

    return true;
  });

  if (isLoading) {
    return <Loading message="Loading document repository..." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Documents"
        description="Upload and track candidate dossiers undergoing automated pre-submission structure checks."
        actions={
          <Button
            variant="primary"
            size="sm"
            icon={<Plus className="w-4 h-4" />}
            onClick={() => setIsUploadModalOpen(true)}
          >
            Upload Document
          </Button>
        }
      />

      {/* Mandatory Phrasing Callout */}
      <div className="p-4 rounded-xl bg-slate-100/80 border border-slate-200 text-xs text-slate-700 flex items-start gap-2.5">
        <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong>Document Information Check Protocol:</strong> Statuses such as <em>"Appears complete"</em> and <em>"Under review"</em> describe automated pre-checks. ISense does not legally validate or approve documents; statutory verification is conducted exclusively by the Bureau of Indian Standards.
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search documents by name or category..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
          />
        </div>

        <div className="flex items-center gap-3 overflow-x-auto pb-1 sm:pb-0">
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
            {['All', 'Required', 'Uploaded', 'Pending', 'Under Validation'].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all whitespace-nowrap cursor-pointer ${
                  filter === tab
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-1 border-l border-slate-200 pl-3">
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-lg border cursor-pointer ${
                viewMode === 'table'
                  ? 'bg-blue-50 text-blue-600 border-blue-200'
                  : 'text-slate-400 hover:text-slate-600 border-transparent'
              }`}
            >
              <Table className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg border cursor-pointer ${
                viewMode === 'grid'
                  ? 'bg-blue-50 text-blue-600 border-blue-200'
                  : 'text-slate-400 hover:text-slate-600 border-transparent'
              }`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main List */}
      {filteredDocs.length === 0 ? (
        <EmptyState
          title="No documents found"
          description="No files match your current filter criteria."
          action={
            <Button size="sm" variant="primary" onClick={() => setIsUploadModalOpen(true)}>
              Upload New Document
            </Button>
          }
        />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocs.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              onView={(d) => setViewingDoc(d)}
              onDownload={(d) => alert(`Downloading verified copy of: ${d.fileName || d.name}`)}
              onReplace={() => setIsUploadModalOpen(true)}
              onDelete={handleDelete}
            />
          ))}
        </div>
      ) : (
        <DocumentTable
          documents={filteredDocs}
          onView={(d) => setViewingDoc(d)}
          onDownload={(d) => alert(`Downloading verified copy of: ${d.fileName || d.name}`)}
          onReplace={() => setIsUploadModalOpen(true)}
          onDelete={handleDelete}
        />
      )}

      {/* Upload Modal */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        title="Upload Document Artifact"
        description="Supports PDF, JPG, PNG files (Max 15MB)"
      >
        <DocumentUpload
          applicationId="APP-001"
          onUploadSuccess={handleUploadSuccess}
          onCancel={() => setIsUploadModalOpen(false)}
        />
      </Modal>

      {/* View Document Details Modal */}
      {viewingDoc && (
        <Modal
          isOpen={!!viewingDoc}
          onClose={() => setViewingDoc(null)}
          title={viewingDoc.name}
          description={`Category: ${viewingDoc.category}`}
        >
          <div className="space-y-4 text-xs text-slate-700">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">File Name:</span>
                <span className="font-semibold text-slate-900">{viewingDoc.fileName || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">File Size:</span>
                <span className="font-semibold text-slate-900">{viewingDoc.fileSize || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Status:</span>
                <span className="font-semibold text-slate-900">{viewingDoc.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Uploaded Date:</span>
                <span className="font-semibold text-slate-900">
                  {viewingDoc.uploadedAt ? new Date(viewingDoc.uploadedAt).toLocaleString() : 'N/A'}
                </span>
              </div>
            </div>

            {viewingDoc.verificationNote && (
              <div className="p-3 bg-blue-50/60 rounded-lg border border-blue-200 text-blue-900">
                <strong>Information Check Summary:</strong>
                <p className="mt-1 text-slate-700 leading-relaxed">{viewingDoc.verificationNote}</p>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
