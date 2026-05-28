import MaterialIcon from '../ui/MaterialIcon';

export default function TopAppBar() {
  return (
    <header className="bg-surface border-b border-outline-variant docked full-width top-0 sticky z-50">
      <div className="flex justify-between items-center w-full px-[16px] md:px-[32px] max-w-container-max mx-auto h-16">
        <div className="flex items-center gap-2">
          <MaterialIcon name="restaurant_menu" className="text-primary" />
          <h1 className="text-headline-md font-headline-md font-bold text-primary">
            GourmetAI
          </h1>
        </div>

        <div className="hidden md:flex gap-8 items-center h-full">
          <a
            className="text-primary font-bold text-label-sm font-label-sm h-full flex items-center px-2"
            href="#"
            onClick={(e) => e.preventDefault()}
          >
            Discover
          </a>
          <a
            className="text-secondary text-label-sm font-label-sm hover:bg-surface-container-high transition-colors px-2 rounded-lg"
            href="#"
            onClick={(e) => e.preventDefault()}
          >
            Saved
          </a>
          <a
            className="text-secondary text-label-sm font-label-sm hover:bg-surface-container-high transition-colors px-2 rounded-lg"
            href="#"
            onClick={(e) => e.preventDefault()}
          >
            Assistant
          </a>
          <a
            className="text-secondary text-label-sm font-label-sm hover:bg-surface-container-high transition-colors px-2 rounded-lg"
            href="#"
            onClick={(e) => e.preventDefault()}
          >
            Profile
          </a>
        </div>

        <button
          type="button"
          className="bg-primary-container text-on-primary-container px-4 py-2 rounded-lg font-label-bold text-label-bold flex items-center gap-2 hover:opacity-90 active:scale-95 duration-150"
        >
          <MaterialIcon name="smart_toy" className="text-[18px]" />
          AI Assistant
        </button>
      </div>
    </header>
  );
}

