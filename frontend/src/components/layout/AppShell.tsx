import { NavLink, Outlet } from "react-router-dom";
import { useEffect } from "react";
import { ensureTraceScript } from "../../lib/trace";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex flex-col items-center gap-0.5 text-xs font-medium ${
    isActive ? "text-primary" : "text-on-surface-variant hover:text-primary"
  }`;

export default function AppShell() {
  useEffect(() => {
    ensureTraceScript();
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-30 bg-surface-container-lowest/90 backdrop-blur border-b border-outline-variant/30">
        <div className="mx-auto max-w-[1280px] px-4 md:px-10 h-16 flex items-center justify-between">
          <NavLink to="/" className="flex items-center gap-2">
            <span className="w-9 h-9 rounded-xl ai-gradient flex items-center justify-center text-white">
              <span className="material-symbols-outlined text-[20px]">auto_awesome</span>
            </span>
            <div>
              <div className="font-bold text-lg text-primary leading-none">LocalAI</div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant">
                Discover Local
              </div>
            </div>
          </NavLink>
          <nav className="hidden md:flex items-center gap-6">
            <NavLink to="/" className={linkClass} end>
              Home
            </NavLink>
            <NavLink to="/search" className={linkClass}>
              Explore
            </NavLink>
            <NavLink to="/chat" className={linkClass}>
              Ask AI
            </NavLink>
          </nav>
          <div className="text-xs text-on-surface-variant font-mono hidden sm:block">
            Powered by Zeus · v{__APP_VERSION__}
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <nav className="md:hidden sticky bottom-0 z-30 bg-surface-container-lowest border-t border-outline-variant/30 px-6 py-2 flex justify-around">
        <NavLink to="/" className={linkClass} end>
          <span className="material-symbols-outlined">home</span>
          Home
        </NavLink>
        <NavLink to="/search" className={linkClass}>
          <span className="material-symbols-outlined">explore</span>
          Explore
        </NavLink>
        <NavLink to="/chat" className={linkClass}>
          <span className="material-symbols-outlined">auto_awesome</span>
          Ask AI
        </NavLink>
      </nav>
    </div>
  );
}
