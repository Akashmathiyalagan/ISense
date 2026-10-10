import React, { useState, useEffect } from 'react';
import { CheckSquare, ArrowRight, Upload, Filter } from 'lucide-react';
import { applicationApi } from '../services/applicationApi';
import { documentApi } from '../services/documentApi';
import { Application, ApplicationRequirement } from '../types/application';
import { PageHeader } from '../components/layout/PageHeader';
import { RequirementChecklist } from '../components/applications/RequirementChecklist';
import { ProgressBar } from '../components/common/ProgressBar';
import { Loading } from '../components/common/Loading';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { DocumentUpload } from '../components/documents/DocumentUpload';
import { Link } from 'react-router-dom';

export const Requirements: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string>('');
  const [requirements, setRequirements] = useState<ApplicationRequirement[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [uploadModalReq, setUploadModalReq] = useState<ApplicationRequirement | null>(null);

  const loadData = async (appId = selectedAppId) => {
    const apps = await applicationApi.getApplications();
    setApplications(apps);
    if (apps.length === 0) {
      setRequirements([]);
      setIsLoading(false);
      return;
    }
    const currentId = apps.some(a => a.id === appId) ? appId : apps[0].id;
    if (currentId !== selectedAppId) {
      setSelectedAppId(currentId);
    }
    const reqs = await applicationApi.getRequirements(currentId);
    setRequirements(reqs);
    setIsLoading(false);
  };

  useEffect(() => {
    setIsLoading(true);
    loadData(selectedAppId);
  }, [selectedAppId]);

  const selectedApp = applications.find(a => a.id === selectedAppId) || applications[0];
  const completedCount = requirements.filter(r => r.status === 'completed').length;
  const totalCount = requirements.length;
  const percent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  if (isLoading && applications.length === 0) {
    return <Loading message="Loading requirements..." />;
  }

  if (!isLoading && applications.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Requirements & Checklist"
          description="Review standard-specific compliance requirements extracted from the configured BIS knowledge base."
        />
        <EmptyState
          title="No applications registered yet"
          description="Create your first BIS application to generate standard-specific requirement checklists and documentation requirements."
          action={
            <Link to="/new-application">
              <Button size="sm" variant="primary">
                Create First Application
              </Button>
            </Link>
          }
        />
      </div>
    );
  }

  const handleRequirementUpload = async (file: File, category: string) => {
    if (!uploadModalReq) return;
    try {
      await documentApi.uploadDocument(selectedAppId, file, category);
    } catch {
      // Continue locally
    }
    setRequirements(prev =>
      prev.map(r => r.id === uploadModalReq.id ? { ...r, status: 'completed' } : r)
    );
    setUploadModalReq(null);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Requirements &amp; Checklist"
        description="Review standard-specific compliance requirements extracted from the configured BIS knowledge base."
      />

      {/* Application Selector Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Active Application Context
          </label>
          <div className="flex items-center gap-3">
            <select
              value={selectedAppId}
              onChange={(e) => setSelectedAppId(e.target.value)}
              className="font-bold text-slate-900 bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              {applications.map((app) => (
                <option key={app.id} value={app.id}>
                  {app.productName} ({app.id})
                </option>
              ))}
            </select>
            <span className="text-xs text-slate-500 hidden sm:inline">
              Standard: <strong>{selectedApp?.standardCode || 'Standard Pending'}</strong>
            </span>
          </div>
        </div>

        <div className="w-full sm:w-64">
          <ProgressBar progress={percent} showLabel size="md" />
          <p className="text-[11px] text-slate-400 mt-1 text-right">
            {completedCount} of {totalCount} completed
          </p>
        </div>
      </div>

      {/* Main Checklist */}
      <RequirementChecklist
        requirements={requirements}
        onActionClick={(req) => setUploadModalReq(req)}
      />

      {/* Modal for Action / Upload */}
      {uploadModalReq && (
        <Modal
          isOpen={!!uploadModalReq}
          onClose={() => setUploadModalReq(null)}
          title={`Requirement Artifact: ${uploadModalReq.title}`}
          description={`Submit documentation for ${uploadModalReq.source}`}
        >
          <DocumentUpload
            applicationId={selectedAppId}
            initialCategory="Test Report"
            onUploadSuccess={handleRequirementUpload}
            onCancel={() => setUploadModalReq(null)}
          />
        </Modal>
      )}
    </div>
  );
};
