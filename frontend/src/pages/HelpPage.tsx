import { APP_META } from "../app/appMeta";

export function HelpPage() {
  return (
    <section className="page-stack">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="section-label">System guide</p>
            <h3 className="page-title">How to use and support this system</h3>
            <p className="page-copy">
              This page is for operators and support engineers. Use it for quick checks during normal operation, first-line
              troubleshooting, and handover after deployment.
            </p>
          </div>
          <div className="app-meta-card">
            <span className="summary-card__label">Product</span>
            <strong>{APP_META.productName}</strong>
            <span className="app-meta-card__version">{APP_META.version}</span>
          </div>
        </div>
      </section>

      <section className="setup-guide setup-guide--highlight">
        <article className="setup-guide__card">
          <span className="setup-guide__step">Step 1</span>
          <h4>Check live status</h4>
          <p>Open Live View first. Confirm the selected meter is online and that new readings are visible.</p>
        </article>
        <article className="setup-guide__card">
          <span className="setup-guide__step">Step 2</span>
          <h4>Review meter setup</h4>
          <p>Use Meter Setup to confirm COM port, slave ID, enabled state, and serial settings for each live meter.</p>
        </article>
        <article className="setup-guide__card">
          <span className="setup-guide__step">Step 3</span>
          <h4>Check reports</h4>
          <p>Use Reports &amp; Email to export Excel or Word files, or review email and schedule configuration.</p>
        </article>
        <article className="setup-guide__card">
          <span className="setup-guide__step">Step 4</span>
          <h4>Use API status if needed</h4>
          <p>
            If something looks wrong, check <code>/api/status</code> to confirm database health, polling heartbeat, and
            per-meter communication state.
          </p>
        </article>
      </section>

      <section className="help-grid">
        <article className="panel help-card">
          <div className="section-heading">
            <div>
              <p className="section-label">Operators</p>
              <h4>Normal daily checks</h4>
            </div>
          </div>
          <ul className="help-list">
            <li>Dashboard loads without error.</li>
            <li>Expected meters appear in Live View.</li>
            <li>Online meters show fresh readings and current trend updates.</li>
            <li>Disabled meters are not treated as active plant meters.</li>
            <li>Recent export works for a valid time range.</li>
          </ul>
        </article>

        <article className="panel help-card">
          <div className="section-heading">
            <div>
              <p className="section-label">Meter status</p>
              <h4>What the states mean</h4>
            </div>
          </div>
          <ul className="help-list">
            <li><strong>Online:</strong> recent successful polling and fresh data.</li>
            <li><strong>Warning:</strong> communication trouble, stale data, or repeated failures are starting.</li>
            <li><strong>Offline:</strong> the meter is not currently communicating successfully.</li>
            <li><strong>Disabled:</strong> the meter stays in the database but is intentionally not polled.</li>
          </ul>
        </article>

        <article className="panel help-card">
          <div className="section-heading">
            <div>
              <p className="section-label">Quick troubleshooting</p>
              <h4>If the dashboard looks wrong</h4>
            </div>
          </div>
          <ul className="help-list">
            <li>If the whole dashboard fails, check backend availability and open <code>/api/health</code>.</li>
            <li>If one meter has no readings yet, confirm it is enabled and physically connected.</li>
            <li>If a live meter goes stale, review COM port, slave ID, and cable stability.</li>
            <li>If exports fail, verify the selected meter and date range actually contain data.</li>
          </ul>
        </article>

        <article className="panel help-card">
          <div className="section-heading">
            <div>
              <p className="section-label">Support handover</p>
              <h4>Where a developer should start</h4>
            </div>
          </div>
          <ul className="help-list">
            <li>Read the Developer Guide and Codebase Map in the project docs.</li>
            <li>Use the Debugging Guide before changing runtime or Modbus logic.</li>
            <li>Use the Maintenance Playbook for backup, restart, and replacement procedures.</li>
            <li>Use the Change Guide before editing polling, schema, or API contracts.</li>
          </ul>
        </article>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="section-label">Escalation path</p>
            <h4>When to involve engineering support</h4>
          </div>
        </div>
        <div className="help-grid help-grid--two">
          <div className="help-note help-note--warning">
            <strong>Needs quick review</strong>
            <p>
              One meter is warning or stale, exports fail for a normal range, or the dashboard only partially loads.
            </p>
          </div>
          <div className="help-note help-note--danger">
            <strong>Needs immediate support</strong>
            <p>
              Polling stops completely, database health becomes degraded, multiple meters go offline together, or no new
              readings are entering the system.
            </p>
          </div>
        </div>
      </section>
    </section>
  );
}
