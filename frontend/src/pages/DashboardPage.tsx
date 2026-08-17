import { Clock3, Settings2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ActiveAlertsPanel } from "../components/dashboard/ActiveAlertsPanel";
import { AllMetersEnergyPanel } from "../components/dashboard/AllMetersEnergyPanel";
import { EnergyChart } from "../components/dashboard/EnergyChart";
import { EnergyHistoryPanel } from "../components/dashboard/EnergyHistoryPanel";
import { LatestReadingsTable } from "../components/dashboard/LatestReadingsTable";
import { MeterCard } from "../components/dashboard/MeterCard";
import { MeterSelector } from "../components/dashboard/MeterSelector";
import { MetricStrip } from "../components/dashboard/MetricStrip";
import { ParameterExplorer } from "../components/dashboard/ParameterExplorer";
import { useDashboardData } from "../hooks/useDashboardData";
import { useHourlyEnergyHistory } from "../hooks/useHourlyEnergyHistory";
import { useSystemStatusData } from "../hooks/useMetersData";
import { formatTimestamp } from "../lib/formatters";
import { ENERGY_PARAMETER_KEYS, sortParametersByEnergyPriority } from "../lib/energyParameters";
import type { MeterRecord, SystemStatusMeter } from "../types/energy";

const TREND_RANGES = [
  { label: "Live", hours: undefined },
  { label: "24h", hours: 24 },
  { label: "7d", hours: 168 },
  { label: "30d", hours: 720 },
  { label: "90d", hours: 2160 },
];

function connectionTone(meter: SystemStatusMeter) {
  if (!meter.enabled) return "offline";
  return meter.communicationStatus;
}

function connectionLabel(meter: SystemStatusMeter) {
  if (!meter.enabled) return "disabled";
  return meter.communicationStatus;
}

function diagnosticLabel(meter: SystemStatusMeter) {
  switch (meter.diagnosticCode) {
    case "com_port_missing":
      return "COM port missing";
    case "com_port_unavailable":
      return "COM port unavailable";
    case "meter_no_response":
      return "Meter no response";
    case "meter_no_primary_values":
      return "Primary values missing";
    case "duplicate_slave_id":
      return "Duplicate slave ID";
    case "serial_settings_conflict":
      return "Serial settings conflict";
    default:
      return "";
  }
}

type DashboardPageProps = {
  selectedMeterId: string;
  onSelectMeter: (meterId: string) => void;
  onConfigureMeters: () => void;
};

