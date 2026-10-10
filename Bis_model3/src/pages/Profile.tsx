import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { PageHeader } from '../components/layout/PageHeader';
import { Button } from '../components/common/Button';
import { UserRole } from '../types/user';
import { Check, User as UserIcon, Building, Mail, Phone, Shield } from 'lucide-react';

export const Profile: React.FC = () => {
  const { currentUser, updateProfile } = useAuth();

  const [fullName, setFullName] = useState(currentUser?.fullName || 'Rajesh Sharma');
  const [email, setEmail] = useState(currentUser?.email || 'rajesh.sharma@lumensystems.in');
  const [phone, setPhone] = useState(currentUser?.phone || '+91 98765 43210');
  const [organisation, setOrganisation] = useState(currentUser?.organisation || 'Lumen Systems Private Limited');
  const [userType, setUserType] = useState<UserRole>(currentUser?.userType || 'Manufacturer');
  const [isSaved, setIsSaved] = useState(false);

  const userRoles: UserRole[] = ['Manufacturer', 'Importer', 'Brand Owner', 'MSME', 'Other'];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile({
      fullName,
      email,
      phone,
      organisation,
      userType,
    });
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  return (
    <div className="max-w-3xl space-y-6">
      <PageHeader
        title="User Profile"
        description="Manage your enterprise contact details, organization registration, and applicant classification."
      />

      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        {/* Profile Card Header */}
        <div className="flex items-center gap-4 pb-6 border-b border-slate-100 mb-6">
          <div className="w-14 h-14 rounded-2xl bg-blue-600 text-white flex items-center justify-center font-bold text-xl shadow-xs">
            {fullName
              .split(' ')
              .map((n) => n[0])
              .join('')
              .slice(0, 2)}
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">{fullName}</h3>
            <p className="text-xs text-slate-500">{organisation} • {userType}</p>
          </div>
        </div>

        {isSaved && (
          <div className="mb-6 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-600" />
            <span>Profile settings successfully updated and synchronized across Web &amp; WhatsApp!</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Full Name</label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Phone Number</label>
              <div className="relative">
                <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="tel"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Organization / Entity</label>
              <div className="relative">
                <Building className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={organisation}
                  onChange={(e) => setOrganisation(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Applicant User Type</label>
            <div className="relative">
              <Shield className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <select
                value={userType}
                onChange={(e) => setUserType(e.target.value as UserRole)}
                className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {userRoles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <Button type="submit" variant="primary">
              Save Changes
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
