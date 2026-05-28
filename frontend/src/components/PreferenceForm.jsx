import { useEffect, useState } from 'react';
import Typeahead from './Typeahead';
import BudgetSlider from './BudgetSlider';

const PreferenceForm = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState({
    location: '',
    budget_amount: 800,
    cuisine: '',
    min_rating: 4.0,
    extras: '',
    top_n: 5
  });

  const [locationOptions, setLocationOptions] = useState([]);
  const [locationsLoading, setLocationsLoading] = useState(true);
  const [cuisineOptions, setCuisineOptions] = useState([]);
  const [cuisinesLoading, setCuisinesLoading] = useState(true);
  const [locationQuery, setLocationQuery] = useState('');
  const [cuisineQuery, setCuisineQuery] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function loadLocations() {
      try {
        setLocationsLoading(true);
        const res = await fetch('/api/v1/locations');
        const data = await res.json();
        const options = Array.isArray(data?.locations) ? data.locations : [];

        if (!cancelled) {
          setLocationOptions(options);
        }
      } catch {
        if (!cancelled) setLocationOptions([]);
      } finally {
        if (!cancelled) setLocationsLoading(false);
      }
    }

    loadLocations();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadCuisines() {
      try {
        setCuisinesLoading(true);
        const res = await fetch('/api/v1/cuisines');
        const data = await res.json();
        const options = Array.isArray(data?.cuisines) ? data.cuisines : [];
        if (!cancelled) setCuisineOptions(options);
      } catch {
        if (!cancelled) setCuisineOptions([]);
      } finally {
        if (!cancelled) setCuisinesLoading(false);
      }
    }

    loadCuisines();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'min_rating' || name === 'top_n' ? parseFloat(value) : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // If user typed a value but didn't click a suggestion, submit what they typed.
    const finalLocation = locationQuery.trim() || formData.location;
    const finalCuisine = cuisineQuery.trim() || formData.cuisine;
    
    // Parse extras into an array
    const extrasArray = formData.extras 
      ? formData.extras.split(',').map(s => s.trim()).filter(s => s)
      : [];

    onSubmit({
      ...formData,
      location: finalLocation,
      cuisine: finalCuisine,
      extras: extrasArray
    });
  };

  return (
    <div className="glass" style={{ padding: '2rem' }}>
      <h2 style={{ marginBottom: '1.5rem', fontSize: '1.5rem', background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
        Your Preferences
      </h2>
      <form onSubmit={handleSubmit} className="grid" style={{ gap: '1rem' }}>
        
        <Typeahead
          id="location"
          label="Location"
          placeholder={locationsLoading ? 'Loading locations…' : 'Type 3+ letters (e.g. Indira, Bell)'}
          options={locationOptions}
          disabled={locationsLoading && locationOptions.length === 0}
          value={locationQuery}
          onChange={setLocationQuery}
          onSelect={(loc) => {
            setFormData(prev => ({ ...prev, location: loc }));
            setLocationQuery(loc);
          }}
          helperText={<>Type at least <strong>3 letters</strong> to see area suggestions.</>}
        />

        <Typeahead
          id="cuisine"
          label="Cuisine"
          placeholder={cuisinesLoading ? 'Loading cuisines…' : 'Type 3+ letters (e.g. Ital, North)'}
          options={cuisineOptions}
          disabled={cuisinesLoading && cuisineOptions.length === 0}
          value={cuisineQuery}
          onChange={setCuisineQuery}
          onSelect={(c) => {
            setFormData(prev => ({ ...prev, cuisine: c }));
            setCuisineQuery(c);
          }}
          helperText={<>Type at least <strong>3 letters</strong> to see cuisine suggestions.</>}
        />

        <div className="flex" style={{ gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 380px' }}>
            <BudgetSlider
              value={formData.budget_amount}
              onChange={(v) => setFormData(prev => ({ ...prev, budget_amount: v }))}
              disabled={isLoading}
            />
          </div>

          <div style={{ flex: '1 1 200px' }}>
            <label htmlFor="min_rating">Min Rating</label>
            <input
              type="number"
              id="min_rating"
              name="min_rating"
              min="0" max="5" step="0.1"
              value={formData.min_rating}
              onChange={handleChange}
            />
          </div>
        </div>

        <div>
          <label htmlFor="extras">Extras (comma-separated)</label>
          <input 
            type="text" 
            id="extras" 
            name="extras" 
            placeholder="e.g. outdoor seating, romantic" 
            value={formData.extras}
            onChange={handleChange}
          />
        </div>
        
        <div style={{ marginTop: '0.5rem' }}>
          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%' }}
            disabled={isLoading}
          >
            {isLoading ? 'Generating AI Picks...' : 'Find Recommendations'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PreferenceForm;
