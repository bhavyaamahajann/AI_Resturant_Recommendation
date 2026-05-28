import { useMemo, useState } from 'react';
import MaterialIcon from '../components/ui/MaterialIcon';

function formatRupees(n) {
  if (typeof n !== 'number' || Number.isNaN(n)) return null;
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(n);
}

function getHighlightsFromExplanation(explanation) {
  if (!explanation) return [];
  // lightweight heuristic: pick a few short fragments separated by commas/semicolons.
  const parts = String(explanation)
    .split(/[,;•]/g)
    .map((s) => s.trim())
    .filter(Boolean)
    .filter((s) => s.length >= 6 && s.length <= 22);
  return Array.from(new Set(parts)).slice(0, 3);
}

export default function ResultsScreen({ result, onRefine }) {
  const [expanded, setExpanded] = useState(() => new Set());

  const { summary, recommendations = [] } = result || {};

  const top = recommendations[0];
  const second = recommendations[1];
  const rest = recommendations.slice(2, 5);

  const toggle = (id) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const title = useMemo(() => {
    const c = recommendations?.[0]?.cuisine;
    return c ? `Curated selection for "${c}"` : 'AI-curated selection';
  }, [recommendations]);

  return (
    <>
      <main className="max-w-container-max mx-auto px-[16px] md:px-[32px] mt-sm">
        <section className="mt-md mb-xl">
          <div className="bg-surface-container-low border border-outline-variant rounded-xl p-md md:p-lg relative overflow-hidden ai-shimmer">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-md relative z-10">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <MaterialIcon
                    name="auto_awesome"
                    className="text-primary"
                  />
                  <span className="text-label-bold font-label-bold text-primary tracking-widest">
                    AI ANALYSIS COMPLETE
                  </span>
                </div>
                <h2 className="text-headline-sm font-headline-sm text-on-surface mb-2">
                  {title}
                </h2>
                {summary ? (
                  <p className="text-body-md font-body-md text-on-surface-variant max-w-3xl">
                    {summary}
                  </p>
                ) : (
                  <p className="text-body-md font-body-md text-on-surface-variant max-w-3xl">
                    We ranked the best matches based on your preferences and the
                    dataset signals (rating, cost, and cuisine fit).
                  </p>
                )}
              </div>

              <div className="hidden lg:block w-48 h-24 rounded-lg bg-surface-container-highest border border-outline-variant flex items-center justify-center">
                <div className="text-center">
                  <div className="text-headline-md font-headline-md text-primary">
                    98%
                  </div>
                  <div className="text-label-sm font-label-sm text-on-surface-variant">
                    Match Score
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-12 gap-gutter">
          {top && (
            <div className="md:col-span-8 group relative bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden hover:border-primary/30 transition-all duration-300">
              <div className="relative aspect-[16/9] w-full overflow-hidden bg-surface-container-highest">
                <div className="absolute inset-0 ai-shimmer opacity-50" />
                <div className="absolute top-4 left-4 bg-primary text-on-primary px-3 py-1.5 rounded font-label-bold text-label-bold shadow-lg">
                  #1 AI PICK
                </div>
              </div>
              <div className="p-md md:p-lg">
                <div className="flex justify-between items-start mb-sm">
                  <div>
                    <h3 className="text-headline-md font-headline-md text-on-surface">
                      {top.name || `Restaurant #${top.rank ?? 1}`}
                    </h3>
                    <p className="text-body-md font-body-md text-on-surface-variant flex items-center gap-1">
                      <MaterialIcon name="location_on" className="text-[16px]" />
                      {top.location || 'Nearby'}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center justify-end text-primary mb-1">
                      <MaterialIcon
                        name="star"
                        className="text-[18px]"
                      />
                      <span className="text-headline-sm font-headline-sm ml-1">
                        {typeof top.rating === 'number' ? top.rating.toFixed(1) : '—'}
                      </span>
                    </div>
                    <span className="text-label-sm font-label-sm text-on-surface-variant">
                      {top.estimated_cost != null
                        ? `₹${formatRupees(top.estimated_cost)} for two`
                        : 'Cost unavailable'}
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 mb-md">
                  {getHighlightsFromExplanation(top.explanation).map((h) => (
                    <span
                      key={h}
                      className="bg-surface-variant text-on-surface-variant px-3 py-1 rounded-full text-label-sm font-label-sm"
                    >
                      {h}
                    </span>
                  ))}
                </div>

                <div className="border-l-4 border-primary bg-surface-container-low p-md rounded-r-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <MaterialIcon
                      name="auto_awesome"
                      className="text-primary text-[18px]"
                    />
                    <span className="text-label-bold font-label-bold text-primary">
                      WHY THIS PICK
                    </span>
                  </div>
                  <p
                    className={[
                      'text-body-md font-body-md text-on-surface-variant leading-relaxed',
                      expanded.has(top.restaurant_id) ? '' : 'line-clamp-3',
                    ].join(' ')}
                  >
                    {top.explanation || 'AI explanation unavailable.'}
                  </p>
                  <button
                    type="button"
                    onClick={() => toggle(top.restaurant_id)}
                    className="mt-2 text-primary font-label-bold text-label-bold flex items-center gap-1 hover:underline"
                  >
                    {expanded.has(top.restaurant_id) ? 'Show Less' : 'Read More'}{' '}
                    <MaterialIcon name="arrow_forward" className="text-[14px]" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {second && (
            <div className="md:col-span-4 group bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden hover:border-primary/30 transition-all duration-300">
              <div className="relative aspect-[4/3] w-full bg-surface-container-highest overflow-hidden">
                <div className="absolute inset-0 ai-shimmer opacity-50" />
                <div className="absolute top-3 left-3 bg-secondary text-on-secondary px-2 py-1 rounded font-label-bold text-label-bold shadow-md">
                  #{second.rank ?? 2}
                </div>
              </div>
              <div className="p-md">
                <h3 className="text-headline-sm font-headline-sm text-on-surface">
                  {second.name || `Restaurant #${second.rank ?? 2}`}
                </h3>
                <div className="flex justify-between items-center mt-xs">
                  <span className="text-body-md font-body-md text-on-surface-variant">
                    {second.location || 'Nearby'}
                  </span>
                  <div className="flex items-center text-primary">
                    <MaterialIcon
                      name="star"
                      className="text-[16px]"
                    />
                    <span className="text-label-bold font-label-bold ml-1">
                      {typeof second.rating === 'number'
                        ? second.rating.toFixed(1)
                        : '—'}
                    </span>
                  </div>
                </div>
                <p className="text-label-sm font-label-sm text-on-surface-variant mt-1">
                  {second.estimated_cost != null
                    ? `₹${formatRupees(second.estimated_cost)} for two`
                    : 'Cost unavailable'}
                  {second.cuisine ? ` • ${second.cuisine}` : ''}
                </p>

                <div className="mt-md pt-md border-t border-outline-variant">
                  <div className="flex items-center gap-1 mb-1">
                    <MaterialIcon
                      name="auto_awesome"
                      className="text-primary text-[16px]"
                    />
                    <span className="text-label-bold font-label-bold text-primary text-[10px] tracking-wider">
                      AI INSIGHT
                    </span>
                  </div>
                  <p
                    className={[
                      'text-body-md font-body-md text-on-surface-variant',
                      expanded.has(second.restaurant_id) ? '' : 'line-clamp-2',
                    ].join(' ')}
                  >
                    {second.explanation || 'AI explanation unavailable.'}
                  </p>
                  <button
                    type="button"
                    onClick={() => toggle(second.restaurant_id)}
                    className="text-primary text-label-sm font-label-sm mt-1"
                  >
                    {expanded.has(second.restaurant_id) ? 'Show Less' : 'Read More'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {rest.map((rec) => (
            <div
              key={rec.restaurant_id}
              className="md:col-span-4 bg-surface-container-lowest border border-outline-variant rounded-xl p-md hover:border-primary/30 transition-all"
            >
              <div className="flex gap-md">
                <div className="w-20 h-20 rounded-lg overflow-hidden flex-shrink-0 bg-surface-container-highest relative">
                  <div className="absolute inset-0 ai-shimmer opacity-60" />
                </div>
                <div className="flex-1">
                  <span className="text-label-bold font-label-bold text-secondary">
                    #{rec.rank ?? '—'}
                  </span>
                  <h4 className="text-body-lg font-headline-sm text-on-surface">
                    {rec.name || 'Restaurant'}
                  </h4>
                  <p className="text-body-md font-body-md text-on-surface-variant">
                    {rec.location || 'Nearby'}
                  </p>
                </div>
              </div>

              <div className="mt-md">
                <div className="flex flex-wrap gap-1 mb-md">
                  {getHighlightsFromExplanation(rec.explanation).map((h) => (
                    <span
                      key={h}
                      className="bg-surface-container text-on-surface-variant px-2 py-0.5 rounded text-[10px] font-label-bold uppercase tracking-tighter"
                    >
                      {h}
                    </span>
                  ))}
                </div>
                <div className="bg-surface-container-low border-l-2 border-primary/50 p-2 rounded-r">
                  <p
                    className={[
                      'text-[12px] text-on-surface-variant leading-snug',
                      expanded.has(rec.restaurant_id) ? '' : 'line-clamp-2',
                    ].join(' ')}
                  >
                    {rec.explanation || 'AI explanation unavailable.'}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </section>
      </main>

      <div className="fixed bottom-24 left-0 right-0 flex justify-center z-40 pointer-events-none md:bottom-28">
        <button
          type="button"
          onClick={onRefine}
          className="bg-on-background text-background px-6 py-3 rounded-full shadow-xl flex items-center gap-2 pointer-events-auto hover:bg-primary transition-all active:scale-95 border border-outline-variant/20"
        >
          <MaterialIcon name="tune" />
          <span className="font-label-bold text-label-bold tracking-wider">
            REFINE PREFERENCES
          </span>
        </button>
      </div>
    </>
  );
}

