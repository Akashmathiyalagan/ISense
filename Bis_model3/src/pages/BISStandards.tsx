import React, { useState } from 'react';
import { Search, Shield, BookOpen, ExternalLink, AlertCircle, Database } from 'lucide-react';
import { applicationApi } from '../services/applicationApi';
import { BISStandard } from '../types/application';
import { PageHeader } from '../components/layout/PageHeader';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';

export const BISStandards: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [standards, setStandards] = useState<BISStandard[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedStandard, setSelectedStandard] = useState<BISStandard | null>(null);

  const handleSearch = async (query = searchQuery) => {
    setIsSearching(true);
    const results = await applicationApi.searchBISStandards(query);
    setStandards(results);
    setIsSearching(false);
  };

  React.useEffect(() => {
    handleSearch('');
  }, []);

  const popularSearches = ['Solar Inverter', 'Ceiling Fan', 'Smart Plug', 'Lithium Battery', 'LED bulb', 'Smartphone', 'Water Heater'];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Find BIS Information"
        description="Search applicable Indian Standards and regulatory compliance schedules from the configured BIS knowledge base."
      />

      {/* Mandatory Regulatory Grounding Disclaimer */}
      <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200 text-xs text-blue-900 flex items-start gap-3">
        <Database className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <p className="font-semibold text-slate-900">Configured BIS Knowledge Base Grounding Notice:</p>
          <p className="text-slate-600 mt-0.5">
            Every entry listed below is retrieved directly from our configured BIS regulatory repository. Standards are cited for technical guidance and pre-submission readiness; official notifications and Gazette amendments are published exclusively by the Bureau of Indian Standards.
          </p>
        </div>
      </div>

      {/* Search Input Box */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Enter product name, IS number or keyword... (e.g. LED bulb, IS 16102)"
              className="w-full bg-slate-50 border border-slate-300 rounded-xl pl-11 pr-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
            />
          </div>
          <Button
            type="button"
            variant="primary"
            onClick={() => handleSearch()}
            isLoading={isSearching}
            className="w-full sm:w-auto px-6 py-3"
          >
            Search Knowledge Base
          </Button>
        </div>

        {/* Popular chips */}
        <div className="flex items-center gap-2 flex-wrap pt-2 text-xs">
          <span className="text-slate-400 font-medium">Quick Suggestions:</span>
          {popularSearches.map((term) => (
            <button
              key={term}
              onClick={() => {
                setSearchQuery(term);
                handleSearch(term);
              }}
              className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-600 border border-slate-200 transition-colors cursor-pointer text-[11px]"
            >
              {term}
            </button>
          ))}
        </div>
      </div>

      {/* Search Results */}
      <div className="space-y-4">
        <div className="flex items-center justify-between text-xs text-slate-500 px-1">
          <span>Search Results ({standards.length} retrieved from KB)</span>
          <span className="text-emerald-700 font-medium">● Verified KB Source</span>
        </div>

        {standards.length === 0 ? (
          <div className="bg-white p-8 rounded-xl border border-slate-200 text-center">
            <BookOpen className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-800">No matching standards found</h4>
            <p className="text-xs text-slate-500 mt-1">
              Try searching with another keyword or product category name.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {standards.map((std) => (
              <div
                key={std.id}
                className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs hover:border-blue-300 transition-all space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap mb-1.5">
                      <span className="font-mono font-bold text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-md">
                        {std.isNumber}
                      </span>
                      <Badge variant="neutral">{std.category}</Badge>
                      <Badge variant="blue">{std.mandatoryStatus}</Badge>
                    </div>
                    <h3 className="text-base font-bold text-slate-900">{std.title}</h3>
                  </div>

                  <span className="text-[11px] text-slate-400 shrink-0 font-mono">
                    Updated: {std.lastUpdated}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">{std.description}</p>

                {/* Grounded Source Tag */}
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex items-center gap-2 text-xs text-slate-600">
                  <Shield className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>
                    <strong className="text-slate-800">Authorized Source: </strong>
                    {std.source}
                  </span>
                </div>

                {/* Relevant Sections */}
                {std.relevantSections && std.relevantSections.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-slate-700 mb-1.5">Key Relevant Sections:</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {std.relevantSections.map((sec, i) => (
                        <div
                          key={i}
                          className="text-[11px] bg-slate-50/70 p-2 rounded border border-slate-200/80 text-slate-700 flex items-center gap-2"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0" />
                          <span className="truncate">{sec}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">
                    Source: Configured BIS Knowledge Base Schema
                  </span>
                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      alert(`Viewing official metadata record for ${std.isNumber} from configured repository.`);
                    }}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 cursor-pointer"
                  >
                    <span>View Source Documentation</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
