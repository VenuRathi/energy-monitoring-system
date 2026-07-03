type HeaderProps = {
  pageTitle: string;
  onMenuClick: () => void;
};

export function Header({ pageTitle, onMenuClick }: HeaderProps) {
  return (
    <header className="header">
      <button type="button" className="header__menu-button" onClick={onMenuClick} aria-label="Toggle navigation">
        Menu
      </button>

      <div>
        <p className="header__eyebrow">Energy Monitoring System</p>
        <h2 className="header__title">{pageTitle}</h2>
      </div>

      <div className="header__meta">
        <div className="header__pill">Light Industrial Theme</div>
      </div>
    </header>
  );
}
