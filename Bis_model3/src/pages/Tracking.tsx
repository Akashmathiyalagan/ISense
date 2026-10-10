import React, { useState, useEffect } from 'react';
import { Compass, ShieldCheck, CheckCircle2, Clock, AlertCircle, ArrowRight } from 'lucide-react';
import { applicationApi } from '../services/applicationApi';
import { Application } from '../types/application';
import { PageHeader } from '../components/layout/PageHeader';
import { ApplicationTimeline } from '../components/applications/ApplicationTimeline';
import { ProgressBar } from '../components/common/ProgressBar';
import { Badge } from '../components/common/Badge';
import { Loading } from '../components/common/Loading';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { Link } from 'react-router-dom';

export const Tracking: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadApps = async () => {
      setIsLoading(true);
      const data = await applicationApi.getApplications();
      setApplications(data);
      if (data.length > 0) {
        setSelectedAppId(data[0].id);
      }
      setIsLoading(false);
    };
    loadApps();
  }, []);

  const selectedApp = applications.find(a => a.id === selectedAppId) || applications[0];

  if (isLoading && applications.length === 0) {
    return <Loading message="Loading application tracker..." />;
  }

  if (!isLoading && applications.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Application Stage Tracking"
          description="Monitor multi-stage progression from preliminary product identification to official BIS portal readiness."
        />
        <EmptyState
          title="No applications to track yet"
          description="Register a product to track its regulatory milestones, test requirements, and statutory readiness."
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

  return (
    <div className="space-y-6">
      <PageHeader
        title="Application Stage Tracking"
        description="Monitor multi-stage progression from preliminary product identification to official BIS portal readiness."
      />

      {/* Mandatory Statutory Boundary Notice */}
      <div className="p-4 rounded-xl bg-slate-100/90 border border-slate-200 text-xs text-slate-700 flex items-start gap-2.5">
        <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong>Non-Certification Disclaimer:</strong> ISense tracks documentation readiness, preliminary conformity checks, and process workflows. ISense does not grant, certify, or approve BIS applications. Official licenses and CRS registration are issued solely by the Bureau of Indian Standards through statutory evaluation.
        </div>
      </div>

      {/* Product Selector Card */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Select Tracked Product
            </label>
            <select
              value={selectedAppId}
              onChange={(e) => setSelectedAppId(e.target.value)}
              className="font-bold text-slate-900 bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {applications.map((app) => (
                <option key={app.id} value={app.id}>
                  {app.productName} ({app.id}) — {app.status}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500">Current Status:</span>
            <Badge variant={selectedApp?.status === 'Completed' ? 'success' : 'blue'}>
              {selectedApp?.status || 'In Progress'}
            </Badge>
          </div>
        </div>

        {selectedApp && (
          <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-400 block">Application ID:</span>
              <span className="font-mono font-semibold text-slate-800">{selectedApp.id}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Current Milestone:</span>
              <span className="font-semibold text-slate-800">{selectedApp.currentStage}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Standard:</span>
              <span className="font-semibold text-blue-700">{selectedApp.standardCode || 'Standard Pending'}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-1">Overall Readiness:</span>
              <ProgressBar progress={selectedApp.progress} showLabel size="sm" />
            </div>
          </div>
        )}
      </div>

      {/* Detailed Timeline View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ApplicationTimeline
            currentStageIndex={selectedApp?.status === 'Completed' ? 6 : 4}
            totalDocuments={selectedApp?.totalDocuments || 9}
            completedDocuments={selectedApp?.completedDocuments || 7}
          />
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <h4 className="text-sm font-semibold text-slate-900 mb-2">Omni-Channel Status Sync</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              This application is linked with your phone number on WhatsApp. You can query status anytime by messaging:
            </p>
            <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-200 font-mono text-xs text-slate-800">
              "Status of {selectedApp?.id}"
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <h4 className="text-sm font-semibold text-slate-900 mb-2">Next Recommended Milestone</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Upload the Factory Quality Assurance Plan (QAP) to bring your candidate dossier to 89% readiness.
            </p>
            <div className="mt-4">
              <Link
                to={`/applications/${selectedApp?.id || 'APP-001'}`}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <span>Go to Dossier Management</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
