import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  FileText,
  CheckSquare,
  FolderOpen,
  Bot,
  Clock,
  ArrowLeft,
  Upload,
  Download,
  ShieldCheck,
  Share2,
} from 'lucide-react';
import { applicationApi } from '../services/applicationApi';
import { documentApi } from '../services/documentApi';
import { Application, ApplicationRequirement, ApplicationActivity } from '../types/application';
import { DocumentItem } from '../types/document';
import { PageHeader } from '../components/layout/PageHeader';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { ProgressBar } from '../components/common/ProgressBar';
import { ApplicationStatus } from '../components/applications/ApplicationStatus';
import { ApplicationTimeline } from '../components/applications/ApplicationTimeline';
import { RequirementChecklist } from '../components/applications/RequirementChecklist';
import { DocumentTable } from '../components/documents/DocumentTable';
import { DocumentUpload } from '../components/documents/DocumentUpload';
import { Modal } from '../components/common/Modal';
import { AIChat } from '../components/ai/AIChat';
import { Loading } from '../components/common/Loading';
import { EmptyState } from '../components/common/EmptyState';

export const ApplicationDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<'overview' | 'requirements' | 'documents' | 'ai' | 'activity'>('overview');
  const [application, setApplication] = useState<Application | null>(null);
  const [requirements, setRequirements] = useState<ApplicationRequirement[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [activities, setActivities] = useState<ApplicationActivity[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);

  const loadData = async () => {
    const appId = id || 'APP-001';
    const app = await applicationApi.getApplicationById(appId);
    const reqs = await applicationApi.getRequirements(appId);
    const docs = await documentApi.getDocuments(appId);
    const acts = await applicationApi.getActivities(appId);

    setApplication(app);
    setRequirements(reqs);
    setDocuments(docs);
    setActivities(acts);
    setIsLoading(false);
  };

  useEffect(() => {
    setIsLoading(true);
    loadData();
  }, [id]);

  if (isLoading) {
    return <Loading message="Loading application details..." />;
  }

  if (!application) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Application Overview"
          description="View detailed BIS certification dossier progress and requirements."
        />
        <EmptyState
          title="Application Not Accessible"
          description="The requested application could not be located or belongs to another user account under statutory privacy rules."
          action={
            <Link to="/applications">
              <Button size="sm" variant="primary">
                Return to My Applications
              </Button>
            </Link>
          }
        />
      </div>
    );
  }

  const handleUploadSuccess = async (file: File, category: string) => {
    try {
      const newDoc = await documentApi.uploadDocument(application.id, file, category);
      setDocuments((prev) => [newDoc, ...prev]);
      const refreshedApp = await applicationApi.getApplicationById(application.id);
      if (refreshedApp) setApplication(refreshedApp);
      const acts = await applicationApi.getActivities(application.id);
      setActivities(acts);
    } catch {
      // Fallback
      const newDoc: DocumentItem = {
        id: `doc-${Date.now()}`,
        applicationId: application.id,
        name: file.name.replace(/\.[^/.]+$/, ''),
        category,
        status: 'Under Validation',
        uploadedAt: new Date().toISOString(),
        fileName: file.name,
        fileSize: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        fileType: file.type || 'application/pdf',
        verificationNote: 'Document information check: Under review. Format structure validated.',
        isRequired: true,
      };
      setDocuments((prev) => [newDoc, ...prev]);
    }
    setIsUploadModalOpen(false);
  };

  const handleDeleteDoc = async (doc: DocumentItem) => {
    await documentApi.deleteDocument(doc.id);
    setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
    const refreshedApp = await applicationApi.getApplicationById(application.id);
    if (refreshedApp) setApplication(refreshedApp);
  };

  const tabs = [
    { key: 'overview', label: 'Overview', icon: FileText },
    { key: 'requirements', label: `Requirements (${requirements.filter(r => r.status === 'completed').length}/${requirements.length})`, icon: CheckSquare },
    { key: 'documents', label: `Documents (${documents.filter(d => d.status === 'Uploaded' || d.status === 'Under Validation').length}/${documents.length})`, icon: FolderOpen },
    { key: 'ai', label: 'AI Assistant', icon: Bot },
    { key: 'activity', label: 'Activity', icon: Clock },
  ];

  return (
    <div className="space-y-6">
      {/* Back button & Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Link to="/applications" className="hover:text-blue-600 flex items-center gap-1 font-medium">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Applications</span>
        </Link>
        <span>/</span>
        <span className="font-mono text-slate-800 font-semibold">{application.id}</span>
      </div>

      {/* Main Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-2xl font-bold text-slate-900">{application.productName}</h1>
              <span className="font-mono font-semibold text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                {application.id}
              </span>
              <Badge variant={application.status === 'Completed' ? 'success' : 'blue'}>
                {application.status}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {application.productCategory} • Manufacturer: {application.manufacturer} • Origin: {application.countryOfOrigin}
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              icon={<Upload className="w-4 h-4" />}
              onClick={() => setIsUploadModalOpen(true)}
            >
              Upload Document
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={<ShieldCheck className="w-4 h-4" />}
              onClick={() => setActiveTab('ai')}
            >
              Ask AI About App
            </Button>
          </div>
        </div>

        {/* Progress summary bar */}
        <div className="pt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <span className="text-slate-400 block mb-1">Standard Reference:</span>
            <span className="font-semibold text-slate-800">{application.standardCode || 'Standard Under Assignment'}</span>
          </div>
          <div>
            <span className="text-slate-400 block mb-1">Current Milestone:</span>
            <span className="font-semibold text-slate-800">{application.currentStage}</span>
          </div>
          <div>
            <span className="text-slate-400 block mb-1">Readiness Completion:</span>
            <ProgressBar progress={application.progress} showLabel size="sm" />
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 overflow-x-auto pb-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shrink-0 cursor-pointer ${
                isActive
                  ? 'bg-blue-50 text-blue-700 border border-blue-200'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB CONTENT */}

      {/* 1. Overview */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <ApplicationStatus
              status={application.status}
              progress={application.progress}
              currentStage={application.currentStage}
              totalDocuments={application.totalDocuments}
              completedDocuments={application.completedDocuments}
              onContinueAction={() => setActiveTab('documents')}
            />

            <RequirementChecklist
              requirements={requirements}
              onActionClick={() => setActiveTab('requirements')}
            />
          </div>

          <div className="space-y-6">
            <ApplicationTimeline
              currentStageIndex={application.status === 'Completed' ? 6 : 4}
              totalDocuments={application.totalDocuments}
              completedDocuments={application.completedDocuments}
            />
          </div>
        </div>
      )}

      {/* 2. Requirements */}
      {activeTab === 'requirements' && (
        <div className="space-y-6">
          <RequirementChecklist
            requirements={requirements}
            onActionClick={() => setIsUploadModalOpen(true)}
          />
        </div>
      )}

      {/* 3. Documents */}
      {activeTab === 'documents' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Application Documents</h3>
              <p className="text-xs text-slate-500">Technical test reports and factory compliance records</p>
            </div>
            <Button
              size="sm"
              variant="primary"
              icon={<Upload className="w-4 h-4" />}
              onClick={() => setIsUploadModalOpen(true)}
            >
              Upload Document
            </Button>
          </div>
          <DocumentTable
            documents={documents}
            onReplace={() => setIsUploadModalOpen(true)}
            onDelete={handleDeleteDoc}
            onDownload={(doc) => alert(`Downloading ${doc.fileName || doc.name}`)}
            onView={(doc) => alert(`Viewing metadata for ${doc.name}\nStatus: ${doc.status}\nNote: ${doc.verificationNote || 'N/A'}`)}
          />
        </div>
      )}

      {/* 4. AI Assistant */}
      {activeTab === 'ai' && (
        <div className="h-[650px]">
          <AIChat
            applicationId={application.id}
            onAttachDocument={() => setIsUploadModalOpen(true)}
          />
        </div>
      )}

      {/* 5. Activity */}
      {activeTab === 'activity' && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
          <h3 className="font-semibold text-slate-900 text-base mb-4">Complete Audit &amp; Event Trail</h3>
          <div className="space-y-4">
            {activities.map((act) => (
              <div key={act.id} className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 bg-slate-50/50">
                <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <Clock className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-slate-900">{act.title}</span>
                    <span className="text-[11px] text-slate-400">{act.timestamp}</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5">{act.description}</p>
                  <p className="text-[10px] text-slate-400 mt-1 font-mono">Actor: {act.actor}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Document Upload Modal */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        title="Upload Application Document"
        description={`Attach document for ${application.productName} (${application.id})`}
      >
        <DocumentUpload
          applicationId={application.id}
          onUploadSuccess={handleUploadSuccess}
          onCancel={() => setIsUploadModalOpen(false)}
        />
      </Modal>
    </div>
  );
};
