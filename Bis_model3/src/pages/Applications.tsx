import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Plus, Filter, LayoutGrid, Table, ArrowRight, Shield } from 'lucide-react';
import { useApplications } from '../hooks/useApplications';
import { PageHeader } from '../components/layout/PageHeader';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { ProgressBar } from '../components/common/ProgressBar';
import { ApplicationCard } from '../components/dashboard/ApplicationCard';
import { EmptyState } from '../components/common/EmptyState';
import { Loading } from '../components/common/Loading';
import { ApplicationStatusType } from '../types/application';

export const Applications: React.FC = () => {
  const { applications, isLoading } = useApplications();
  const [filter, setFilter] = useState<'All' | 'Active' | 'Pending' | 'Completed'>('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('table');

  if (isLoading) {
    return <Loading message="Loading applications..." />;
  }

  const filteredApps = applications.filter((app) => {
    // Search match
    const matchesSearch =
      app.productName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.applicantName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.productCategory.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    // Filter match
    if (filter === 'All') return true;
    if (filter === 'Active') return app.status === 'In Progress';
    if (filter === 'Pending') return app.status === 'Documents Pending' || app.status === 'Under Review';
    if (filter === 'Completed') return app.status === 'Completed';

    return true;
  });

  const getStatusBadge = (status: ApplicationStatusType) => {
    switch (status) {
      case 'Completed':
        return <Badge variant="success">Completed</Badge>;
      case 'Documents Pending':
        return <Badge variant="warning">Documents Pending</Badge>;
      case 'In Progress':
        return <Badge variant="blue">In Progress</Badge>;
      case 'Under Review':
        return <Badge variant="info">Under Review</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Applications"
        description="Monitor, update, and manage your BIS product certification dossiers."
        actions={
          <Link to="/new-application">
            <Button variant="primary" size="sm" icon={<Plus className="w-4 h-4" />}>
              New Application
            </Button>
          </Link>
        }
      />

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search applications by ID, product, or applicant..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
          />
        </div>

        {/* Filter Pills & View Mode */}
        <div className="flex items-center gap-3 overflow-x-auto pb-1 sm:pb-0">
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
            {(['All', 'Active', 'Pending', 'Completed'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
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
              className={`p-1.5 rounded-lg border ${
                viewMode === 'table'
                  ? 'bg-blue-50 text-blue-600 border-blue-200'
                  : 'text-slate-400 hover:text-slate-600 border-transparent'
              }`}
              title="Table view"
            >
              <Table className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg border ${
                viewMode === 'grid'
                  ? 'bg-blue-50 text-blue-600 border-blue-200'
                  : 'text-slate-400 hover:text-slate-600 border-transparent'
              }`}
              title="Grid view"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Content: Table or Grid */}
      {filteredApps.length === 0 ? (
        <EmptyState
          title="No applications found"
          description="Try adjusting your search query or filter criteria, or register a new product."
          action={
            <Link to="/new-application">
              <Button size="sm" variant="primary">
                Create First Application
              </Button>
            </Link>
          }
        />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredApps.map((app) => (
            <ApplicationCard key={app.id} application={app} />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-700 uppercase tracking-wider">
                <tr>
                  <th scope="col" className="px-5 py-3.5">Application ID</th>
                  <th scope="col" className="px-5 py-3.5">Product &amp; Category</th>
                  <th scope="col" className="px-5 py-3.5">Applicant</th>
                  <th scope="col" className="px-5 py-3.5">Created Date</th>
                  <th scope="col" className="px-5 py-3.5">Status</th>
                  <th scope="col" className="px-5 py-3.5">Progress</th>
                  <th scope="col" className="px-5 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredApps.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-5 py-4 font-mono font-semibold text-xs text-blue-600">
                      {app.id}
                    </td>
                    <td className="px-5 py-4">
                      <div>
                        <p className="font-semibold text-slate-900">{app.productName}</p>
                        <p className="text-xs text-slate-500">{app.productCategory}</p>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-xs font-medium text-slate-700">
                      {app.applicantName}
                    </td>
                    <td className="px-5 py-4 text-xs text-slate-500">
                      {new Date(app.createdAt).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-4">
                      {getStatusBadge(app.status)}
                    </td>
                    <td className="px-5 py-4 w-44">
                      <ProgressBar progress={app.progress} showLabel size="sm" />
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link to={`/applications/${app.id}`}>
                        <Button size="sm" variant="outline" className="text-xs">
                          <span>View Application</span>
                          <ArrowRight className="w-3.5 h-3.5 ml-1" />
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
