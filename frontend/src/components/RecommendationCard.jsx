const RecommendationCard = ({ recommendation }) => {
  const { name, cuisine, rating, estimated_cost, explanation, rank } = recommendation;

  return (
    <div className="glass animate-fade-in" style={{ padding: '1.5rem', position: 'relative', overflow: 'hidden' }}>
      <div 
        style={{
          position: 'absolute',
          top: '-10px',
          right: '-10px',
          background: 'var(--accent-gradient)',
          color: 'white',
          width: '50px',
          height: '50px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '50%',
          fontWeight: 'bold',
          fontSize: '1.2rem',
          boxShadow: 'var(--shadow-md)',
          zIndex: 1
        }}
      >
        #{rank}
      </div>
      
      <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', paddingRight: '2rem' }}>{name}</h3>
      
      <div className="flex" style={{ gap: '1rem', marginBottom: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          🍽️ {cuisine}
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          ⭐ {rating?.toFixed(1) || 'N/A'}
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          💰 ₹{estimated_cost?.toFixed(0) || 'N/A'}
        </span>
      </div>
      
      <div style={{ 
        background: 'rgba(0,0,0,0.15)', 
        padding: '1rem', 
        borderRadius: 'var(--radius-md)',
        fontSize: '0.9rem',
        borderLeft: '3px solid var(--accent-primary)'
      }}>
        <p style={{ margin: 0, fontStyle: 'italic' }}>
          " {explanation} "
        </p>
      </div>
    </div>
  );
};

export default RecommendationCard;
