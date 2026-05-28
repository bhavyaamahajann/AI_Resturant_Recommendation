import { useEffect, useMemo, useState } from 'react';
import MaterialIcon from '../components/ui/MaterialIcon';

const MESSAGES = [
  'Filtering dataset...',
  'Ranking & generating explanations...',
  'Applying flavor profiles...',
  'Personalizing concierge notes...',
];

export default function SearchingScreen() {
  const [idx, setIdx] = useState(0);
  const message = useMemo(() => MESSAGES[idx % MESSAGES.length], [idx]);

  useEffect(() => {
    const t = setInterval(() => setIdx((i) => i + 1), 3000);
    return () => clearInterval(t);
  }, []);

  return (
    <main className="flex-grow w-full max-w-container-max mx-auto px-[16px] md:px-[32px] py-lg md:py-xl">
      <section className="mb-xl bg-surface-container-low border border-outline-variant rounded-xl p-lg flex flex-col md:flex-row items-center gap-lg">
        <div className="relative w-20 h-20 flex-shrink-0">
          <div className="absolute inset-0 rounded-full border-4 border-primary/10" />
          <div className="absolute inset-0 rounded-full border-4 border-primary border-t-transparent animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <MaterialIcon
              name="cognition"
              className="text-primary text-[32px]"
            />
          </div>
        </div>

        <div className="flex-grow text-center md:text-left">
          <h2 className="text-headline-sm font-headline-sm text-on-surface mb-xs">
            Refining Your Selection
          </h2>
          <div className="flex flex-col gap-xs">
            <p className="text-on-surface-variant font-body-md text-body-md flex items-center justify-center md:justify-start gap-2 transition-all duration-500">
              {message}
            </p>
            <div className="flex items-center justify-center md:justify-start gap-1">
              <div className="w-2 h-2 rounded-full bg-primary/40 animate-typing [animation-delay:-0.32s]" />
              <div className="w-2 h-2 rounded-full bg-primary/70 animate-typing [animation-delay:-0.16s]" />
              <div className="w-2 h-2 rounded-full bg-primary animate-typing" />
            </div>
          </div>
        </div>

        <div className="hidden md:block w-64 h-24 rounded-lg bg-surface-container-highest border border-outline-variant ai-shimmer" />
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden"
          >
            <div className="aspect-video w-full bg-surface-container-highest ai-shimmer" />
            <div className="p-md space-y-md">
              <div className="space-y-xs">
                <div className="h-6 w-3/4 bg-surface-container-highest ai-shimmer rounded" />
                <div className="h-4 w-1/2 bg-surface-container-highest ai-shimmer rounded" />
              </div>
              <div className="flex gap-xs">
                <div className="h-6 w-12 bg-surface-container-highest ai-shimmer rounded-full" />
                <div className="h-6 w-12 bg-surface-container-highest ai-shimmer rounded-full" />
                <div className="h-6 w-12 bg-surface-container-highest ai-shimmer rounded-full" />
              </div>
              <div className="pt-sm border-t border-outline-variant/30">
                <div className="flex gap-sm items-start">
                  <div className="w-5 h-5 rounded-full bg-surface-container-highest ai-shimmer flex-shrink-0" />
                  <div className="space-y-xs flex-grow">
                    <div className="h-3 w-full bg-surface-container-highest ai-shimmer rounded" />
                    <div className="h-3 w-5/6 bg-surface-container-highest ai-shimmer rounded" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-xl text-center max-w-2xl mx-auto space-y-sm">
        <p className="text-label-sm font-label-sm text-secondary uppercase tracking-[0.2em]">
          Authentic Intelligence
        </p>
        <p className="text-body-lg font-body-lg text-on-surface-variant italic">
          "We're analyzing local culinary trends and cross-referencing your
          preferences to ensure every recommendation is worthy of your palate."
        </p>
      </div>
    </main>
  );
}

