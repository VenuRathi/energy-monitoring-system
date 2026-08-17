import { Menu, ServerCog, ShieldCheck } from "lucide-react";
import { useSystemStatusData } from "../../hooks/useMetersData";

type HeaderProps = {
  pageTitle: string;
  systemName: string;
  version: string;
  deploymentMode: string;
  onMenuClick: () => void;
};

export function Header({ pageTitle, systemName, version, deploymentMode, onMenuClick }: HeaderProps) {
  const { data: systemStatus, isError } = useSystemStatusData();
  const statusTone = isError ? "offline" : systemStatus?.status === "degraded" ? "warning" : "online";
  const statusLabel = isError ? "Backend offline" : systemStatus?.status === "degraded" ? "Needs attention" : "Operational";

  return (
    <header className="header">
      <button type="button" className="header__menu-button" onClick={onMenuClick} aria-label="Toggle navigation">
        <Menu size={18} aria-hidden="true" />
      </button>

      <div>
        <p className="header__eyebrow">{systemName}</p>
        <h2 className="header__title">{pageTitle}</h2>
      </div>

      <div className="header__meta">
        <div className={`header__pill header__pill--system status-pill--${statusTone}`}>
          <ServerCog size={15} aria-hidden="true" />
          {statusLabel}
        </div>
        <div className="header__pill header__pill--accent">{version}</div>
        <div className="header__pill">
          <ShieldCheck size={15} aria-hidden="true" />
          {deploymentMode}
        </div>
      </div>
    </header>
  );
}
