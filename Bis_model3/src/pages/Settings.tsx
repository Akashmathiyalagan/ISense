import React, { useState } from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { Button } from '../components/common/Button';
import {
  Bell,
  Lock,
  Globe,
  Shield,
  Smartphone,
  Save,
  Check,
} from 'lucide-react';

export const Settings: React.FC = () => {
  const [activeSection, setActiveSection] = useState<'account' | 'notifications' | 'security' | 'language' | 'privacy'>('account');
  const [isSaved, setIsSaved] = useState(false);

  const [settings, setSettings] = useState({
    emailAlerts: true,
    whatsappSync: true,
    smsAlerts: false,
    twoFactor: true,
    language: 'English (en-IN)',
    dataRetentionDays: '365',
  });

  const handleSave = () => {
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2500);
  };

  const navItems = [
    { key: 'account', label: 'Account & WhatsApp Sync', icon: Smartphone },
    { key: 'notifications', label: 'Notifications', icon: Bell },
    { key: 'security', label: 'Security & Auth', icon: Lock },
    { key: 'language', label: 'Language & Locale', icon: Globe },
    { key: 'privacy', label: 'Data & Privacy', icon: Shield },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Configure account preferences, omni-channel notifications, and knowledge base sync rules."
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Navigation side pills */}
        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.key;
            return (
              <button
                key={item.key}
                onClick={() => setActiveSection(item.key as any)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold text-left transition-all ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content area */}
        <div className="md:col-span-3 bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
          {isSaved && (
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-600" />
              <span>Settings successfully saved!</span>
            </div>
          )}

          {activeSection === 'account' && (
            <div className="space-y-4">
              <h3 className="text-base font-semibold text-slate-900">Account &amp; WhatsApp Integration</h3>
              <p className="text-xs text-slate-500">Manage unified access between Web and WhatsApp Assistant.</p>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-slate-800">Live WhatsApp Assistant Pairing</p>
                    <p className="text-slate-500">Allow your phone number to submit documents directly via WhatsApp.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.whatsappSync}
                    onChange={(e) => setSettings({ ...settings, whatsappSync: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                </div>
              </div>
            </div>
          )}

          {activeSection === 'notifications' && (
            <div className="space-y-4">
              <h3 className="text-base font-semibold text-slate-900">Notification Preferences</h3>
              <p className="text-xs text-slate-500">Configure how and when you receive dossier update notices.</p>

              <div className="space-y-3 text-xs">
                <label className="flex items-center justify-between p-3 rounded-lg border border-slate-200">
                  <div>
                    <p className="font-semibold text-slate-800">Email Notifications</p>
                    <p className="text-slate-500">Receive summaries on document verification checks.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.emailAlerts}
                    onChange={(e) => setSettings({ ...settings, emailAlerts: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                </label>

                <label className="flex items-center justify-between p-3 rounded-lg border border-slate-200">
                  <div>
                    <p className="font-semibold text-slate-800">SMS Critical Alerts</p>
                    <p className="text-slate-500">Alerts when laboratory test validity approaches expiration.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.smsAlerts}
                    onChange={(e) => setSettings({ ...settings, smsAlerts: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                </label>
              </div>
            </div>
          )}

          {activeSection === 'security' && (
            <div className="space-y-4">
              <h3 className="text-base font-semibold text-slate-900">Security &amp; Authentication</h3>
              <p className="text-xs text-slate-500">Protect access to your technical dossiers and compliance reports.</p>

              <div className="space-y-3 text-xs">
                <label className="flex items-center justify-between p-3 rounded-lg border border-slate-200">
                  <div>
                    <p className="font-semibold text-slate-800">Two-Factor Authentication (2FA)</p>
                    <p className="text-slate-500">Require OTP verification upon signing in from new devices.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.twoFactor}
                    onChange={(e) => setSettings({ ...settings, twoFactor: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                </label>
              </div>
            </div>
          )}

          {activeSection === 'language' && (
            <div className="space-y-4">
              <h3 className="text-base font-semibold text-slate-900">Language &amp; Localization</h3>
              <p className="text-xs text-slate-500">Select language for AI Assistant and documentation instructions.</p>

              <div className="max-w-xs">
                <select
                  value={settings.language}
                  onChange={(e) => setSettings({ ...settings, language: e.target.value })}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="English (en-IN)">English (India)</option>
                  <option value="Hindi (hi-IN)">हिंदी (Hindi)</option>
                  <option value="Tamil (ta-IN)">தமிழ் (Tamil)</option>
                  <option value="Telugu (te-IN)">తెలుగు (Telugu)</option>
                </select>
              </div>
            </div>
          )}

          {activeSection === 'privacy' && (
            <div className="space-y-4">
              <h3 className="text-base font-semibold text-slate-900">Data &amp; Privacy</h3>
              <p className="text-xs text-slate-500">Manage data retention and export audit logs.</p>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 leading-relaxed">
                <p>
                  ISense encrypts all technical dossiers in transit and at rest. Documents submitted for automated structure checks are not shared with unverified third parties.
                </p>
              </div>
            </div>
          )}

          <div className="pt-4 border-t border-slate-100 flex justify-end">
            <Button variant="primary" size="sm" onClick={handleSave} icon={<Save className="w-4 h-4" />}>
              Save Preferences
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
