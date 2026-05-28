import MaterialIcon from '../ui/MaterialIcon';

export default function BottomNavBar() {
  return (
    <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-2 py-3 bg-surface-container border-t border-outline-variant shadow-sm">
      <button
        type="button"
        className="flex flex-col items-center justify-center bg-primary-container text-on-primary-container rounded-full px-4 py-1 active:scale-90 duration-200"
      >
        <MaterialIcon name="explore" />
        <span className="text-label-sm font-label-sm">Discover</span>
      </button>
      <button
        type="button"
        className="flex flex-col items-center justify-center text-on-surface-variant opacity-70 hover:bg-surface-variant transition-all"
      >
        <MaterialIcon name="bookmark" />
        <span className="text-label-sm font-label-sm">Saved</span>
      </button>
      <button
        type="button"
        className="flex flex-col items-center justify-center text-on-surface-variant opacity-70 hover:bg-surface-variant transition-all"
      >
        <MaterialIcon name="smart_toy" />
        <span className="text-label-sm font-label-sm">Assistant</span>
      </button>
      <button
        type="button"
        className="flex flex-col items-center justify-center text-on-surface-variant opacity-70 hover:bg-surface-variant transition-all"
      >
        <MaterialIcon name="person" />
        <span className="text-label-sm font-label-sm">Profile</span>
      </button>
    </nav>
  );
}

