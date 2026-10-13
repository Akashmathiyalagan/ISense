import React, { useMemo, useState } from 'react';
import { apiClient, handleApiError } from '../services/api';
import {
  ArrowRight, ArrowLeft, CheckCircle2, ChevronDown, CircleHelp,
  FileSearch, LoaderCircle, RotateCcw, Search, ShieldAlert, Sparkles
} from 'lucide-react';

type QuestionField = {
  id: string;
  label: string;
  type: 'radio' | 'checkbox' | 'text';
  options?: string[];
  required?: boolean;
  helpText?: string;
};

type CandidateStandard = {
  is_number?: string;
  title?: string;
  technical_department?: string;
  sectional_committee?: string;
  standard_type?: string;
  published_on?: string;
  source_url?: string;
  evidence_level?: string;
  applicability?: string;
};

type ScopeEvidence = {
  standard_code?: string;
  standard_title?: string;
  clause?: string;
  text?: string;
  source_url?: string;
};

type QuestionnaireSchema = {
  product: string;
  title: string;
  description: string;
  fields: QuestionField[];
  candidateStandards?: CandidateStandard[];
  scopeEvidence?: ScopeEvidence[];
  revisionPolicy?: string;
  conversationId?: string;
};

type AssessmentResult = {
  content?: string;
  sources?: Array<{ title?: string; source?: string; url?: string; standard_code?: string; clause?: string }>;
  confidence?: number;
  insufficient_evidence?: boolean;
  warnings?: string[];
  conversationId?: string;
};

const cx = (...parts: Array<string | false | undefined>) => parts.filter(Boolean).join(' ');

