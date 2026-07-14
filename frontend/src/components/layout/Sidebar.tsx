import { APP_META } from "../../app/appMeta";
import type { PageKey } from "../../types/energy";

const navItems: Array<{ key: PageKey; label: string }> = [
  { key: "dashboard", label: "Live View" },
  { key: "meters", label: "Meter Setup" },
  { key: "reports", label: "Reports & Email" },
  { key: "help", label: "Help & Guide" },
];

type SidebarProps = {
  activePage: PageKey;
  open: boolean;
  onNavigate: (page: PageKey) => void;
  onClose: () => void;
};

export function Sidebar({ activePage, open, onNavigate, onClose }: SidebarProps) {
  return (
    <>
      <button
        type="button"
        className={`sidebar-backdrop ${open ? "sidebar-backdrop--visible" : ""}`}
        onClick={onClose}
        aria-label="Close sidebar"
      />
      <aside className={`sidebar ${open ? "sidebar--open" : ""}`}>
        <div className="sidebar__brand">
          <div className="sidebar__badge">EM</div>
          <div>
            <p className="sidebar__eyebrow">{APP_META.systemName}</p>
            <h1 className="sidebar__title">{APP_META.productName}</h1>
            <p className="sidebar__meta">{APP_META.version}</p>
          </div>
        </div>

        <nav className="sidebar__nav" aria-label="Main navigation">
          {navItems.map((item) => (
            <button
              type="button"
              key={item.label}
              className={`sidebar__link ${activePage === item.key ? "sidebar__link--active" : ""}`}
              onClick={() => onNavigate(item.key)}
            >
              <span className="sidebar__link-dot" />
              {item.label}
            </button>
          ))}
        </nav>

        <section className="sidebar__status">
          <p className="sidebar__status-label">System Status</p>
          <div className="sidebar__status-pill sidebar__status-pill--ok">Operational</div>
          <p className="sidebar__status-note">
            Use Meter Setup to scan the line, Live View to check readings, and Help &amp; Guide for troubleshooting.
          </p>
        </section>
      </aside>
    </>
  );
}