export function DashboardPage({ selectedMeterId, onSelectMeter, onConfigureMeters }: DashboardPageProps) {
  const [trendParameterKey, setTrendParameterKey] = useState<string>(ENERGY_PARAMETER_KEYS[0]);
  const [trendHours, setTrendHours] = useState<number | undefined>(undefined);
  const [readingTab, setReadingTab] = useState<"latest" | "history" | "parameters">("latest");
  const { data, isLoading, isError, error, refetch } = useDashboardData(selectedMeterId, trendParameterKey, trendHours);
  const hourlyEnergyHistory = useHourlyEnergyHistory(
    selectedMeterId === "ALL" ? "" : selectedMeterId,
    72,
    selectedMeterId !== "ALL",
  );
  const {
    data: systemStatus,
    isLoading: isSystemStatusLoading,
    isError: isSystemStatusError,
    error: systemStatusError,
    refetch: refetchSystemStatus,
  } = useSystemStatusData();

  useEffect(() => {
    setReadingTab("latest");
  }, [selectedMeterId]);

  const meterTone = (meter: MeterRecord | null | undefined) => {
    if (!meter?.enabled) return "offline";
    if (meter.status === "online" && meter.data_quality === "live") return "online";
    if (meter.status === "offline") return "offline";
    return "warning";
  };

  const selectedTrendLabel = useMemo(
    () => data?.trendParameter?.label ?? "Active Power Total",
    [data?.trendParameter?.label],
  );
  const trendParameters = useMemo(
    () => sortParametersByEnergyPriority(data?.parameterCatalog ?? []),
    [data?.parameterCatalog],
  );

  if (isLoading) {
    return <div className="page-state">Loading dashboard data...</div>;
  }

  if (isError || !data) {
    const message = error instanceof Error ? error.message : "Unable to load dashboard data.";
    return (
      <div className="page-state page-state--error">
        <h3>Dashboard unavailable</h3>
        <p>{message}</p>
        <button type="button" className="ghost-button" onClick={() => refetch()}>
          Retry
        </button>
      </div>
    );
  }

  const selectedMeter = data.selectedMeter ?? data.meters[0];
  const isAllMetersView = selectedMeterId === "ALL" || selectedMeter?.meter_id === "ALL";
  const noReadingsYet = !isAllMetersView && (!selectedMeter?.has_readings || (data.latestReadings?.length ?? 0) === 0);
  const statusTone = meterTone(selectedMeter);
  const latestUpdateText = formatTimestamp(selectedMeter?.last_update ?? "");
  const totalAlerts = data.activeAlerts.length;
  const selectedMeterAlerts = isAllMetersView
    ? totalAlerts
    : data.activeAlerts.filter((alert) => alert.meterId === selectedMeter?.meter_id).length;

  if (!selectedMeter) {
    return (
      <div className="page-state page-state--error">
        <h3>No meters available</h3>
        <p>Add or enable at least one meter to start using the dashboard.</p>
        <button type="button" className="primary-button" onClick={onConfigureMeters}>
          Open Meter Setup
        </button>
      </div>
    );
  }

  return (
    <section className="dashboard">
      <section className="dashboard__commandbar">
        <div className="dashboard__commandbar-copy">
          <p className="section-label">Live View</p>
          <h3 className="dashboard__headline">Energy command center</h3>
          <p className="dashboard__copy">Fresh readings, meter health, and active alerts at a glance.</p>
        </div>
        <div className="dashboard__commandbar-actions">
          <span className={`status-pill status-pill--${statusTone}`}>{statusTone}</span>
          <span className="dashboard__updated-at"><Clock3 size={14} aria-hidden="true" /> {latestUpdateText}</span>
          <MeterSelector meters={data.meters} value={selectedMeterId} onChange={onSelectMeter} />
          <button type="button" className="ghost-button" onClick={onConfigureMeters}>
            <Settings2 size={15} aria-hidden="true" />
            Meter setup
          </button>
        </div>
      </section>

      <section className="dashboard__kpis" aria-label="Live View summary">
        <div className="summary-card">
          <span className="summary-card__label">Total meters</span>
          <strong>{data.summary.totalMeters}</strong>
        </div>
        <div className="summary-card">
          <span className="summary-card__label">Online</span>
          <strong>{data.summary.onlineMeters}</strong>
        </div>
        <div className="summary-card">
          <span className="summary-card__label">Needs attention</span>
          <strong>{data.summary.warningMeters + data.summary.offlineMeters}</strong>
        </div>
        <div className="summary-card">
          <span className="summary-card__label">Active alerts</span>
          <strong>{totalAlerts}</strong>
        </div>
        <div className="summary-card">
          <span className="summary-card__label">Latest reading</span>
          <strong>{latestUpdateText}</strong>
        </div>
      </section>

      <section className="dashboard__main-grid">
        <div className="panel dashboard__trend-panel">
          <div className="section-heading">
            <div>
              <p className="section-label">Trend</p>
              <h4>{isAllMetersView ? "Energy by meter" : selectedTrendLabel}</h4>
            </div>
            {!isAllMetersView ? (
              <div className="trend-controls">
                <label className="trend-parameter-select">
                  <span className="sr-only">Trend parameter</span>
                  <select value={trendParameterKey} onChange={(event) => setTrendParameterKey(event.target.value)}>
                    {trendParameters.map((parameter) => (
                      <option key={parameter.key} value={parameter.key}>
                        {parameter.label} {parameter.unit ? `(${parameter.unit})` : ""}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="trend-range" role="tablist" aria-label="Trend range">
                  {TREND_RANGES.map((range) => (
                    <button
                      key={range.label}
                      type="button"
                      className={`trend-range__button ${trendHours === range.hours ? "trend-range__button--active" : ""}`}
                      onClick={() => setTrendHours(range.hours)}
                    >
                      {range.label}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
          {isAllMetersView ? (
            <AllMetersEnergyPanel meters={data.meterEnergySummaries ?? []} />
          ) : (
            <EnergyChart data={data.trendSeries ?? []} label={selectedTrendLabel} unit={data.trendParameter?.unit ?? ""} />
          )}
        </div>

        <aside className="dashboard__side-rail">
          <div className="panel dashboard__health-panel">
            <div className="section-heading">
              <div>
                <p className="section-label">Meter health</p>
                <h4>What needs attention</h4>
              </div>
              {systemStatus ? <span className="table-subtle">Live status</span> : null}
            </div>
            {systemStatus ? (
              <div className="health-list">
                {[
                  ["Online", systemStatus.summary.meters.filter((meter) => meter.communicationStatus === "online").length, "online"],
                  ["Warning", systemStatus.summary.meters.filter((meter) => meter.communicationStatus === "warning").length, "warning"],
                  ["Offline", systemStatus.summary.meters.filter((meter) => meter.communicationStatus === "offline").length, "offline"],
                  ["Stale", systemStatus.summary.staleMeterCount, "warning"],
                ].map(([label, value, tone]) => (
                  <div key={label} className="health-list__row">
                    <span><i className={`health-list__dot health-list__dot--${tone}`} />{label}</span>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
            ) : isSystemStatusLoading ? (
              <div className="page-state">Loading status...</div>
            ) : (
              <div className="page-state page-state--error">
                <p>{isSystemStatusError && systemStatusError instanceof Error ? systemStatusError.message : "Status unavailable."}</p>
                <button type="button" className="ghost-button" onClick={() => refetchSystemStatus()}>Retry</button>
              </div>
            )}
          </div>

          <div className="panel dashboard__alerts-panel">
            <div className="section-heading">
              <div>
                <p className="section-label">Alerts</p>
                <h4>Active now</h4>
              </div>
              <strong className="dashboard__alert-count">{totalAlerts}</strong>
            </div>
            <ActiveAlertsPanel alerts={data.activeAlerts ?? []} />
          </div>
        </aside>
      </section>

      <section className="dashboard__cards">
        {data.meters.map((meter) => (
          <MeterCard
            key={meter.meter_id}
            meter={meter}
            active={meter.meter_id === selectedMeter?.meter_id}
            onClick={onSelectMeter}
          />
        ))}
      </section>

      <section className="dashboard__section dashboard__connections">
        <div className="section-heading">
          <div>
            <p className="section-label">Diagnostics</p>
            <h4>Communication details</h4>
          </div>
          {systemStatus ? (
            <span className={`status-pill status-pill--${systemStatus.status === "ok" ? "online" : "warning"}`}>
              {systemStatus.summary.enabledMeterCount} enabled
            </span>
          ) : null}
        </div>

        {isSystemStatusLoading ? <div className="page-state">Loading live connection status...</div> : null}

        {isSystemStatusError ? (
          <div className="page-state page-state--error">
            <h3>Live connections unavailable</h3>
            <p>{systemStatusError instanceof Error ? systemStatusError.message : "Unable to load /api/status."}</p>
            <button type="button" className="ghost-button" onClick={() => refetchSystemStatus()}>
              Retry live connections
            </button>
          </div>
        ) : null}

        {systemStatus ? (
          <div className="status-stack">
            <div className="status-meter-grid">
              {systemStatus.summary.meters.map((meter) => (
                <article key={meter.meterId} className="status-meter-card">
                  <div className="status-meter-card__top">
                    <div>
                      <p className="section-label">{meter.comPort || "COM n/a"} / Slave {meter.slaveId ?? "n/a"}</p>
                      <h4>{meter.meterName}</h4>
                    </div>
                    <span className={`status-pill status-pill--${connectionTone(meter)}`}>{connectionLabel(meter)}</span>
                  </div>

                  <dl className="status-meter-card__list">
                    <div>
                      <dt>Last success</dt>
                      <dd>{formatTimestamp(meter.lastSuccessfulReadingTime)}</dd>
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
                      <dt>Live data</dt>
                      <dd>{meter.staleWarning ? "Stale" : "Fresh"}</dd>
                    </div>
                  </dl>

                  {meter.diagnosticMessage || meter.lastErrorMessage ? (
                    <p className="dashboard__status-note dashboard__status-note--offline">
                      {diagnosticLabel(meter) ? <strong>{diagnosticLabel(meter)}: </strong> : null}
                      {meter.diagnosticMessage || meter.lastErrorMessage}
                    </p>
                  ) : null}
                </article>
              ))}
            </div>
          </div>
        ) : null}
      </section>

      <section className="dashboard__section">
        <div className="section-heading">
          <div>
            <p className="section-label">Selected meter</p>
            <h4>{isAllMetersView ? "All meters energy summary" : selectedMeter.meter_name}</h4>
          </div>
          <div className="dashboard__meter-aside">
            <span className={`status-pill status-pill--${statusTone}`}>{statusTone}</span>
            <span className="dashboard__updated-at">Updated {latestUpdateText}</span>
          </div>
        </div>
        <div className="dashboard__meter-meta">
          {isAllMetersView ? (
            <>
              <span>{data.meterEnergySummaries?.length ?? data.meters.length} meter(s)</span>
              <span>Per-meter energy totals</span>
              <span>No aggregate values</span>
              <span>kWh / kVARh / kVAh</span>
            </>
          ) : (
            <>
              <span>{selectedMeter.location || "n/a"}</span>
              <span>{selectedMeter.manufacturer || "n/a"}</span>
              <span>{selectedMeter.model || "n/a"}</span>
              <span>{selectedMeter.com_port || "COM n/a"} - Slave {selectedMeter.slave_id}</span>
            </>
          )}
        </div>
        {selectedMeter.status_detail ? (
          <div className={`dashboard__status-note dashboard__status-note--${statusTone}`}>
            {selectedMeter.status_detail}
          </div>
        ) : null}
        {noReadingsYet ? (
          <div className="dashboard__status-note dashboard__status-note--no_readings">
            No readings available yet for this meter.
          </div>
        ) : null}
        {isAllMetersView ? (
          <AllMetersEnergyPanel meters={data.meterEnergySummaries ?? []} />
        ) : (
          <div className="selected-meter__grid">
            <div className="selected-meter__energy">
              <MetricStrip metrics={data.metrics} energyOnly />
            </div>
            <div className="selected-meter__operating">
              <MetricStrip metrics={data.metrics} excludeEnergy />
            </div>
            <div className="dashboard__overview dashboard__overview--secondary">
              <div className="summary-card">
                <span className="summary-card__label">Data quality</span>
                <strong>{selectedMeter.data_quality?.replaceAll("_", " ") ?? "n/a"}</strong>
                <span className="table-subtle">
                  {selectedMeter.live_measurements ? "Live values available" : "Waiting for live values"}
                </span>
              </div>
              <div className="summary-card">
                <span className="summary-card__label">Current alert load</span>
                <strong>{selectedMeterAlerts}</strong>
                <span className="table-subtle">{selectedMeterAlerts > 0 ? "Needs operator review" : "No active alerts"}</span>
              </div>
              <div className="summary-card">
                <span className="summary-card__label">Polling state</span>
                <strong>{selectedMeter.enabled ? "Included" : "Disabled"}</strong>
                <span className="table-subtle">{selectedMeter.one_based_map ? "One-based map" : "Zero-based map"}</span>
              </div>
              <div className="summary-card">
                <span className="summary-card__label">Role</span>
                <strong>{selectedMeter.seu ? "SEU meter" : "Standard meter"}</strong>
                <span className="table-subtle">{selectedMeter.driver}</span>
              </div>
            </div>
          </div>
        )}
      </section>

      {!isAllMetersView ? (
        <section className="dashboard__section dashboard__reading-tabs">
          <div className="reading-tabs" role="tablist" aria-label="Selected meter details">
            <button
              type="button"
              role="tab"
              aria-selected={readingTab === "latest"}
              className={`reading-tabs__button ${readingTab === "latest" ? "reading-tabs__button--active" : ""}`}
              onClick={() => setReadingTab("latest")}
            >
              Latest Main Readings
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={readingTab === "history"}
              className={`reading-tabs__button ${readingTab === "history" ? "reading-tabs__button--active" : ""}`}
              onClick={() => setReadingTab("history")}
            >
              72h Energy History
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={readingTab === "parameters"}
              className={`reading-tabs__button ${readingTab === "parameters" ? "reading-tabs__button--active" : ""}`}
              onClick={() => setReadingTab("parameters")}
            >
              All Parameters
            </button>
          </div>

          {readingTab === "latest" ? (
            <div className="reading-tabs__panel">
              <div className="section-heading">
                <div>
                  <p className="section-label">Latest Main Readings</p>
                  <h4>Current operating values</h4>
                </div>
              </div>
              <LatestReadingsTable rows={data.latestReadings ?? []} />
            </div>
          ) : null}

          {readingTab === "history" ? (
            <div className="reading-tabs__panel">
              <div className="section-heading">
                <div>
                  <p className="section-label">72h Energy History</p>
                  <h4>Hourly energy received</h4>
                </div>
                <span className="table-subtle">kWh / kVARh / kVAh</span>
              </div>
              <EnergyHistoryPanel
                data={hourlyEnergyHistory.data ?? []}
                isLoading={hourlyEnergyHistory.isLoading}
                isError={hourlyEnergyHistory.isError}
                errorMessage={hourlyEnergyHistory.error instanceof Error ? hourlyEnergyHistory.error.message : undefined}
                onRetry={() => hourlyEnergyHistory.refetch()}
              />
            </div>
          ) : null}

          {readingTab === "parameters" ? (
            <div className="reading-tabs__panel">
              <div className="section-heading">
                <div>
                  <p className="section-label">All Parameters</p>
                  <h4>Full parameter explorer</h4>
                </div>
              </div>
              <ParameterExplorer
                parameters={data.parameterCatalog ?? []}
                latestReadings={data.latestReadings ?? []}
                selectedKey={trendParameterKey}
                onSelect={(parameterKey) => setTrendParameterKey(parameterKey)}
              />
            </div>
          ) : null}
        </section>
      ) : null}

    </section>
  );
}
