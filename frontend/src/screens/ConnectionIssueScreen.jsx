import MaterialIcon from '../components/ui/MaterialIcon';

export default function ConnectionIssueScreen({ errorInfo, onRetry, onRefine }) {
  const status = errorInfo?.status;
  const code =
    status === 504
      ? '504_GATEWAY_TIMEOUT_AI_CHEF'
      : status
        ? `${status}_AI_ERROR`
        : 'AI_ERROR';

  return (
    <main className="flex-grow flex items-center justify-center px-[16px] md:px-[32px] py-xl">
      <div className="max-w-xl w-full flex flex-col items-center text-center">
        <div className="relative mb-lg">
          <div className="w-32 h-32 md:w-40 md:h-40 rounded-full bg-surface-container-high flex items-center justify-center relative overflow-hidden">
            <div className="absolute inset-0 ai-shimmer" />
            <MaterialIcon
              name="cloud_off"
              className="text-[64px] md:text-[80px] text-primary opacity-20"
            />
          </div>
          <div className="absolute -bottom-2 -right-2 bg-error text-on-error px-3 py-1 rounded-full shadow-lg flex items-center gap-1.5 border-2 border-background">
            <MaterialIcon name="timer" className="text-[16px]" />
            <span className="font-label-bold text-label-bold uppercase tracking-wider">
              Timeout
            </span>
          </div>
        </div>

        <h2 className="text-display-lg-mobile md:text-display-lg font-display-lg text-on-background mb-md">
          Our Chef is Taking a Moment
        </h2>
        <p className="text-body-lg text-on-surface-variant max-w-md mx-auto mb-xl">
          {errorInfo?.message ||
            "The AI is currently processing a high volume of culinary data. It's taking a bit longer than expected to serve your recommendations."}
        </p>

        <div className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-md md:p-lg mb-xl text-left relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-primary opacity-40" />
          <div className="flex items-start gap-4">
            <div className="p-2 bg-surface-container-lowest rounded-lg border border-outline-variant">
              <MaterialIcon name="query_stats" className="text-primary" />
            </div>
            <div className="flex-grow">
              <h3 className="font-headline-sm text-headline-sm text-on-surface mb-xs">
                Technical Status
              </h3>
              <p className="text-body-md text-on-surface-variant mb-md">
                Your request may be delayed. You can retry now, or go back to
                refine your taste preferences.
              </p>
              <div className="h-1.5 w-full bg-surface-variant rounded-full overflow-hidden">
                <div className="h-full bg-primary w-[85%]" />
              </div>
              <div className="flex justify-between mt-2">
                <span className="text-label-sm font-label-sm text-on-surface-variant">
                  API Response Delay
                </span>
                <span className="text-label-sm font-label-sm font-bold text-primary">
                  85% Processed
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-col md:flex-row items-center gap-md w-full">
          <button
            type="button"
            onClick={onRetry}
            className="w-full md:flex-1 bg-primary text-on-primary font-bold py-4 rounded-xl shadow-md hover:brightness-110 active:scale-95 transition-all flex items-center justify-center gap-2"
          >
            <MaterialIcon name="refresh" />
            Retry Now
          </button>
          <button
            type="button"
            onClick={onRefine}
            className="w-full md:flex-1 bg-surface-container-highest text-on-surface font-bold py-4 rounded-xl border border-outline-variant hover:bg-surface-variant active:scale-95 transition-all flex items-center justify-center gap-2"
          >
            <MaterialIcon name="edit_note" />
            Refine Search
          </button>
        </div>

        <p className="mt-xl text-label-sm font-label-sm text-on-surface-variant flex items-center gap-1.5">
          <MaterialIcon name="info" className="text-[14px]" />
          Error Code: {code}
        </p>
      </div>
    </main>
  );
}

