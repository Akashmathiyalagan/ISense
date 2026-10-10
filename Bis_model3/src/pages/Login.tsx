import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MessageCircle, ShieldCheck, ArrowRight, Lock, Mail, AlertCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/common/Button';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('rajesh.sharma@lumensystems.in');
  const [password, setPassword] = useState('Password@123');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    const success = await login({ email, password });
    setIsLoading(false);
    if (success) {
      navigate('/dashboard');
    } else {
      setError('Invalid credentials. Incorrect password was rejected by authentication service.');
    }
  };

  const handleWhatsAppLogin = async () => {
    setError(null);
    setIsLoading(true);
    const success = await login({ email: 'whatsapp.user@isense.in', isWhatsAppLogin: true });
    setIsLoading(false);
    if (success) {
      navigate('/dashboard');
    } else {
      setError('Failed to initiate WhatsApp session. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2.5 mb-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-xl shadow-xs">
              IS
            </div>
            <span className="font-bold text-slate-900 tracking-tight text-2xl">ISense</span>
          </Link>
          <h2 className="text-xl font-bold text-slate-900">Sign in to your account</h2>
          <p className="text-xs text-slate-500 mt-1">
            Access your BIS certification dashboard, applications &amp; documents
          </p>
        </div>

        {/* WhatsApp Fast Entry Option */}
        <div className="mb-6">
          <button
            type="button"
            onClick={handleWhatsAppLogin}
            className="w-full py-2.5 px-4 rounded-xl border border-emerald-300 bg-emerald-50/80 hover:bg-emerald-100/80 text-emerald-800 text-sm font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-2xs"
          >
            <MessageCircle className="w-4 h-4 text-emerald-600" />
            <span>Continue with WhatsApp Session</span>
          </button>
          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-2 text-slate-400 font-medium">Or continue with email</span>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200/90 text-rose-800 text-xs font-medium flex items-start gap-2.5 animate-in fade-in">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
              <div className="flex-1">{error}</div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-semibold text-slate-700">Password</label>
              <a href="#" className="text-xs text-blue-600 hover:underline">Forgot password?</a>
            </div>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full justify-center mt-2"
            isLoading={isLoading}
          >
            Login to Dashboard
          </Button>
        </form>

        {/* Unified Platform Note */}
        <div className="mt-6 p-3 bg-slate-50 rounded-lg border border-slate-200/80 text-[11px] text-slate-500 text-center">
          First-time applicant? You can start with WhatsApp guidance or register your account directly.
        </div>

        {/* Register link */}
        <p className="text-center text-xs text-slate-500 mt-6">
          Don't have an account?{' '}
          <Link to="/register" className="font-semibold text-blue-600 hover:underline">
            Create account
          </Link>
        </p>
      </div>
    </div>
  );
};
