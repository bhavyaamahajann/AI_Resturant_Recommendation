import { useEffect, useMemo, useState } from 'react';
import heroImg from '../assets/hero.png';
import MaterialIcon from '../components/ui/MaterialIcon';
import Typeahead from '../components/Typeahead';

const DEFAULT_PREFS = {
  location: '',
  cuisines: [],
  budget: '$', // $ | $$ | $$$ | $$$$
  top_n: 5,
  min_rating: 4.0,
  extras: [],
};

function clamp(n, min, max) {
  return Math.min(max, Math.max(min, n));
}

export default function PreferencesScreen({
  onSubmit,
  disabled = false,
  initialPreferences,
}) {
  const [prefs, setPrefs] = useState(() => ({
    ...DEFAULT_PREFS,
    ...(initialPreferences || {}),
  }));

  const [locationOptions, setLocationOptions] = useState([]);
  const [locationsLoading, setLocationsLoading] = useState(true);
  const [cuisineOptions, setCuisineOptions] = useState([]);
  const [cuisinesLoading, setCuisinesLoading] = useState(true);

  const [locationQuery, setLocationQuery] = useState(prefs.location || '');
  const [selectedCuisines, setSelectedCuisines] = useState(prefs.cuisines || []);

  const [extrasInput, setExtrasInput] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function loadLocations() {
      try {
        setLocationsLoading(true);
        const res = await fetch('/api/v1/locations');
        const data = await res.json();
        if (!cancelled) {
          setLocationOptions(Array.isArray(data?.locations) ? data.locations : []);
        }
      } catch {
        if (!cancelled) setLocationOptions([]);
      } finally {
        if (!cancelled) setLocationsLoading(false);
      }
    }

    async function loadCuisines() {
      try {
        setCuisinesLoading(true);
        const res = await fetch('/api/v1/cuisines');
        const data = await res.json();
        if (!cancelled) {
          setCuisineOptions(Array.isArray(data?.cuisines) ? data.cuisines : []);
        }
      } catch {
        if (!cancelled) setCuisineOptions([]);
      } finally {
        if (!cancelled) setCuisinesLoading(false);
      }
    }

    loadLocations();
    loadCuisines();

    return () => {
      cancelled = true;
    };
  }, []);

  const canSubmit = useMemo(() => {
    const loc = (locationQuery || prefs.location || '').trim();
    const cuis = selectedCuisines.length > 0;
    return loc.length > 0 && cuis;
  }, [locationQuery, selectedCuisines, prefs.location]);

  const removeExtra = (idx) => {
    setPrefs((p) => ({ ...p, extras: p.extras.filter((_, i) => i !== idx) }));
  };

  const addExtraFromInput = () => {
    const raw = extrasInput.trim();
    if (!raw) return;
    setPrefs((p) => {
      const exists = p.extras.some((x) => x.toLowerCase() === raw.toLowerCase());
      return exists ? p : { ...p, extras: [...p.extras, raw] };
    });
    setExtrasInput('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const finalLocation = (locationQuery || prefs.location || '').trim();
    const finalCuisine = (cuisineQuery || prefs.cuisine || '').trim();

    onSubmit?.({
      ...prefs,
      location: finalLocation,
      cuisine: finalCuisine,
      top_n: clamp(Number(prefs.top_n || 5), 1, 20),
      min_rating: clamp(Number(prefs.min_rating || 0), 0, 5),
      budget: prefs.budget || 'medium',
      extras: Array.isArray(prefs.extras) ? prefs.extras : [],
    });
  };

  return (
    <main className="max-w-container-max mx-auto px-[16px] md:px-[32px] pt-xl pb-xl">
      <section className="mb-xl relative overflow-hidden rounded-xl bg-surface-container-low p-md md:p-xl flex flex-col md:flex-row items-center gap-xl border border-outline-variant">
        <div className="flex-1 z-10 text-center md:text-left">
          <h2 className="text-display-lg-mobile md:text-display-lg font-display-lg mb-md text-on-surface">
            Find your next meal with AI precision
          </h2>
          <p className="text-body-lg font-body-lg text-on-surface-variant max-w-lg">
            Discover curated culinary experiences powered by advanced machine
            learning. Your palate, perfected.
          </p>
        </div>
        <div className="flex-1 w-full max-w-md aspect-[4/3] rounded-xl overflow-hidden shadow-sm relative border border-outline-variant">
          <img
            className="w-full h-full object-cover"
            alt="Hero"
            src={heroImg}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
        </div>
      </section>

      <div className="max-w-4xl mx-auto">
        <div className="bg-surface-container-lowest rounded-xl border border-outline-variant p-md md:p-lg">
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
              <div className="space-y-xs">
                <label className="text-label-bold font-label-bold text-on-surface-variant flex items-center gap-1">
                  <MaterialIcon name="location_on" className="text-[16px]" />
                  LOCATION
                </label>

                <div className="relative">
                  <Typeahead
                    id="location"
                    label={null}
                    placeholder={
                      locationsLoading
                        ? 'Loading locations…'
                        : 'Search neighborhood...'
                    }
                    options={locationOptions}
                    disabled={disabled || (locationsLoading && locationOptions.length === 0)}
                    value={locationQuery}
                    onChange={setLocationQuery}
                    onSelect={(loc) => {
                      setPrefs((p) => ({ ...p, location: loc }));
                      setLocationQuery(loc);
                    }}
                    helperText={null}
                  />
                  <MaterialIcon
                    name="expand_more"
                    className="absolute right-md top-1/2 -translate-y-1/2 text-secondary opacity-60 pointer-events-none"
                  />
                </div>
              </div>

              <div className="space-y-xs">
                <label className="text-label-bold font-label-bold text-on-surface-variant flex items-center gap-1">
                  <MaterialIcon name="restaurant" className="text-[16px]" />
                  CUISINE
                </label>

                <div className="relative">
                  <Typeahead
                    id="cuisine"
                    label={null}
                    placeholder={
                      cuisinesLoading ? 'Loading cuisines…' : 'E.g. Japanese, Fusion...'
                    }
                    options={cuisineOptions}
                    disabled={disabled || (cuisinesLoading && cuisineOptions.length === 0)}
                    value={cuisineQuery}
                    onChange={setCuisineQuery}
                    onSelect={(c) => {
                      setPrefs((p) => ({ ...p, cuisine: c }));
                      setCuisineQuery(c);
                    }}
                    helperText={null}
                  />
                  <MaterialIcon
                    name="search"
                    className="absolute right-md top-1/2 -translate-y-1/2 text-secondary opacity-60 pointer-events-none"
                  />
                </div>
              </div>

              <div className="space-y-xs">
                <label className="text-label-bold font-label-bold text-on-surface-variant">
                  BUDGET
                </label>
                <div className="flex bg-surface-container p-xs rounded h-11">
                  {[
                    ['low', 'Low'],
                    ['medium', 'Medium'],
                    ['high', 'High'],
                  ].map(([key, label]) => {
                    const active = prefs.budget === key;
                    return (
                      <button
                        key={key}
                        type="button"
                        disabled={disabled}
                        onClick={() => setPrefs((p) => ({ ...p, budget: key }))}
                        className={[
                          'flex-1 text-label-sm font-label-sm rounded transition-all',
                          active
                            ? 'bg-on-surface text-surface shadow-sm'
                            : 'text-on-surface opacity-70 hover:opacity-100',
                        ].join(' ')}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-xs">
                <label className="text-label-bold font-label-bold text-on-surface-variant">
                  NUMBER OF RESULTS
                </label>
                <div className="flex items-center bg-surface-container-low border border-outline-variant rounded overflow-hidden h-11">
                  <button
                    type="button"
                    disabled={disabled}
                    className="px-md h-full hover:bg-surface-variant transition-colors"
                    onClick={() =>
                      setPrefs((p) => ({ ...p, top_n: clamp((p.top_n || 5) - 1, 1, 20) }))
                    }
                  >
                    <MaterialIcon name="remove" className="text-on-surface text-[20px]" />
                  </button>
                  <span className="flex-1 text-center font-bold text-body-lg">
                    {prefs.top_n}
                  </span>
                  <button
                    type="button"
                    disabled={disabled}
                    className="px-md h-full hover:bg-surface-variant transition-colors"
                    onClick={() =>
                      setPrefs((p) => ({ ...p, top_n: clamp((p.top_n || 5) + 1, 1, 20) }))
                    }
                  >
                    <MaterialIcon name="add" className="text-on-surface text-[20px]" />
                  </button>
                </div>
              </div>

              <div className="md:col-span-2 space-y-md py-md border-t border-b border-outline-variant/30">
                <div className="flex justify-between items-center">
                  <label className="text-label-bold font-label-bold text-on-surface-variant">
                    MINIMUM RATING
                  </label>
                  <span className="text-primary font-bold text-body-lg">
                    {Number(prefs.min_rating).toFixed(1)}+ Stars
                  </span>
                </div>
                <input
                  className="w-full h-[2px] bg-outline-variant appearance-none slider-thumb cursor-pointer"
                  max="5"
                  min="0"
                  step="0.1"
                  type="range"
                  value={prefs.min_rating}
                  disabled={disabled}
                  onChange={(e) =>
                    setPrefs((p) => ({ ...p, min_rating: Number(e.target.value) }))
                  }
                />
              </div>

              <div className="md:col-span-2 space-y-xs">
                <label className="text-label-bold font-label-bold text-on-surface-variant">
                  EXTRAS
                </label>
                <div className="flex flex-wrap gap-sm bg-surface-container-low border border-outline-variant rounded p-sm min-h-[44px]">
                  {prefs.extras.map((ex, idx) => (
                    <span
                      key={`${ex}-${idx}`}
                      className="bg-primary text-on-primary px-3 py-1 rounded-full text-label-sm flex items-center gap-1"
                    >
                      {ex}
                      <button
                        type="button"
                        onClick={() => removeExtra(idx)}
                        className="material-symbols-outlined text-[14px]"
                      >
                        close
                      </button>
                    </span>
                  ))}
                  <input
                    className="bg-transparent outline-none text-body-md border-none focus:ring-0 px-2 flex-grow min-w-[120px]"
                    placeholder="Add more..."
                    type="text"
                    disabled={disabled}
                    value={extrasInput}
                    onChange={(e) => setExtrasInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addExtraFromInput();
                      }
                      if (e.key === ',' || e.key === 'Tab') {
                        if (extrasInput.trim()) {
                          e.preventDefault();
                          addExtraFromInput();
                        }
                      }
                      if (e.key === 'Backspace' && !extrasInput && prefs.extras.length) {
                        removeExtra(prefs.extras.length - 1);
                      }
                    }}
                    onBlur={() => addExtraFromInput()}
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-col md:flex-row gap-md mt-xl">
              <button
                type="submit"
                disabled={disabled || !canSubmit}
                className="flex-[2] bg-primary text-on-primary font-label-bold text-label-bold h-12 rounded-lg flex items-center justify-center gap-2 hover:shadow-lg transition-all active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <MaterialIcon name="auto_awesome" />
                Get Recommendations
              </button>
              <button
                type="button"
                disabled={disabled}
                onClick={() => {
                  setPrefs(DEFAULT_PREFS);
                  setLocationQuery('');
                  setCuisineQuery('');
                  setExtrasInput('');
                }}
                className="flex-1 bg-surface-container text-on-surface-variant font-label-bold text-label-bold h-12 rounded-lg border border-outline-variant hover:bg-surface-variant transition-all"
              >
                Reset
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  );
}

