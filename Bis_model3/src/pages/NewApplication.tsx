import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Check,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  ShieldCheck,
  AlertCircle,
  FileText,
  UploadCloud,
  CheckCircle2,
  Clock,
  Layers,
  ChevronDown,
} from 'lucide-react';
import { useApplications } from '../hooks/useApplications';
import { PageHeader } from '../components/layout/PageHeader';
import { Button } from '../components/common/Button';
import { ProgressBar } from '../components/common/ProgressBar';
import {
  detectProductStandard,
  BIS_STANDARDS_CATALOG,
  DetectedStandard,
} from '../utils/bisMatcher';

export const NewApplication: React.FC = () => {
  const navigate = useNavigate();
  const { createApplication } = useApplications();

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);

  // Form State
  const [formData, setFormData] = useState({
    productName: '',
    productCategory: 'Solar & Renewable Equipment',
    manufacturer: 'Lumen Systems Pvt Ltd',
    countryOfOrigin: 'India',
    description: '',
  });

  const [detectedStandard, setDetectedStandard] = useState<DetectedStandard>(() =>
    detectProductStandard('', 'Solar & Renewable Equipment')
  );

  const categories = [
    'Solar & Renewable Equipment',
    'Electronics & IT Products',
    'Household Electrical Appliances',
    'Lighting & Electrotechnical',
    'Smart Devices & IoT',
    'Power Supplies & Chargers',
    'Consumer Electronics',
    'Automotive & Road Safety',
    'Consumer Goods & Toys',
    'Civil Engineering & Construction',
    'Food & Beverages',
    'Other / Unspecified',
  ];

  const handleNextStep1 = () => {
    if (!formData.productName.trim()) return;
    setIsAnalyzing(true);
    setCurrentStep(2);

    // Intelligently detect applicable standard
    const matched = detectProductStandard(formData.productName, formData.productCategory);
    setDetectedStandard(matched);

    setTimeout(() => {
      setIsAnalyzing(false);
    }, 900);
  };

  const handleSelectCustomStandard = (stdCode: string) => {
    const found = BIS_STANDARDS_CATALOG.find((s) => s.standardCode === stdCode);
    if (found) {
      setDetectedStandard(found);
    }
  };

  const handleFinalSubmit = async () => {
    setIsSubmitting(true);
    try {
      const created = await createApplication({
        productName: formData.productName,
        productCategory: formData.productCategory,
        manufacturer: formData.manufacturer,
        countryOfOrigin: formData.countryOfOrigin,
        description: formData.description,
        standardCode: detectedStandard.standardCode,
        standardTitle: detectedStandard.standardTitle,
      });
      setIsSubmitting(false);
      navigate(`/applications/${created.id}`);
    } catch {
      setIsSubmitting(false);
      navigate('/applications');
    }
  };

  const steps = [
    { num: 1, title: 'Product Info' },
    { num: 2, title: 'Analysis' },
    { num: 3, title: 'Requirements' },
    { num: 4, title: 'Documents' },
    { num: 5, title: 'Review & Confirm' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader
        title="Create New Application"
        subtitle="Step-by-step guided application creation with automated BIS standard identification"
      />

      {/* Wizard Progress Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex items-center justify-between mb-2">
          {steps.map((s) => (
            <div key={s.num} className="flex flex-col items-center">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  currentStep > s.num
                    ? 'bg-emerald-600 text-white'
                    : currentStep === s.num
                    ? 'bg-blue-600 text-white ring-4 ring-blue-100'
                    : 'bg-slate-100 text-slate-400'
                }`}
              >
                {currentStep > s.num ? <Check className="w-4 h-4" /> : s.num}
              </div>
              <span
                className={`text-[11px] font-medium mt-1.5 hidden sm:block ${
                  currentStep === s.num ? 'text-blue-600 font-semibold' : 'text-slate-500'
                }`}
              >
                {s.title}
              </span>
            </div>
          ))}
        </div>
        <ProgressBar
          progress={((currentStep - 1) / (steps.length - 1)) * 100}
          height="h-1.5"
          color="bg-blue-600"
          showLabel={false}
        />
      </div>

      {/* STEP 1: Product Information */}
      {currentStep === 1 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-5">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-base font-semibold text-slate-900">Step 1: Product Information</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Enter your product details to identify potentially relevant BIS standards and certification requirements.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Product Name / Model Designation *
              </label>
              <input
                type="text"
                required
                value={formData.productName}
                onChange={(e) => {
                  const val = e.target.value;
                  setFormData({ ...formData, productName: val });
                  if (val.trim()) {
                    setDetectedStandard(detectProductStandard(val, formData.productCategory));
                  }
                }}
                placeholder="e.g. Smart Solar Inverter 5kW, BLDC Ceiling Fan 1200mm, 5G Smartphone"
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Product Category *
              </label>
              <select
                value={formData.productCategory}
                onChange={(e) => {
                  const cat = e.target.value;
                  setFormData({ ...formData, productCategory: cat });
                  setDetectedStandard(detectProductStandard(formData.productName, cat));
                }}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Country of Origin *
              </label>
              <input
                type="text"
                required
                value={formData.countryOfOrigin}
                onChange={(e) => setFormData({ ...formData, countryOfOrigin: e.target.value })}
                placeholder="e.g. India, Japan, Germany"
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Manufacturer / Brand Organization
              </label>
              <input
                type="text"
                value={formData.manufacturer}
                onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
                placeholder="Company Name"
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Technical Description &amp; Specifications
              </label>
              <textarea
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief technical description, rated voltages, operational wattages, casing materials, or intended applications..."
                className="w-full bg-white border border-slate-300 rounded-lg p-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Real-Time Live Standard Preview Pill */}
          {formData.productName.trim() && (
            <div className="p-3 bg-blue-50/70 rounded-xl border border-blue-200/80 flex items-center justify-between text-xs animate-in fade-in">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-600 shrink-0" />
                <span>
                  Detected Standard: <strong className="text-blue-900">{detectedStandard.standardCode}</strong>
                </span>
              </div>
              <span className="text-[11px] text-blue-700 font-medium hidden sm:inline">
                {detectedStandard.scheme}
              </span>
            </div>
          )}

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <Button
              variant="primary"
              onClick={handleNextStep1}
              disabled={!formData.productName.trim()}
              icon={<ArrowRight className="w-4 h-4" />}
              iconPosition="right"
            >
              Analyse Applicable Standard
            </Button>
          </div>
        </div>
      )}

      {/* STEP 2: Product Analysis */}
      {currentStep === 2 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-5">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-base font-semibold text-slate-900">Step 2: BIS Standard Identification</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Automated standard matching grounded in official Bureau of Indian Standards regulatory schedules.
            </p>
          </div>

          {isAnalyzing ? (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <Sparkles className="w-10 h-10 text-blue-600 animate-spin mb-3" />
              <h4 className="text-base font-semibold text-slate-900">ISense is analysing "{formData.productName}"...</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Querying BIS Electrotechnical, IT &amp; Mechanical Division repositories for product-specific safety standards.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-blue-50 border border-blue-200">
                <div className="flex items-center gap-2 text-xs font-semibold text-blue-800 mb-1">
                  <ShieldCheck className="w-4 h-4 text-blue-600" />
                  <span>Potentially Relevant BIS Information Identified</span>
                </div>
                <h4 className="text-base font-bold text-slate-900 mt-1">
                  {detectedStandard.standardCode} — {detectedStandard.standardTitle}
                </h4>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  Based on your product designation <strong>"{formData.productName}"</strong>, this standard governs safety, performance, and certification prerequisites.
                </p>
                <div className="mt-2.5 p-2.5 bg-white/80 rounded-lg text-xs text-slate-700 border border-blue-100">
                  <strong>Technical Scope:</strong> {detectedStandard.scopeSummary}
                </div>
              </div>

              {/* Standard Selector / Override */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-700">Need to select a different standard?</span>
                  <span className="text-[11px] text-slate-400">Custom selection available</span>
                </div>
                <select
                  value={detectedStandard.standardCode}
                  onChange={(e) => handleSelectCustomStandard(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {BIS_STANDARDS_CATALOG.map((std) => (
                    <option key={std.standardCode} value={std.standardCode}>
                      {std.standardCode} — {std.standardTitle}
                    </option>
                  ))}
                </select>
              </div>

              {/* Statutory Non-legal Callout */}
              <div className="p-4 rounded-lg bg-amber-50/70 border border-amber-200/90 text-xs text-amber-900 flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                <div className="leading-relaxed">
                  <strong>Review Required:</strong> This assessment represents <em>potentially relevant BIS information</em> based on keyword and category heuristics. Official certification decisions and approvals remain solely with the Bureau of Indian Standards.
                </div>
              </div>

              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500">Scheme Classification:</span>
                  <span className="font-semibold text-slate-800">{detectedStandard.scheme}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Governing Division:</span>
                  <span className="font-semibold text-slate-800">{detectedStandard.division}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Estimated Prerequisite Count:</span>
                  <span className="font-semibold text-slate-800">
                    {detectedStandard.checklist.length + 2} Compliance Artifacts
                  </span>
                </div>
              </div>

              <div className="flex justify-between pt-4 border-t border-slate-100">
                <Button variant="outline" onClick={() => setCurrentStep(1)} icon={<ArrowLeft className="w-4 h-4" />}>
                  Back
                </Button>
                <Button variant="primary" onClick={() => setCurrentStep(3)} icon={<ArrowRight className="w-4 h-4" />} iconPosition="right">
                  Proceed to Requirements
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* STEP 3: Requirements */}
      {currentStep === 3 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-5">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-base font-semibold text-slate-900">Step 3: Requirements Checklist</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Preliminary checklist generated for <strong>{detectedStandard.standardCode}</strong>
            </p>
          </div>

          <div className="space-y-3">
            {[
              { title: 'Product Technical Data Sheet', desc: 'Operating voltage, wattage, and casing drawings', checked: true },
              { title: 'Manufacturer Incorporation & Factory License', desc: 'Valid industrial license, GSTIN, and manufacturing site address proof', checked: true },
              ...detectedStandard.checklist.map((item, idx) => ({
                title: item,
                desc: `Mandatory testing verification protocol under ${detectedStandard.standardCode}`,
                checked: false,
              })),
            ].map((item, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                <div className="mt-0.5">
                  {item.checked ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <Clock className="w-4 h-4 text-slate-400" />
                  )}
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-800">{item.title}</p>
                  <p className="text-[11px] text-slate-500">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <Button variant="outline" onClick={() => setCurrentStep(2)} icon={<ArrowLeft className="w-4 h-4" />}>
              Back
            </Button>
            <Button variant="primary" onClick={() => setCurrentStep(4)} icon={<ArrowRight className="w-4 h-4" />} iconPosition="right">
              Proceed to Documents
            </Button>
          </div>
        </div>
      )}

      {/* STEP 4: Documents Upload Simulation */}
      {currentStep === 4 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-5">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-base font-semibold text-slate-900">Step 4: Upload Required Documents</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Upload preliminary technical files for <strong>{detectedStandard.standardCode}</strong>. You can upload or replace documents anytime from the Document Management page.
            </p>
          </div>

          <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center bg-slate-50/50">
            <UploadCloud className="w-10 h-10 text-blue-600 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-800">Upload Product Technical Dossier</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Attach product specification sheet, test reports, or factory layout diagrams (PDF, DOCX, PNG up to 15MB)
            </p>
            <div className="mt-4 flex justify-center gap-2">
              <label className="cursor-pointer">
                <span className="py-2 px-4 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors inline-block">
                  Select Files
                </span>
                <input type="file" className="hidden" />
              </label>
            </div>
          </div>

          <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Document upload is optional right now. You can create your application first and upload documents later.</span>
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <Button variant="outline" onClick={() => setCurrentStep(3)} icon={<ArrowLeft className="w-4 h-4" />}>
              Back
            </Button>
            <Button variant="primary" onClick={() => setCurrentStep(5)} icon={<ArrowRight className="w-4 h-4" />} iconPosition="right">
              Proceed to Review
            </Button>
          </div>
        </div>
      )}

      {/* STEP 5: Review & Confirm */}
      {currentStep === 5 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-5">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-base font-semibold text-slate-900">Step 5: Review &amp; Create Application</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Verify your information before initializing the certification assistance record.
            </p>
          </div>

          <div className="bg-slate-50 rounded-xl p-5 border border-slate-200 space-y-3 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <span className="text-slate-400 block">Product Designation:</span>
                <span className="font-semibold text-slate-900 text-sm">{formData.productName}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Product Category:</span>
                <span className="font-semibold text-slate-900">{formData.productCategory}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Manufacturer:</span>
                <span className="font-semibold text-slate-900">{formData.manufacturer}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Country of Origin:</span>
                <span className="font-semibold text-slate-900">{formData.countryOfOrigin}</span>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-200">
              <span className="text-slate-400 block mb-1">Applicable Indian Standard Reference:</span>
              <div className="font-semibold text-blue-700 bg-blue-50 px-3 py-2 rounded-lg border border-blue-200 space-y-0.5">
                <div className="text-sm font-bold">{detectedStandard.standardCode}</div>
                <div className="text-xs text-blue-900 font-medium">{detectedStandard.standardTitle}</div>
                <div className="text-[11px] text-blue-600 font-normal">{detectedStandard.scheme}</div>
              </div>
            </div>
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <Button variant="outline" onClick={() => setCurrentStep(4)} icon={<ArrowLeft className="w-4 h-4" />}>
              Back
            </Button>
            <Button
              variant="primary"
              onClick={handleFinalSubmit}
              isLoading={isSubmitting}
              icon={<Check className="w-4 h-4" />}
            >
              Create Application
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
