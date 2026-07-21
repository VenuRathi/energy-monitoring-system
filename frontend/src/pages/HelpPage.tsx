import { APP_META } from "../app/appMeta";
import { useSystemStatusData } from "../hooks/useMetersData";
import { formatTimestamp } from "../lib/formatters";
import type { SystemStatusMeter } from "../types/energy";

function formatStatusDuration(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "n/a";
  }

  if (value < 60) {
    return `${Math.round(value)} sec`;
  }

  const minutes = Math.floor(value / 60);
  const seconds = Math.round(value % 60);
  if (minutes < 60) {
    return `${minutes} min ${seconds} sec`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours} hr ${remainingMinutes} min`;
}

function statusLabel(meter: SystemStatusMeter) {
  if (!meter.enabled) {
    return "disabled";
  }
  return meter.communicationStatus;
}

export function HelpPage() {
  const { data: systemStatus, isLoading, isError, error, refetch } = useSystemStatusData();

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

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="section-label">Runtime health</p>
            <h4>Live backend and polling status</h4>
          </div>
          {systemStatus ? (
            <span className={`status-pill status-pill--${systemStatus.status === "ok" ? "online" : "warning"}`}>
              {systemStatus.status === "ok" ? "ok" : "degraded"}
            </span>
          ) : null}
        </div>

        {isLoading ? <div className="page-state">Loading live system status...</div> : null}

        {isError ? (
          <div className="page-state page-state--error">
            <h3>Live status unavailable</h3>
            <p>{error instanceof Error ? error.message : "Unable to load /api/status."}</p>
            <button type="button" className="ghost-button" onClick={() => refetch()}>
              Retry status
            </button>
          </div>
        ) : null}

        {systemStatus ? (
          <div className="status-stack">
            <div className="dashboard__summary dashboard__summary--compact">
              <div className="summary-card">
                <span className="summary-card__label">API</span>
                <strong>{systemStatus.checks.api.status}</strong>
              </div>
              <div className="summary-card">
                <span className="summary-card__label">Database</span>
                <strong>{systemStatus.databaseStatus}</strong>
              </div>
              <div className="summary-card">
                <span className="summary-card__label">Polling</span>
                <strong>{systemStatus.polling.running ? "running" : "stopped"}</strong>
              </div>
              <div className="summary-card">
                <span className="summary-card__label">Enabled meters</span>
                <strong>{systemStatus.summary.enabledMeterCount}</strong>
              </div>
              <div className="summary-card">
                <span className="summary-card__label">Stale / warning</span>
                <strong>{systemStatus.summary.staleMeterCount}</strong>
              </div>
              <div className="summary-card">
                <span className="summary-card__label">Polling cycles</span>
                <strong>{systemStatus.polling.totalCyclesCompleted}</strong>
              </div>
            </div>

            <div className="help-grid">
              <article className="panel help-card">
                <div className="section-heading">
                  <div>
                    <p className="section-label">Polling heartbeat</p>
                    <h4>Cycle activity</h4>
                  </div>
                </div>
                <ul className="help-list help-list--compact">
                  <li>Cycle in progress: {systemStatus.polling.cycleInProgress ? "Yes" : "No"}</li>
                  <li>Started at: {formatTimestamp(systemStatus.polling.startedAt)}</li>
                  <li>Last cycle start: {formatTimestamp(systemStatus.polling.lastCycleStartTime)}</li>
                  <li>Last cycle end: {formatTimestamp(systemStatus.polling.lastCycleEndTime)}</li>
                  <li>Last cycle duration: {formatStatusDuration(systemStatus.polling.lastCycleDurationSeconds)}</li>
                  <li>Backend uptime: {formatStatusDuration(systemStatus.polling.uptimeSeconds)}</li>
                </ul>
                {systemStatus.polling.lastGlobalPollingError ? (
                  <div className="help-note help-note--danger">
                    <strong>Last polling error</strong>
                    <p>{systemStatus.polling.lastGlobalPollingError}</p>
                  </div>
                ) : null}
              </article>

              <article className="panel help-card">
                <div className="section-heading">
                  <div>
                    <p className="section-label">Health checks</p>
                    <h4>Backend dependencies</h4>
                  </div>
                </div>
                <ul className="help-list help-list--compact">
                  <li>API: {systemStatus.checks.api.message}</li>
                  <li>Database: {systemStatus.checks.database.message}</li>
                  <li>Meter inventory: {systemStatus.checks.meters.message}</li>
                  <li>Polling: {systemStatus.checks.polling.message}</li>
                  <li>Data source: {systemStatus.checks.dataSource.message}</li>
                </ul>
              </article>
            </div>

            <div className="section-heading">
              <div>
                <p className="section-label">Per-meter runtime state</p>
                <h4>Live communication summary</h4>
              </div>
            </div>

            <div className="status-meter-grid">
              {systemStatus.summary.meters.map((meter) => {
                const tone = !meter.enabled ? "offline" : meter.communicationStatus === "online" ? "online" : meter.communicationStatus === "warning" ? "warning" : "offline";
                return (
                  <article key={meter.meterId} className="status-meter-card">
                    <div className="status-meter-card__top">
                      <div>
                        <p className="section-label">Meter</p>
                        <h4>{meter.meterName}</h4>
                        <p className="meter-card__detail">
                          {meter.comPort || "COM n/a"} - Slave {meter.slaveId ?? "n/a"}
                        </p>
                      </div>
                      <span className={`status-pill status-pill--${tone}`}>{statusLabel(meter)}</span>
                    </div>

                    <dl className="status-meter-card__list">
                      <div>
                        <dt>Last success</dt>
                        <dd>{formatTimestamp(meter.lastSuccessfulReadingTime)}</dd>
                      </div>
                      <div>
                        <dt>Latest reading</dt>
                        <dd>{formatTimestamp(meter.latestReadingTimestamp ?? "")}</dd>
                      </div>
                      <div>
                        <dt>Last poll</dt>
                        <dd>{formatTimestamp(meter.lastPollAttemptTime)}</dd>
                      </div>
                      <div>
                        <dt>Failures</dt>
                        <dd>{meter.consecutiveFailureCount}</dd>
                      </div>
                      <div>
                        <dt>Stale</dt>
                        <dd>{meter.staleWarning ? "Yes" : "No"}</dd>
                      </div>
                      <div>
                        <dt>Enabled</dt>
                        <dd>{meter.enabled ? "Yes" : "No"}</dd>
                      </div>
                    </dl>

                    {meter.lastErrorMessage ? (
                      <div className="help-note help-note--warning">
                        <strong>Last error</strong>
                        <p>{meter.lastErrorMessage}</p>
                      </div>
                    ) : null}
                  </article>
                );
              })}
            </div>
          </div>
        ) : null}
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
