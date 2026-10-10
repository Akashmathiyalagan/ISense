import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  MessageCircle,
  LayoutDashboard,
  ArrowRight,
  CheckCircle2,
  FileCheck,
  Bot,
  Database,
  Search,
  Sparkles,
  Layers,
  FileText,
  Clock,
  Compass,
} from 'lucide-react';
import { Button } from '../components/common/Button';

export const Landing: React.FC = () => {
  const navigate = useNavigate();

  const workflowSteps = [
    { number: '01', title: 'Product', desc: 'Identify specifications, rating & technical parameters' },
    { number: '02', title: 'BIS Standard', desc: 'Auto-match against authoritative Indian Standards' },
    { number: '03', title: 'Requirements', desc: 'Extract mandatory checklist items & testing schedule' },
    { number: '04', title: 'Documents', desc: 'Upload lab reports, factory QAP & verify consistency' },
    { number: '05', title: 'Readiness', desc: 'Generate complete verified dossier for official submission' },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900 selection:bg-blue-100 selection:text-blue-900">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-lg shadow-sm">
              IS
            </div>
            <div>
              <span className="font-bold text-slate-900 tracking-tight text-xl leading-none">ISense</span>
              <span className="ml-2 text-[10px] font-semibold bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full border border-blue-200">
                BIS AI Assistance
              </span>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <a href="#how-it-works" className="hover:text-blue-600 transition-colors">How It Works</a>
            <a href="#entry-points" className="hover:text-blue-600 transition-colors">WhatsApp vs Website</a>
            <a href="#features" className="hover:text-blue-600 transition-colors">Features</a>
            <a href="#about" className="hover:text-blue-600 transition-colors">About</a>
          </nav>

          <div className="flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Login
              </Button>
            </Link>
            <Link to="/register">
              <Button variant="primary" size="sm">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-16 pb-20 sm:pt-24 sm:pb-28 overflow-hidden bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-xs font-semibold text-blue-700 mb-6">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>RAG-Grounded Guidance for Bureau of Indian Standards (BIS)</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-slate-900 leading-tight">
            Your AI Guide for <span className="text-blue-600">BIS Certification</span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
            Understand BIS requirements, prepare documents and navigate the certification journey with AI-powered assistance.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register">
              <Button size="lg" variant="primary" icon={<ArrowRight className="w-5 h-5" />} iconPosition="right">
                Start with ISense
              </Button>
            </Link>
            <a href="#how-it-works">
              <Button size="lg" variant="outline">
                Explore How It Works
              </Button>
            </a>
          </div>

          {/* Unified Platform Banner */}
          <div className="mt-12 p-4 max-w-2xl mx-auto rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center gap-4 text-xs text-slate-600">
            <div className="flex items-center gap-1.5 font-medium text-emerald-700">
              <MessageCircle className="w-4 h-4 text-emerald-600" />
              <span>WhatsApp Interface</span>
            </div>
            <span className="text-slate-300">✦</span>
            <div className="flex items-center gap-1.5 font-medium text-blue-700">
              <LayoutDashboard className="w-4 h-4 text-blue-600" />
              <span>Web Platform</span>
            </div>
            <span className="text-slate-300">✦</span>
            <div className="flex items-center gap-1.5 font-medium text-slate-700">
              <Database className="w-4 h-4 text-slate-600" />
              <span>Same Database &amp; RAG Engine</span>
            </div>
          </div>
        </div>
      </section>

      {/* Visual Workflow Representation */}
      <section id="how-it-works" className="py-20 bg-slate-50 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs uppercase font-bold tracking-wider text-blue-600">The Certification Pathway</h2>
            <p className="text-3xl font-bold text-slate-900 mt-2">The ISense Guided Workflow</p>
            <p className="text-sm text-slate-500 mt-2">
              From product identification to complete application readiness for official BIS filing.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
            {workflowSteps.map((step, idx) => (
              <div
                key={step.number}
                className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs relative flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-2xl font-bold text-blue-600 font-mono">{step.number}</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  </div>
                  <h3 className="text-base font-semibold text-slate-900">{step.title}</h3>
                  <p className="text-xs text-slate-500 mt-2 leading-relaxed">{step.desc}</p>
                </div>
                {idx < workflowSteps.length - 1 && (
                  <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-slate-100 border border-slate-300 items-center justify-center text-slate-400">
                    <ArrowRight className="w-3 h-3" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Two Entry Points Section */}
      <section id="entry-points" className="py-20 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-14">
            <h2 className="text-xs uppercase font-bold tracking-wider text-blue-600">Omni-Channel Architecture</h2>
            <p className="text-3xl font-bold text-slate-900 mt-2">Two Entry Points, One Unified System</p>
            <p className="text-sm text-slate-500 mt-2 leading-relaxed">
              WhatsApp and Website are not two separate systems. Both access the exact same backend, database, applications, documents, and RAG knowledge engine.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* WhatsApp Card */}
            <div className="bg-slate-50 rounded-2xl p-8 border border-emerald-200 shadow-xs flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-100/50 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
              <div>
                <div className="w-12 h-12 rounded-xl bg-emerald-600 text-white flex items-center justify-center mb-6 shadow-xs">
                  <MessageCircle className="w-6 h-6" />
                </div>
                <div className="inline-block px-2.5 py-1 rounded bg-emerald-100 text-emerald-800 text-xs font-semibold uppercase tracking-wider mb-2">
                  WHATSAPP INTERFACE
                </div>
                <h3 className="text-2xl font-bold text-slate-900">Guided for First-Time Applicants</h3>
                <p className="text-sm text-slate-600 mt-2">
                  Designed primarily for first-time applicants who do not understand the BIS registration process.
                </p>

                <ul className="mt-6 space-y-3.5 text-sm text-slate-700">
                  <li className="flex items-center gap-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span><strong>Step-by-step guidance</strong> through natural conversation</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span><strong>Simple conversational interaction</strong> with no learning curve</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span><strong>Document collection</strong> directly through phone photos &amp; files</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span><strong>AI assistance</strong> answering queries 24/7 on WhatsApp</span>
                  </li>
                </ul>
              </div>

              <div className="mt-8 pt-6 border-t border-emerald-200/80">
                <Link to="/login">
                  <Button variant="outline" className="w-full justify-center border-emerald-300 text-emerald-800 hover:bg-emerald-100/60">
                    Connect via WhatsApp Bot
                  </Button>
                </Link>
              </div>
            </div>

            {/* Website Card */}
            <div className="bg-slate-50 rounded-2xl p-8 border border-blue-200 shadow-xs flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-100/50 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
              <div>
                <div className="w-12 h-12 rounded-xl bg-blue-600 text-white flex items-center justify-center mb-6 shadow-xs">
                  <LayoutDashboard className="w-6 h-6" />
                </div>
                <div className="inline-block px-2.5 py-1 rounded bg-blue-100 text-blue-800 text-xs font-semibold uppercase tracking-wider mb-2">
                  WEBSITE PLATFORM
                </div>
                <h3 className="text-2xl font-bold text-slate-900">Built for Complete Application Management</h3>
                <p className="text-sm text-slate-600 mt-2">
                  Designed for users and enterprises who want direct access to manage multiple products.
                </p>

                <ul className="mt-6 space-y-3.5 text-sm text-slate-700">
                  <li className="flex items-center gap-3">
                    <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
                    <span><strong>Manage multiple applications</strong> in an enterprise dashboard</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
                    <span><strong>Document management</strong> with verification check audit trails</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
                    <span><strong>Progress tracking</strong> across all 7 certification milestones</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
                    <span><strong>RAG AI Assistant</strong> with citations to official standards</span>
                  </li>
                </ul>
              </div>

              <div className="mt-8 pt-6 border-t border-blue-200/80">
                <Link to="/dashboard">
                  <Button variant="primary" className="w-full justify-center">
                    Launch Web Dashboard
                  </Button>
                </Link>
              </div>
            </div>
          </div>

          {/* Unified System Callout */}
          <div className="mt-8 p-5 bg-white rounded-xl border border-slate-200 text-center text-xs text-slate-600">
            <p>
              <strong className="text-slate-900 font-semibold">Important Architecture Fact:</strong> Both WhatsApp and Web access the same live database. You can start your product submission on WhatsApp from your mobile phone, and immediately manage documents and track readiness on the Web platform.
            </p>
          </div>
        </div>
      </section>

      {/* Features Overview */}
      <section id="features" className="py-20 bg-slate-50 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-14">
            <h2 className="text-xs uppercase font-bold tracking-wider text-blue-600">Core Capabilities</h2>
            <p className="text-3xl font-bold text-slate-900 mt-2">Everything Needed for BIS Compliance</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
              <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-slate-900 text-base">BIS Standards Discovery</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Query our grounded knowledge base to find applicable IS numbers, testing scopes, and relevant clauses without confusing legal jargon.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
                <FileCheck className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-slate-900 text-base">Pre-Submission Check</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Automated document information checks verify if your lab reports, factory registration, and artwork match regulatory prerequisites.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
              <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center mb-4">
                <Bot className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-slate-900 text-base">RAG Grounded AI Assistant</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Every AI response quotes authoritative knowledge base clauses with page numbers and exact standard references.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer id="about" className="bg-white py-12 border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
              IS
            </div>
            <span className="font-semibold text-slate-800">ISense Platform</span>
            <span>• SIH Prototype</span>
          </div>
          <p>
            Built for Smart India Hackathon. Official grant of BIS registration is subject to statutory procedures.
          </p>
          <div className="flex items-center gap-4">
            <Link to="/login" className="hover:text-blue-600">Login</Link>
            <Link to="/register" className="hover:text-blue-600">Register</Link>
            <Link to="/dashboard" className="hover:text-blue-600">Demo App</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};
