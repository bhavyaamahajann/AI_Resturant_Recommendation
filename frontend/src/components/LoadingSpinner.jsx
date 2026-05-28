const LoadingSpinner = () => {
  return (
    <div className="flex" style={{ flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '4rem 2rem', gap: '1.5rem' }}>
      <div style={{
        width: '50px',
        height: '50px',
        border: '4px solid var(--border-light)',
        borderTopColor: 'var(--accent-primary)',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }} />
      <style>
        {`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}
      </style>
      <p style={{ color: 'var(--text-secondary)', fontWeight: 500, animation: 'pulse 2s infinite' }}>
        Analyzing preferences and contacting the LLM...
      </p>
      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `}
      </style>
    </div>
  );
};

export default LoadingSpinner;
