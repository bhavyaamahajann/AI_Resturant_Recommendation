import RecommendationCard from './RecommendationCard';

const RecommendationList = ({ result }) => {
  if (!result || !result.recommendations) {
    return null;
  }

  const { summary, recommendations, metadata } = result;

  return (
    <div className="animate-fade-in">
      {summary && (
        <div className="glass" style={{ padding: '1rem', marginBottom: '1.5rem', background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.3)' }}>
          <p style={{ margin: 0, fontWeight: 500, color: 'var(--success)' }}>✨ AI Summary: {summary}</p>
        </div>
      )}

      {metadata?.warnings?.length > 0 && (
        <div className="glass" style={{ padding: '1rem', marginBottom: '1.5rem', background: 'rgba(245, 158, 11, 0.1)', borderColor: 'rgba(245, 158, 11, 0.3)' }}>
          <p style={{ margin: '0 0 0.5rem 0', fontWeight: 600, color: 'var(--warning)' }}>⚠️ Notice</p>
          <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.875rem', color: 'var(--warning)' }}>
            {metadata.warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

      <div className="grid">
        {recommendations.map(rec => (
          <RecommendationCard key={rec.restaurant_id} recommendation={rec} />
        ))}
      </div>
    </div>
  );
};

export default RecommendationList;
