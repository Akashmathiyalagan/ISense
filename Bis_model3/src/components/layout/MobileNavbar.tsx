import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Search,
  FolderOpen,
  Bot,
} from 'lucide-react';

export const MobileNavbar: React.FC = () => {
  const tabs = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/applications', label: 'Apps', icon: FileText },
    { to: '/standards', label: 'Standards', icon: Search },
    { to: '/documents', label: 'Documents', icon: FolderOpen },
    { to: '/ai-assistant', label: 'AI Chat', icon: Bot },
  ];

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-40 px-2 py-1 flex items-center justify-around shadow-lg">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        return (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              `flex flex-col items-center py-1.5 px-3 rounded-lg text-[11px] font-medium transition-colors ${
                isActive ? 'text-blue-600 font-semibold' : 'text-slate-500 hover:text-slate-900'
              }`
            }
          >
            <Icon className="w-5 h-5 mb-0.5" />
            <span>{tab.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
};