export const ProductAssessment: React.FC = () => {
  const [product, setProduct] = useState('');
  const [schema, setSchema] = useState<QuestionnaireSchema | null>(null);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [loadingResearch, setLoadingResearch] = useState(false);
  const [loadingAssessment, setLoadingAssessment] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [conversationId, setConversationId] = useState('');

  const candidates = useMemo(() => {
    const list = schema?.candidateStandards?.length
      ? schema.candidateStandards
      : (schema as any)?.catalogue_candidates || [];
    const seen = new Set<string>();
    return list.filter((item: CandidateStandard) => {
      const key = String(item.is_number || '') + String(item.title || '');
      if (!item.is_number || !item.title || seen.has(key)) return false;
      seen.add(key);
      return true;
    }).slice(0, 12);
  }, [schema]);

  const setAnswer = (id: string, value: string | string[]) => {
    setAnswers(previous => ({ ...previous, [id]: value }));
  };

  const researchProduct = async (event: React.FormEvent) => {
    event.preventDefault();
    const cleanProduct = product.trim();
    if (!cleanProduct) {
      setError('Enter a product name to begin the assessment.');
      return;
    }
    setLoadingResearch(true);
    setError('');
    setResult(null);
    setSchema(null);
    setAnswers({});
    const nextConversationId = conversationId || `assessment-${Date.now()}`;
    try {
      const response = await apiClient.post<QuestionnaireSchema>('/api/ai/product-questionnaire', {
        product: cleanProduct,
        conversationId: nextConversationId,
      });
      setSchema(response.data);
      setConversationId(response.data.conversationId || nextConversationId);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoadingResearch(false);
    }
  };

  const submitAssessment = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!schema) return;
    const missing = schema.fields.find(field => field.required && (
      answers[field.id] === undefined ||
      answers[field.id] === '' ||
      (Array.isArray(answers[field.id]) && (answers[field.id] as string[]).length === 0)
    ));
    if (missing) {
      setError(`Please answer: ${missing.label}`);
      return;
    }

    setLoadingAssessment(true);
    setError('');
    const formattedAnswers = schema.fields.map(field => {
      const value = answers[field.id];
      return `- ${field.label}: ${Array.isArray(value) ? value.join(', ') : (value || 'Not provided')}`;
    }).join('\n');
    const candidateSummary = candidates.length
      ? candidates.map((item: CandidateStandard) => `- ${item.is_number}: ${item.title} (candidate only; applicability unconfirmed)`).join('\n')
      : 'No catalogue candidate list was returned.';
    const evidenceSummary = (schema.scopeEvidence || []).slice(0, 10).map(item =>
      `- ${item.standard_code || 'Unlabelled standard'} — ${item.standard_title || ''}; ${item.clause || 'scope excerpt'}: ${(item.text || '').slice(0, 800)}; source: ${item.source_url || 'not supplied'}`
    ).join('\n');
    const message = [
      'Perform a preliminary, evidence-grounded BIS product-scope assessment using the existing knowledge base.',
      `Product: ${schema.product}`,
      'Product facts supplied by the applicant:',
      formattedAnswers,
      'Catalogue candidates to investigate (not confirmed applicable standards):',
      candidateSummary,
      'Retrieved scope evidence:',
      evidenceSummary || 'No scope evidence was returned with the questionnaire.',
      'Compare the scope and intended use of each plausible candidate. Explain which standard(s) appear relevant, which can be ruled out or need more information, and why. Distinguish standard editions/amendments when evidence supports it. Cite the available source names, clauses and URLs. Do not invent revisions, clauses or legal status. Do not claim a standard is mandatory/current unless retrieved official evidence establishes that. If evidence is insufficient, state what is missing and ask a focused next question. This is preliminary guidance, not an official BIS decision.',
    ].join('\n\n');

    try {
      const response = await apiClient.post<AssessmentResult>('/api/ai/chat', {
        message,
        conversationId: schema.conversationId || conversationId || undefined,
      });
      setResult(response.data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoadingAssessment(false);
    }
  };

  const reset = () => {
    setProduct('');
    setSchema(null);
    setAnswers({});
    setResult(null);
    setError('');
    setConversationId('');
  };

  return (
    <div className="min-h-full -m-4 sm:-m-6 lg:-m-8 bg-[#090d16] text-slate-100">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-7 sm:py-10 lg:px-10">
        <header className="mb-8 flex flex-col gap-5 border-b border-white/10 pb-7 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-400/25 bg-cyan-400/10 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200">
              <Sparkles className="h-3.5 w-3.5" /> ISense · BIS intelligence
            </div>
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">Product assessment</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Research candidate standards first. Answer product-specific questions, then assess scope against the connected BIS knowledge base.
            </p>
          </div>
          <div className="flex items-center gap-2 self-start rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-300 sm:self-auto">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Connected assessment API
          </div>
        </header>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
          <main className="min-w-0 space-y-6">
            <section className="rounded-2xl border border-white/10 bg-[#101725] p-5 shadow-2xl shadow-black/10 sm:p-7">
              <div className="mb-5 flex items-start gap-3">
                <div className="rounded-xl border border-cyan-400/20 bg-cyan-400/10 p-2.5 text-cyan-200"><Search className="h-5 w-5" /></div>
                <div>
                  <h2 className="text-base font-semibold text-white">01 / Identify your product</h2>
                  <p className="mt-1 text-xs leading-5 text-slate-400">Use a clear product name or type. The backend searches catalogue records and indexed scope evidence.</p>
                </div>
              </div>
              <form onSubmit={researchProduct} className="space-y-4">
                <label className="block text-xs font-medium text-slate-300" htmlFor="product-name">Product name or description <span className="text-rose-300">*</span></label>
                <div className="flex flex-col gap-3 sm:flex-row">
                  <input
                    id="product-name"
                    value={product}
                    onChange={e => setProduct(e.target.value)}
                    maxLength={120}
                    placeholder="e.g. office chair, plastic chair, LED lamp"
                    className="min-w-0 flex-1 rounded-xl border border-white/10 bg-[#090f1b] px-4 py-3.5 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/10"
                    required
                  />
                  <button disabled={loadingResearch} className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-cyan-300 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60">
                    {loadingResearch ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <FileSearch className="h-4 w-4" />}
                    {loadingResearch ? 'Researching…' : 'Research product'}
                  </button>
                </div>
              </form>
            </section>

            {error && <div role="alert" className="flex items-start gap-3 rounded-xl border border-rose-400/25 bg-rose-400/10 p-4 text-sm text-rose-100"><ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" /><span>{error}</span></div>}

            {schema && (
              <>
                <section className="rounded-2xl border border-white/10 bg-[#101725] p-5 sm:p-7">
                  <div className="mb-5 flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-200">Research output</p>
                      <h2 className="mt-2 text-xl font-semibold text-white">{schema.title || `Identify the BIS scope for ${schema.product}`}</h2>
                      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{schema.description}</p>
                    </div>
                    <span className="shrink-0 rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1.5 text-[10px] text-slate-400">{candidates.length} candidates</span>
                  </div>

                  {candidates.length > 0 ? (
                    <div className="space-y-3">
                      <p className="text-xs font-semibold text-slate-300">Candidate standards to investigate <span className="font-normal text-slate-500">· not confirmed applicable</span></p>
                      {candidates.map((candidate: CandidateStandard, index: number) => (
                        <article key={`${candidate.is_number}-${index}`} className="rounded-xl border border-white/[0.08] bg-[#0b111d] p-4">
                          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                            <div className="min-w-0">
                              <div className="mb-1.5 flex flex-wrap items-center gap-2">
                                <span className="rounded-md border border-cyan-300/20 bg-cyan-300/10 px-2 py-1 font-mono text-xs font-semibold text-cyan-100">{candidate.is_number}</span>
                                <span className="rounded-md border border-amber-300/20 bg-amber-300/10 px-2 py-1 text-[10px] text-amber-200">Applicability unconfirmed</span>
                              </div>
                              <h3 className="text-sm font-medium leading-5 text-slate-100">{candidate.title}</h3>
                            </div>
                            {candidate.source_url && <a href={candidate.source_url} target="_blank" rel="noreferrer" className="shrink-0 text-xs text-cyan-200 underline decoration-cyan-200/30 underline-offset-4 hover:text-cyan-100">Source record ↗</a>}
                          </div>
                          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500">
                            {candidate.technical_department && <span>Department: {candidate.technical_department}</span>}
                            {candidate.standard_type && <span>Type: {candidate.standard_type}</span>}
                            {candidate.published_on && <span>Published: {candidate.published_on}</span>}
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <div className="rounded-xl border border-dashed border-white/15 p-4 text-sm text-slate-400">No catalogue candidates were returned. The questions below collect the minimum details needed to narrow the product.</div>
                  )}

                  {(schema.scopeEvidence || []).length > 0 && (
                    <details className="mt-5 rounded-xl border border-white/10 bg-black/10 p-4">
                      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-xs font-semibold text-slate-300">Retrieved scope evidence <ChevronDown className="h-4 w-4 text-slate-500" /></summary>
                      <div className="mt-4 space-y-3">
                        {schema.scopeEvidence!.slice(0, 8).map((item, index) => (
                          <div key={index} className="border-l-2 border-cyan-300/30 pl-3">
                            <p className="text-xs font-semibold text-slate-200">{item.standard_code || 'Standard not labelled'} · {item.clause || 'Scope excerpt'}</p>
                            <p className="mt-1 whitespace-pre-wrap text-xs leading-5 text-slate-400">{item.text}</p>
                            {item.source_url && <a href={item.source_url} target="_blank" rel="noreferrer" className="mt-1 inline-block text-[11px] text-cyan-200 underline underline-offset-2">Open source ↗</a>}
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </section>

                <form onSubmit={submitAssessment} className="rounded-2xl border border-white/10 bg-[#101725] p-5 sm:p-7">
                  <div className="mb-6 flex items-start gap-3">
                    <div className="rounded-xl border border-violet-300/20 bg-violet-300/10 p-2.5 text-violet-200"><CircleHelp className="h-5 w-5" /></div>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-violet-200">02 / Clarify scope</p>
                      <h2 className="mt-1 text-lg font-semibold text-white">A few details about your product</h2>
                      <p className="mt-1 text-xs leading-5 text-slate-400">Questions are generated from the product and available candidate evidence, not from a fixed universal form.</p>
                    </div>
                  </div>

                  <div className="space-y-6">
                    {schema.fields.map((field, index) => (
                      <fieldset key={field.id} className="border-b border-white/[0.07] pb-6 last:border-0 last:pb-0">
                        <legend className="mb-3 text-sm font-medium leading-6 text-slate-100"><span className="mr-2 font-mono text-xs text-slate-500">0{index + 1}</span>{field.label}{field.required && <span className="ml-1 text-rose-300">*</span>}</legend>
                        {field.helpText && <p className="mb-3 text-xs leading-5 text-slate-500">{field.helpText}</p>}
                        {field.type === 'text' ? (
                          <textarea
                            rows={3}
                            value={String(answers[field.id] || '')}
                            onChange={e => setAnswer(field.id, e.target.value)}
                            placeholder="Describe what you know…"
                            className="w-full resize-y rounded-xl border border-white/10 bg-[#090f1b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/10"
                          />
                        ) : (
                          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                            {(field.options || []).map(option => {
                              const selected = field.type === 'radio'
                                ? answers[field.id] === option
                                : Array.isArray(answers[field.id]) && (answers[field.id] as string[]).includes(option);
                              return (
                                <label key={option} className={cx('flex cursor-pointer items-start gap-3 rounded-xl border p-3.5 text-sm transition', selected ? 'border-cyan-300/50 bg-cyan-300/[0.08] text-white' : 'border-white/10 bg-[#0b111d] text-slate-300 hover:border-white/20')}>
                                  <input
                                    type={field.type === 'radio' ? 'radio' : 'checkbox'}
                                    name={field.id}
                                    checked={selected}
                                    onChange={e => {
                                      if (field.type === 'radio') setAnswer(field.id, option);
                                      else {
                                        const current = Array.isArray(answers[field.id]) ? answers[field.id] as string[] : [];
                                        setAnswer(field.id, e.target.checked ? [...current, option] : current.filter(item => item !== option));
                                      }
                                    }}
                                    className="mt-0.5 accent-cyan-300"
                                  />
                                  <span className="leading-5">{option}</span>
                                </label>
                              );
                            })}
                          </div>
                        )}
                      </fieldset>
                    ))}
                  </div>

                  <div className="mt-7 space-y-3 border-t border-white/10 pt-6">
                    <button type="submit" disabled={loadingAssessment} className="flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-300 px-5 py-4 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60">
                      {loadingAssessment ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                      {loadingAssessment ? 'Assessing against BIS evidence…' : 'Assess applicable standard'}
                      {!loadingAssessment && <ArrowRight className="h-4 w-4" />}
                    </button>
                    <p className="text-center text-[11px] leading-5 text-slate-500">Preliminary guidance only. A catalogue match or AI response is not an official BIS determination.</p>
                  </div>
                </form>
              </>
            )}

            {result && (
              <section aria-live="polite" className="rounded-2xl border border-emerald-300/20 bg-[#101b1c] p-5 sm:p-7">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-emerald-200"><CheckCircle2 className="h-5 w-5" /><h2 className="text-lg font-semibold text-white">Assessment response</h2></div>
                  {typeof result.confidence === 'number' && <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-300">Evidence confidence: {Math.round(result.confidence * 100)}%</span>}
                </div>
                {result.insufficient_evidence && <p className="mb-4 rounded-lg border border-amber-300/20 bg-amber-300/[0.06] p-3 text-xs text-amber-100">The knowledge base indicates that evidence is insufficient for a confident conclusion.</p>}
                <div className="whitespace-pre-wrap text-sm leading-7 text-slate-200">{result.content || 'The assessment service returned no explanation.'}</div>
                {(result.sources || []).length > 0 && (
                  <div className="mt-6 border-t border-white/10 pt-5">
                    <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Sources returned by backend</h3>
                    <div className="space-y-2">
                      {result.sources!.map((source, index) => (
                        <div key={index} className="rounded-lg border border-white/10 bg-black/10 p-3 text-xs">
                          <p className="font-medium text-slate-200">{source.title || source.standard_code || source.source || `Source ${index + 1}`}</p>
                          {source.clause && <p className="mt-1 text-slate-400">{source.clause}</p>}
                          {source.url && <a href={source.url} target="_blank" rel="noreferrer" className="mt-1 inline-block text-cyan-200 underline underline-offset-2">Open source ↗</a>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {(result.warnings || []).length > 0 && <ul className="mt-4 list-disc space-y-1 pl-5 text-xs text-amber-200">{result.warnings!.map((warning, i) => <li key={i}>{warning}</li>)}</ul>}
                <div className="mt-6 flex flex-col gap-3 border-t border-white/10 pt-5 sm:flex-row">
                  <button type="button" onClick={() => { setResult(null); window.scrollTo({ top: 0, behavior: 'smooth' }); }} className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 px-4 py-3 text-sm text-slate-200 hover:bg-white/[0.04]"><ArrowLeft className="h-4 w-4" /> Review answers</button>
                  <button type="button" onClick={reset} className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 px-4 py-3 text-sm text-slate-200 hover:bg-white/[0.04]"><RotateCcw className="h-4 w-4" /> Start new assessment</button>
                </div>
              </section>
            )}
          </main>

          <aside className="space-y-4">
            <section className="rounded-2xl border border-white/10 bg-[#101725] p-5">
              <h2 className="text-sm font-semibold text-white">How it works</h2>
              <ol className="mt-4 space-y-4">
                {[
                  ['01', 'Research', 'Retrieve catalogue candidates and indexed scope evidence.'],
                  ['02', 'Differentiate', 'Ask only product-specific questions returned by the backend.'],
                  ['03', 'Assess', 'Send product facts and evidence to the grounded RAG chat endpoint.'],
                ].map(([number, title, description]) => (
                  <li key={number} className="flex gap-3">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-cyan-300/20 bg-cyan-300/[0.07] font-mono text-[10px] text-cyan-200">{number}</span>
                    <div><p className="text-xs font-semibold text-slate-200">{title}</p><p className="mt-1 text-xs leading-5 text-slate-500">{description}</p></div>
                  </li>
                ))}
              </ol>
            </section>
            <section className="rounded-2xl border border-amber-300/20 bg-amber-300/[0.05] p-5">
              <div className="flex items-start gap-2.5"><ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-200" /><div><h2 className="text-xs font-semibold text-amber-100">Important distinction</h2><p className="mt-2 text-xs leading-5 text-amber-100/70">Catalogue metadata identifies records to investigate; it does not prove applicability, currency, or mandatory status. Confirm regulatory status against current official BIS notifications and QCOs.</p></div></div>
            </section>
            {schema?.revisionPolicy && <section className="rounded-2xl border border-white/10 bg-[#101725] p-5"><h2 className="text-xs font-semibold text-slate-300">Revision handling policy</h2><p className="mt-2 text-xs leading-5 text-slate-500">{schema.revisionPolicy}</p></section>}
          </aside>
        </div>
      </div>
    </div>
  );
};
