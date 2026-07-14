type HeaderProps = {
  pageTitle: string;
  systemName: string;
  version: string;
  deploymentMode: string;
  onMenuClick: () => void;
};

export function Header({ pageTitle, systemName, version, deploymentMode, onMenuClick }: HeaderProps) {
  return (
    <header className="header">
      <button type="button" className="header__menu-button" onClick={onMenuClick} aria-label="Toggle navigation">
        Menu
      </button>

      <div>
        <p className="header__eyebrow">{systemName}</p>
        <h2 className="header__title">{pageTitle}</h2>
      </div>

      <div className="header__meta">
        <div className="header__pill header__pill--accent">{version}</div>
        <div className="header__pill">{deploymentMode}</div>
      </div>
    </header>
  );
}
