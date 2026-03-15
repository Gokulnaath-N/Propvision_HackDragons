import React from 'react';
import RoomCard from './RoomCard';

const ModelBadge = ({ meta }) => {
  if (!meta || !meta.model_used) return null;
  const isGemini = meta.model_used.includes('gemini');
  return (
    <div className="flex items-center gap-3 mb-6 px-4 py-2 rounded-full border border-border bg-background w-fit shadow-sm">
      <span className={`text-xs font-bold tracking-wider uppercase ${isGemini ? 'text-[var(--home-cyan)]' : 'text-[var(--home-amber)]'}`}>
        {isGemini ? 'Gemini 2.5 Flash' : 'Llama 3.3 70B'}
      </span>
      <span className="w-1 h-1 rounded-full bg-border" />
      <span className="text-xs text-textSecondary font-mono">{meta.latency_ms}ms</span>
      <span className="w-1 h-1 rounded-full bg-border" />
      <span className="text-xs text-textSecondary truncate max-w-[200px]" title={meta.reasons?.[0]}>
        {meta.reasons?.[0] || 'Unknown reason'}
      </span>
    </div>
  );
};

export default function ResultsGrid({ results, meta }) {
  if (!results || !results.length) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 w-full mt-24">
        <div className="w-16 h-16 rounded-full bg-panel flex items-center justify-center text-textSecondary mb-4">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        </div>
        <h3 className="text-xl font-semibold text-textPrimary">Search for properties</h3>
        <p className="text-sm text-textSecondary mt-2 max-w-sm text-center">
          Enter a query like "bright minimalist living room" to discover properties that match your aesthetic.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full">
      {meta && <ModelBadge meta={meta} />}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mt-4">
        {results.map((listing, index) => (
          <RoomCard key={listing.id || index} listing={listing} />
        ))}
      </div>
    </div>
  );
}
