import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { RealtimeProvider, useRealtime } from './context/RealtimeContext';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { Sidebar } from './components/layout/Sidebar';
import { Navbar } from './components/layout/Navbar';
import { MobileNavbar } from './components/layout/MobileNavbar';
import { Loading } from './components/common/Loading';
import { X, CheckCircle, Info, AlertTriangle } from 'lucide-react';

// Pages
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { Applications } from './pages/Applications';
import { NewApplication } from './pages/NewApplication';
import { ApplicationDetails } from './pages/ApplicationDetails';
import { BISStandards } from './pages/BISStandards';
import { Requirements } from './pages/Requirements';
import { Documents } from './pages/Documents';
import { AIAssistant } from './pages/AIAssistant';
import { Tracking } from './pages/Tracking';
import { Profile } from './pages/Profile';
import { Settings } from './pages/Settings';

// Floating Toast Container for Real-Time Event Alerts
const ToastContainer: React.FC = () => {
  const { toasts, dismissToast } = useRealtime();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-18 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="pointer-events-auto bg-white/95 backdrop-blur-md rounded-xl p-3.5 border border-slate-200/90 shadow-lg flex items-start gap-3 transform transition-all animate-in fade-in slide-in-from-top-2"
        >
          <div className="mt-0.5 shrink-0">
            {toast.type === 'success' ? (
              <CheckCircle className="w-4 h-4 text-emerald-600" />
            ) : toast.type === 'warning' ? (
              <AlertTriangle className="w-4 h-4 text-amber-600" />
            ) : (
              <Info className="w-4 h-4 text-blue-600" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h5 className="text-xs font-bold text-slate-900 truncate">{toast.title}</h5>
              <span className="text-[10px] text-slate-400 shrink-0">{toast.timestamp}</span>
            </div>
            <p className="text-[11px] text-slate-600 mt-0.5 leading-snug">{toast.description}</p>
          </div>
          <button
            onClick={() => dismissToast(toast.id)}
            className="text-slate-400 hover:text-slate-600 p-0.5 rounded cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
};

// Layout for Protected Pages
const AppLayout: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <Loading fullPage message="Authenticating session..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 text-slate-900 relative">
      {/* Real-Time Floating Toasts */}
      <ToastContainer />

      {/* Desktop Sidebar */}
      <div className="hidden lg:block shrink-0 h-full">
        <Sidebar />
      </div>

      {/* Mobile Drawer Backdrop & Sidebar */}
      {isMobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={() => setIsMobileMenuOpen(false)}
          />
          <div className="relative z-50 w-72 bg-white h-full shadow-2xl flex flex-col">
            <Sidebar onCloseMobile={() => setIsMobileMenuOpen(false)} />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar onToggleMobileMenu={() => setIsMobileMenuOpen(prev => !prev)} />

        <main className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6 pb-20 lg:pb-8">
          <Outlet />
        </main>

        {/* Mobile Bottom Navigation */}
        <MobileNavbar />
      </div>
    </div>
  );
};

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <RealtimeProvider>
          <BrowserRouter>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Authenticated SaaS Dashboard Routes */}
              <Route element={<AppLayout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/applications" element={<Applications />} />
                <Route path="/new-application" element={<NewApplication />} />
                <Route path="/applications/:id" element={<ApplicationDetails />} />
                <Route path="/standards" element={<BISStandards />} />
                <Route path="/requirements" element={<Requirements />} />
                <Route path="/documents" element={<Documents />} />
                <Route path="/ai-assistant" element={<AIAssistant />} />
                <Route path="/tracking" element={<Tracking />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/settings" element={<Settings />} />
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </RealtimeProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}
