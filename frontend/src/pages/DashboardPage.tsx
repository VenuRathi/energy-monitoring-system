import { Clock3, Settings2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { AttentionQueue } from "../components/dashboard/AttentionQueue";
import { AllMetersEnergyPanel } from "../components/dashboard/AllMetersEnergyPanel";
import { EnergyChart } from "../components/dashboard/EnergyChart";
import { EnergyHistoryPanel } from "../components/dashboard/EnergyHistoryPanel";
import { LatestReadingsTable } from "../components/dashboard/LatestReadingsTable";
import { MeterInventoryTable } from "../components/dashboard/MeterInventoryTable";
import { MeterCard } from "../components/dashboard/MeterCard";
import { MeterSelector } from "../components/dashboard/MeterSelector";
import { MetricStrip } from "../components/dashboard/MetricStrip";
import { ParameterExplorer } from "../components/dashboard/ParameterExplorer";
import { useDashboardData } from "../hooks/useDashboardData";
import { useHourlyEnergyHistory } from "../hooks/useHourlyEnergyHistory";
import { useSystemStatusData } from "../hooks/useMetersData";
import { formatTimestamp } from "../lib/formatters";
import { ENERGY_PARAMETER_KEYS, sortParametersByEnergyPriority } from "../lib/energyParameters";
import type { MeterRecord } from "../types/energy";

const TREND_RANGES = [
  { label: "Live", hours: undefined },
  { label: "24h", hours: 24 },
  { label: "7d", hours: 168 },
  { label: "30d", hours: 720 },
  { label: "90d", hours: 2160 },
];

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
  const runtimeSelectedMeter = systemStatus?.summary.meters.find((meter) => meter.meterId === selectedMeter?.meter_id);
  const statusTone = runtimeSelectedMeter
    ? !runtimeSelectedMeter.enabled || runtimeSelectedMeter.communicationStatus === "offline"
      ? "offline"
      : runtimeSelectedMeter.communicationStatus === "warning" || runtimeSelectedMeter.staleWarning
        ? "warning"
        : "online"
    : meterTone(selectedMeter);
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
          <h3 className="dashboard__headline">Operations overview</h3>
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
        <div className="summary-card"><span className="summary-card__label">Meters</span><strong>{data.summary.totalMeters}</strong></div>
        <div className="summary-card"><span className="summary-card__label">Healthy</span><strong>{data.summary.onlineMeters}</strong></div>
        <div className="summary-card"><span className="summary-card__label">Needs attention</span><strong>{data.summary.warningMeters + data.summary.offlineMeters}</strong></div>
        <div className="summary-card"><span className="summary-card__label">Threshold alarms</span><strong>{totalAlerts}</strong></div>
      </section>

      <section className="dashboard__primary-grid">
        <div className="panel dashboard__trend-panel">
          <div className="section-heading">
            <div><p className="section-label">Trend</p><h4>{isAllMetersView ? "Energy by meter" : selectedTrendLabel}</h4></div>
            {!isAllMetersView ? (
              <div className="trend-controls">
                <label className="trend-parameter-select"><span className="sr-only">Trend parameter</span><select value={trendParameterKey} onChange={(event) => setTrendParameterKey(event.target.value)}>{trendParameters.map((parameter) => <option key={parameter.key} value={parameter.key}>{parameter.label} {parameter.unit ? `(${parameter.unit})` : ""}</option>)}</select></label>
                <div className="trend-range" role="tablist" aria-label="Trend range">{TREND_RANGES.map((range) => <button key={range.label} type="button" className={`trend-range__button ${trendHours === range.hours ? "trend-range__button--active" : ""}`} onClick={() => setTrendHours(range.hours)}>{range.label}</button>)}</div>
              </div>
            ) : null}
          </div>
          {isAllMetersView ? (
            <AllMetersEnergyPanel meters={data.meterEnergySummaries ?? []} />
          ) : (
            <EnergyChart data={data.trendSeries ?? []} label={selectedTrendLabel} unit={data.trendParameter?.unit ?? ""} />
          )}
        </div>
        <aside className="dashboard__primary-rail">
          <section className="panel dashboard__selected-panel">
            <div className="section-heading">
              <div><p className="section-label">Selected meter</p><h4>{isAllMetersView ? "All meters energy summary" : selectedMeter.meter_name}</h4></div>
              <div className="dashboard__meter-aside"><span className={`status-pill status-pill--${statusTone}`}>{statusTone}</span><span className="dashboard__updated-at">{latestUpdateText}</span></div>
            </div>
            <div className="dashboard__meter-meta">
              {isAllMetersView ? <><span>{data.meterEnergySummaries?.length ?? data.meters.length} meters</span><span>Energy totals</span><span>kWh / kVARh / kVAh</span></> : <><span>{selectedMeter.location || "n/a"}</span><span>{selectedMeter.manufacturer || "n/a"} {selectedMeter.model || ""}</span><span>{selectedMeter.com_port || "COM n/a"} / Slave {selectedMeter.slave_id}</span></>}
            </div>
            {selectedMeter.status_detail && !isAllMetersView ? <div className={`dashboard__status-note dashboard__status-note--${statusTone}`}>{selectedMeter.status_detail}</div> : null}
            {noReadingsYet ? <div className="dashboard__status-note dashboard__status-note--no_readings">No readings available yet for this meter.</div> : null}
            {isAllMetersView ? (
              <div className="plant-faceplate">
                <div>
                  <span>Meters watched</span>
                  <strong>{data.summary.totalMeters}</strong>
                </div>
                <div>
                  <span>Healthy</span>
                  <strong>{data.summary.onlineMeters}</strong>
                </div>
                <div>
                  <span>Attention</span>
                  <strong>{data.summary.warningMeters + data.summary.offlineMeters}</strong>
                </div>
                <div>
                  <span>Threshold alarms</span>
                  <strong>{totalAlerts}</strong>
                </div>
              </div>
            ) : <>
              <div className="selected-meter__energy"><MetricStrip metrics={data.metrics} energyOnly /></div>
              <div className="selected-meter__context"><span>Data quality <strong>{selectedMeter.data_quality?.replaceAll("_", " ") ?? "n/a"}</strong></span><span>Alerts <strong>{selectedMeterAlerts}</strong></span><span>Polling <strong>{selectedMeter.enabled ? "Included" : "Disabled"}</strong></span><span>Role <strong>{selectedMeter.seu ? "SEU" : "Standard"}</strong></span></div>
            </>}
          </section>
          <section className="panel dashboard__attention-panel">
            <div className="section-heading"><div><p className="section-label">Attention queue</p><h4>What needs action</h4></div><strong className="dashboard__alert-count">{totalAlerts}</strong></div>
            <AttentionQueue alerts={data.activeAlerts} meters={data.meters} systemMeters={systemStatus?.summary.meters ?? []} backendError={isSystemStatusError ? (systemStatusError instanceof Error ? systemStatusError.message : "Runtime status unavailable.") : undefined} />
            {isSystemStatusError ? <button type="button" className="ghost-button ghost-button--compact" onClick={() => refetchSystemStatus()}>Retry runtime status</button> : null}
            {isSystemStatusLoading ? <p className="table-subtle">Loading runtime status...</p> : null}
          </section>
        </aside>

        <section className="panel dashboard__meter-overview">
          <div className="section-heading"><div><p className="section-label">Meter overview</p><h4>Energy status by meter</h4></div><span className="table-subtle">Select a card to inspect</span></div>
          <div className="dashboard__cards">
            {data.meters.map((meter) => <MeterCard key={meter.meter_id} meter={meter} active={meter.meter_id === selectedMeter?.meter_id} alertCount={data.activeAlerts.filter((alert) => alert.meterId === meter.meter_id).length} onClick={onSelectMeter} />)}
          </div>
          <details className="engineering-inventory"><summary>Engineering inventory view</summary><MeterInventoryTable meters={data.meters} alerts={data.activeAlerts} systemMeters={systemStatus?.summary.meters} selectedMeterId={selectedMeterId} onSelect={onSelectMeter} /></details>
        </section>
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
