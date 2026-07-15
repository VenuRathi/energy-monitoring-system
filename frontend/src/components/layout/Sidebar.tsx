import { APP_META } from "../../app/appMeta";
import { useSystemStatusData } from "../../hooks/useMetersData";
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
  const { data: systemStatus, isError } = useSystemStatusData();
  const overallStatusTone = isError ? "offline" : systemStatus?.status === "degraded" ? "warning" : "online";
  const overallStatusLabel = isError ? "Backend Unreachable" : systemStatus?.status === "degraded" ? "Needs Attention" : "Operational";
  const statusNote = isError
    ? "Live system status could not be loaded. Check backend availability and API network settings."
    : systemStatus
      ? `${systemStatus.summary.enabledMeterCount} enabled meter(s), ${systemStatus.summary.staleMeterCount} stale/warning, polling ${
          systemStatus.polling.running ? "running" : "stopped"
        }.`
      : "Loading live system status...";

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
          <div className={`sidebar__status-pill status-pill--${overallStatusTone}`}>{overallStatusLabel}</div>
          <p className="sidebar__status-note">{statusNote}</p>
        </section>
      </aside>
    </>
  );
}
