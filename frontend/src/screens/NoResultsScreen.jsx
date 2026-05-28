import MaterialIcon from '../components/ui/MaterialIcon';

export default function NoResultsScreen({ onEditPreferences }) {
  return (
    <main className="max-w-container-max mx-auto px-[16px] md:px-[32px] py-xl min-h-[707px] flex flex-col items-center justify-center">
      <div className="w-full max-w-2xl text-center">
        <div className="relative mb-lg flex justify-center">
          <div className="w-48 h-48 md:w-64 md:h-64 bg-surface-container-low rounded-full flex items-center justify-center relative overflow-hidden ai-shimmer">
            <div className="absolute inset-0 border-2 border-outline-variant rounded-full border-dashed opacity-30" />
            <MaterialIcon name="search_off" className="text-primary text-[80px] opacity-20" />
          </div>
          <div className="absolute -bottom-2 right-1/4 md:right-1/3 bg-primary text-on-primary p-3 rounded-full shadow-lg">
            <MaterialIcon name="search_off" className="text-[32px]" />
          </div>
        </div>

        <h2 className="text-display-lg-mobile md:text-display-lg font-display-lg text-on-surface mb-sm">
          No matches found
        </h2>
        <p className="text-body-lg text-on-surface-variant max-w-md mx-auto mb-xl">
          We couldn't find any restaurants matching your current criteria. Your
          perfect meal might be just one adjustment away.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-md mb-xl text-left">
          {[
            { icon: 'payments', title: 'Budget', body: 'Try expanding your price range to include more local gems.' },
            { icon: 'star_half', title: 'Rating', body: 'Lowering the minimum rating reveals more options.' },
            { icon: 'filter_list_off', title: 'Cuisines', body: 'Remove specific cuisine tags to browse all available flavors.' },
          ].map((s) => (
            <button
              key={s.title}
              type="button"
              className="p-md bg-surface-container-lowest border border-outline-variant rounded-xl hover:bg-surface-container transition-all group text-left"
            >
              <div className="flex items-center gap-3 mb-sm">
                <MaterialIcon name={s.icon} className="text-primary" />
                <span className="text-label-bold font-label-bold text-on-surface">
                  {s.title}
                </span>
              </div>
              <p className="text-body-md text-on-surface-variant">{s.body}</p>
            </button>
          ))}
        </div>

        <div className="flex flex-col items-center gap-lg">
          <button
            type="button"
            onClick={onEditPreferences}
            className="bg-primary text-on-primary px-lg py-md rounded-lg font-label-bold text-label-bold uppercase tracking-widest hover:brightness-110 active:scale-95 transition-all shadow-md"
          >
            Edit Preferences
          </button>

          <div className="group relative flex items-center gap-2 cursor-help py-2 px-4 bg-surface-container-high rounded-full border border-primary/10">
            <MaterialIcon name="verified" className="text-primary text-[18px]" />
            <span className="text-label-sm font-label-sm text-on-surface-variant">
              Grounded in verified dataset
            </span>

            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 w-64 p-md bg-inverse-surface text-inverse-on-surface rounded-xl text-body-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-xl z-10 border border-outline/20">
              Our recommendations are strictly generated from the restaurants in
              the dataset after filtering for your preferences.
              <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-inverse-surface" />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

