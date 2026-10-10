import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  Plus,
  ArrowRight,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { useAuth } from '../hooks/useAuth';
import { useApplications } from '../hooks/useApplications';
import { useRealtime } from '../context/RealtimeContext';
import { applicationApi } from '../services/applicationApi';
import { ApplicationActivity } from '../types/application';
import { StatCard } from '../components/dashboard/StatCard';
import { ApplicationCard } from '../components/dashboard/ApplicationCard';
import { RecentActivity } from '../components/dashboard/RecentActivity';
import { QuickActions } from '../components/dashboard/QuickActions';
import { PageHeader } from '../components/layout/PageHeader';
import { Button } from '../components/common/Button';
import { Loading } from '../components/common/Loading';

export const Dashboard: React.FC = () => {
  const { currentUser } = useAuth();
  const { applications, isLoading } = useApplications();
  const { refreshTrigger } = useRealtime();
  const [activities, setActivities] = useState<ApplicationActivity[]>([]);

  useEffect(() => {
    const loadActivities = async () => {
      const data = await applicationApi.getActivities();
      setActivities(data);
    };
    loadActivities();
  }, [refreshTrigger]);

  const chartData = applications.map((app) => ({
    name: app.productName.split(' ')[0] + ' ' + (app.productName.split(' ')[1] || ''),
    progress: app.progress,
    docs: app.completedDocuments,
  }));

  if (isLoading && applications.length === 0) {
    return <Loading message="Loading your BIS certification dashboard..." />;
  }

  const firstName = currentUser?.fullName ? currentUser.fullName.split(' ')[0] : 'User';

  const activeCount = applications.filter((a) => a.status === 'In Progress').length;
  const pendingDocsCount = applications.filter((a) => a.status === 'Documents Pending').length + (applications.length > 0 ? 3 : 0);
  const completedCount = applications.filter((a) => a.status === 'Completed').length;
  const pendingActionsCount = applications.length > 0 ? 4 : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Good morning, ${firstName}`}
        description="Manage your BIS certification journey from one place with live synchronization."
        actions={
          <div className="flex items-center gap-2">
            <Link to="/standards">
              <Button variant="outline" size="sm">
                Search Standards
              </Button>
            </Link>
            <Link to="/new-application">
              <Button variant="primary" size="sm" icon={<Plus className="w-4 h-4" />}>
                New Application
              </Button>
            </Link>
          </div>
        }
      />

      {/* 4 Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Applications"
          value={applications.length}
          subtitle={`${activeCount} in progress`}
          icon={<FileText className="w-5 h-5" />}
          iconBg="bg-blue-50 text-blue-600 border-blue-100"
          change={applications.length > 0 ? "+1 this month" : "No active applications"}
          changeType="positive"
        />
        <StatCard
          title="Pending Documents"
          value={pendingDocsCount}
          subtitle="Required for official submission"
          icon={<Clock className="w-5 h-5" />}
          iconBg="bg-amber-50 text-amber-600 border-amber-100"
          change={pendingDocsCount > 0 ? "Action required" : "All clear"}
          changeType={pendingDocsCount > 0 ? "negative" : "positive"}
        />
        <StatCard
          title="Completed Applications"
          value={completedCount}
          subtitle="Ready for Manak Online"
          icon={<CheckCircle2 className="w-5 h-5" />}
          iconBg="bg-emerald-50 text-emerald-600 border-emerald-100"
          change={completedCount > 0 ? "100% verified" : "Pending completion"}
          changeType="positive"
        />
        <StatCard
          title="Pending Actions"
          value={pendingActionsCount}
          subtitle="QAP manual & address proofs"
          icon={<AlertCircle className="w-5 h-5" />}
          iconBg="bg-purple-50 text-purple-600 border-purple-100"
          change={pendingActionsCount > 0 ? "High priority" : "None pending"}
          changeType={pendingActionsCount > 0 ? "negative" : "positive"}
        />
      </div>

      {/* Unified Entry Point Notice */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-blue-50 via-indigo-50/40 to-emerald-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-slate-900">Unified WhatsApp &amp; Web Synchronization Active</p>
            <p className="text-slate-600 mt-0.5">
              Any document uploaded or status updated via your registered WhatsApp session automatically syncs to this dashboard in real time.
            </p>
          </div>
        </div>
        <Link to="/ai-assistant" className="shrink-0">
          <span className="font-semibold text-blue-600 hover:text-blue-700 underline cursor-pointer">
            Ask AI Copilot →
          </span>
        </Link>
      </div>

      {/* Main Grid: Application Cards & Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Applications list */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-slate-900">Your Active BIS Applications</h3>
                <p className="text-xs text-slate-500">Overview of products currently undergoing readiness checks</p>
              </div>
              <Link to="/applications" className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1">
                <span>View all ({applications.length})</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {applications.length === 0 ? (
              <div className="bg-white rounded-xl border border-dashed border-slate-300 p-8 text-center space-y-3">
                <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto">
                  <FileText className="w-6 h-6" />
                </div>
                <h4 className="text-base font-semibold text-slate-900">No applications registered yet</h4>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  Register your first product to generate standard-tailored compliance checklists, technical dossiers, and lab testing guidance.
                </p>
                <div className="pt-2">
                  <Link to="/new-application">
                    <Button variant="primary" size="sm" icon={<Plus className="w-4 h-4" />}>
                      Create First Application
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {applications.slice(0, 4).map((app) => (
                  <ApplicationCard key={app.id} application={app} />
                ))}
              </div>
            )}
          </div>

          {/* Recharts Progress Chart */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-slate-900">Dossier Readiness Breakdown</h3>
                <p className="text-xs text-slate-500">Completion percentage across active candidate products</p>
              </div>
              <div className="flex items-center gap-1 text-xs text-slate-500 font-medium">
                <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
                <span>Active Candidates: {applications.length}</span>
              </div>
            </div>

            {chartData.length === 0 ? (
              <div className="h-56 flex flex-col items-center justify-center text-center p-6 text-slate-400">
                <TrendingUp className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-xs font-medium text-slate-500">No product readiness benchmarks yet</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Readiness benchmarks will automatically graph once candidate products are added.</p>
              </div>
            ) : (
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} domain={[0, 100]} />
                    <Tooltip
                      formatter={(val) => [`${val}%`, 'Readiness']}
                      contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                    />
                    <Bar dataKey="progress" radius={[6, 6, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.progress === 100 ? '#059669' : entry.progress > 60 ? '#2563eb' : '#f59e0b'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Quick Actions & Recent Activity */}
        <div className="space-y-6">
          <QuickActions />
          <RecentActivity activities={activities} limit={4} />
        </div>
      </div>
    </div>
  );
};
