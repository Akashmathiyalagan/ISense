import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Bell,
  Search,
  Plus,
  MessageCircle,
  Menu,
  Zap,
  HelpCircle,
} from 'lucide-react';
import { Button } from '../common/Button';

interface NavbarProps {
  onToggleMobileMenu?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleMobileMenu }) => {
  const navigate = useNavigate();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Left: Mobile Menu Toggle & Search */}
      <div className="flex items-center gap-3 sm:gap-4 flex-1 max-w-md">
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg focus:outline-none"
          aria-label="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Global Search Bar */}
        <div className="relative w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search IS standards, products, or documents..."
            onClick={() => navigate('/standards')}
            readOnly
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-1.5 text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all cursor-pointer"
          />
        </div>
      </div>

      {/* Right: Actions, Real-time indicators, Notifications & Status */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Real-Time Live Sync Pulse Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 text-blue-800 border border-blue-200 text-xs font-semibold">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-[11px] font-medium">Real-Time Sync Active</span>
        </div>

        {/* WhatsApp Link indicator */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-medium">
          <MessageCircle className="w-3.5 h-3.5 text-emerald-600" />
          <span>WhatsApp Linked</span>
        </div>

        {/* New Application CTA */}
        <Link to="/new-application">
          <Button size="sm" variant="primary" icon={<Plus className="w-4 h-4" />}>
            <span className="hidden sm:inline">New Application</span>
            <span className="sm:hidden">New</span>
          </Button>
        </Link>

        {/* Notifications */}
        <button
          className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors relative"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-600 rounded-full" />
        </button>

        {/* AI Assistant Quick Trigger */}
        <Link
          to="/ai-assistant"
          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors flex items-center gap-1 text-xs font-medium"
          title="Open AI Assistant"
        >
          <HelpCircle className="w-4 h-4" />
          <span className="hidden lg:inline">Ask AI</span>
        </Link>
      </div>
    </header>
  );
};
