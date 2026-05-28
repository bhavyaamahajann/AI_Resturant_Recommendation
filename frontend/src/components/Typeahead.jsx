import { useMemo, useState } from 'react';

/**
 * Lightweight searchable dropdown (typeahead).
 * - Shows options only when query length >= minChars
 * - Calls onSelect(value) when user chooses
 */
const Typeahead = ({
  id,
  label,
  placeholder,
  options,
  minChars = 3,
  maxResults = 50,
  disabled = false,
  value,
  onChange,
  onSelect,
  helperText,
}) => {
  const [open, setOpen] = useState(false);

  const query = (value || '').trim().toLowerCase();
  const matches = useMemo(() => {
    if (query.length < minChars) return [];
    return (options || [])
      .filter((o) => String(o).toLowerCase().includes(query))
      .slice(0, maxResults);
  }, [options, query, minChars, maxResults]);

  return (
    <div className="w-full">
      {label && <label htmlFor={id}>{label}</label>}
      <div className="relative">
        <input
          id={id}
          name={id}
          type="text"
          placeholder={placeholder}
          value={value}
          disabled={disabled}
          autoComplete="off"
          className="w-full bg-surface-container-low border border-outline-variant rounded px-md py-sm text-body-md focus:ring-2 focus:ring-primary/20 outline-none disabled:opacity-60"
          onChange={(e) => {
            onChange?.(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 120)}
        />

        {open && query.length >= minChars && (
          <div
            className="absolute top-[calc(100%+0.4rem)] left-0 right-0 p-2 z-20 max-h-[260px] overflow-y-auto bg-surface-container-lowest border border-outline-variant rounded-lg shadow-sm"
          >
            {matches.length > 0 ? (
              <div className="flex flex-col gap-1">
                {matches.map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => {
                      onSelect?.(opt);
                      setOpen(false);
                    }}
                    className="text-left px-3 py-2 rounded hover:bg-surface-variant transition-colors text-on-surface"
                  >
                    {opt}
                  </button>
                ))}
              </div>
            ) : (
              <div className="px-3 py-2 text-body-md text-on-surface-variant">
                No matches. Try a different spelling.
              </div>
            )}
          </div>
        )}

        {helperText && (
          <div className="mt-1 text-label-sm text-on-surface-variant">
            {helperText}
          </div>
        )}
      </div>
    </div>
  );
};

export default Typeahead;

