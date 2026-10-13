import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Search,
  Sparkles,
  CheckSquare,
  FolderOpen,
  Bot,
  Compass,
  User,
  Settings,
  LogOut,
  ShieldCheck,
  MessageCircle,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

interface SidebarProps {
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onCloseMobile }) => {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
    if (onCloseMobile) onCloseMobile();
  };

  const navLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/applications', label: 'Applications', icon: FileText },
    { to: '/product-assessment', label: 'Product Assessment', icon: Sparkles, badge: 'AI' },
    { to: '/standards', label: 'BIS Standards', icon: Search },
    { to: '/requirements', label: 'Requirements', icon: CheckSquare },
    { to: '/documents', label: 'Documents', icon: FolderOpen },
    { to: '/ai-assistant', label: 'AI Assistant', icon: Bot, badge: 'RAG' },
    { to: '/tracking', label: 'Tracking', icon: Compass },
    { to: '/profile', label: 'Profile', icon: User },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-full select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-100 flex items-center justify-between">
        <NavLink to="/dashboard" className="flex items-center gap-2.5" onClick={onCloseMobile}>
          <div className="w-9 h-9 rounded-lg bg-blue-600 text-white flex items-center justify-center shadow-xs font-bold text-lg">
            IS
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-slate-900 tracking-tight text-lg leading-none">ISense</span>
              <span className="text-[10px] font-semibold bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded border border-blue-200/60 leading-none">
                BIS AI
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-normal leading-tight mt-0.5">
              Assistance Platform
            </p>
          </div>
        </NavLink>
      </div>

      {/* Sync Banner: WhatsApp + Web shared core */}
      <div className="mx-3.5 my-3 p-2.5 rounded-lg bg-slate-50 border border-slate-200/80">
        <div className="flex items-center gap-2 text-xs font-medium text-slate-700">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="truncate">Unified Backend Sync</span>
        </div>
        <p className="text-[11px] text-slate-500 mt-1 leading-snug">
          WhatsApp &amp; Web access the same live applications, documents &amp; RAG.
        </p>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
        {navLinks.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onCloseMobile}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`
              }
            >
              <div className="flex items-center gap-2.5">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-blue-100/70 text-blue-700">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* WhatsApp Quick Entry Pill */}
      <div className="p-3 mx-3 mb-2 bg-emerald-50/70 border border-emerald-200/80 rounded-lg">
        <div className="flex items-center justify-between text-xs font-semibold text-emerald-800 mb-1">
          <div className="flex items-center gap-1.5">
            <MessageCircle className="w-3.5 h-3.5 text-emerald-600" />
            <span>WhatsApp Entry</span>
          </div>
          <span className="text-[10px] text-emerald-600 bg-emerald-100/80 px-1 py-0.2 rounded font-medium">Synced</span>
        </div>
        <p className="text-[11px] text-emerald-700/90 leading-tight">
          First-time applicant? Continue conversational guidance on WhatsApp.
        </p>
      </div>

      {/* User profile & Logout */}
      <div className="p-3 border-t border-slate-100 bg-white">
        <div className="flex items-center justify-between gap-2 p-1.5 rounded-lg hover:bg-slate-50">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-semibold text-xs shrink-0">
              {currentUser?.fullName
                ? currentUser.fullName
                    .split(' ')
                    .map((n) => n[0])
                    .join('')
                    .slice(0, 2)
                : 'U'}
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold text-slate-800 truncate">
                {currentUser?.fullName || 'Rajesh Sharma'}
              </p>
              <p className="text-[11px] text-slate-500 truncate">
                {currentUser?.userType || 'Manufacturer'}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="Log out"
            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
            aria-label="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
