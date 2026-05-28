const BudgetSlider = ({
  value,
  onChange,
  min = 100,
  max = 10000,
  step = 50,
  disabled = false,
}) => {
  const v = Number.isFinite(value) ? value : min;
  return (
    <div>
      <label htmlFor="budget_amount">Budget (approx for two)</label>
      <div className="glass" style={{ padding: '1rem', marginTop: '0.25rem' }}>
        <div className="flex" style={{ justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
          <div style={{ fontWeight: 600 }}>₹{Math.round(v).toLocaleString('en-IN')}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            ₹{min.toLocaleString('en-IN')} – ₹{max.toLocaleString('en-IN')}
          </div>
        </div>
        <input
          id="budget_amount"
          name="budget_amount"
          type="range"
          min={min}
          max={max}
          step={step}
          value={v}
          disabled={disabled}
          onChange={(e) => onChange?.(parseFloat(e.target.value))}
          style={{ width: '100%' }}
        />
      </div>
    </div>
  );
};

export default BudgetSlider;

