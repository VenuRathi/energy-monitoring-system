import { useMemo, useState } from "react";
import { ActiveAlertsPanel } from "../components/dashboard/ActiveAlertsPanel";
import { EnergyChart } from "../components/dashboard/EnergyChart";
import { LatestReadingsTable } from "../components/dashboard/LatestReadingsTable";
import { MeterCard } from "../components/dashboard/MeterCard";
import { MeterSelector } from "../components/dashboard/MeterSelector";
import { MetricStrip } from "../components/dashboard/MetricStrip";
import { ParameterExplorer } from "../components/dashboard/ParameterExplorer";
import { useDashboardData } from "../hooks/useDashboardData";
import { formatTimestamp } from "../lib/formatters";
import type { MeterRecord } from "../types/energy";

type DashboardPageProps = {
  selectedMeterId: string;
  onSelectMeter: (meterId: string) => void;
  onConfigureMeters: () => void;
};

export function DashboardPage({ selectedMeterId, onSelectMeter, onConfigureMeters }: DashboardPageProps) {
  const [trendParameterKey, setTrendParameterKey] = useState("active_power_total");
  const { data, isLoading, isError, error, refetch } = useDashboardData(selectedMeterId, trendParameterKey);

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
  const noReadingsYet = !selectedMeter?.has_readings || (data.latestReadings?.length ?? 0) === 0;
  const statusTone = meterTone(selectedMeter);
  const latestUpdateText = formatTimestamp(selectedMeter?.last_update ?? "");
  const selectedMeterAlerts = data.activeAlerts.filter((alert) => alert.meterId === selectedMeter?.meter_id).length;
  const totalAlerts = data.activeAlerts.length;

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
      <section className="dashboard__hero dashboard__hero--compact">
        <div className="dashboard__hero-copy">
          <p className="section-label">Live plant view</p>
          <h3 className="dashboard__headline">Check line status and latest readings</h3>
          <p className="dashboard__copy">
            Use this page to see which meters are talking, whether they are live, and what the latest values look like.
          </p>
        </div>

        <div className="dashboard__hero-actions">
          <div className="dashboard__summary dashboard__summary--compact dashboard__summary--dashboard">
            <div className="summary-card">
              <span className="summary-card__label">Total meters</span>
              <strong>{data.summary.totalMeters}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-card__label">Online</span>
              <strong>{data.summary.onlineMeters}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-card__label">Warning</span>
              <strong>{data.summary.warningMeters}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-card__label">Offline</span>
              <strong>{data.summary.offlineMeters}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-card__label">Active alerts</span>
              <strong>{totalAlerts}</strong>
            </div>
          </div>

          <div className="dashboard__control-card">
            <div className="dashboard__control-copy">
              <p className="section-label">Selected meter</p>
              <h4>{selectedMeter.meter_name}</h4>
              <p className="dashboard__control-note">Last update: {latestUpdateText}</p>
            </div>
            <div className="dashboard__control-row">
              <span className={`status-pill status-pill--${statusTone}`}>{statusTone}</span>
              <button type="button" className="ghost-button" onClick={onConfigureMeters}>
                Open Meter Setup
              </button>
            </div>
            <p className="page-copy">
              {selectedMeter.location} · {selectedMeter.manufacturer} {selectedMeter.model} ·{" "}
              {selectedMeter.enabled ? "Polling enabled" : "Disabled"}
            </p>
            <MeterSelector meters={data.meters} value={selectedMeterId} onChange={onSelectMeter} />
          </div>
        </div>
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

      <section className="dashboard__section">
        <div className="section-heading">
          <div>
            <p className="section-label">Selected meter</p>
            <h4>{selectedMeter.meter_name}</h4>
          </div>
          <div className="dashboard__meter-aside">
            <span className={`status-pill status-pill--${statusTone}`}>{statusTone}</span>
            <span className="dashboard__updated-at">Updated {latestUpdateText}</span>
          </div>
        </div>
        <div className="dashboard__meter-meta">
          <span>{selectedMeter.location || "n/a"}</span>
          <span>{selectedMeter.manufacturer || "n/a"}</span>
          <span>{selectedMeter.model || "n/a"}</span>
          <span>{selectedMeter.com_port || "COM n/a"} · Slave {selectedMeter.slave_id}</span>
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
        <div className="dashboard__overview">
          <div className="summary-card">
            <span className="summary-card__label">Data quality</span>
            <strong>{selectedMeter.data_quality?.replaceAll("_", " ") ?? "n/a"}</strong>
            <span className="table-subtle">{selectedMeter.live_measurements ? "Live values available" : "Waiting for live values"}</span>
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
        <MetricStrip metrics={data.metrics} />
      </section>

      <section className="dashboard__split">
        <div className="panel">
          <div className="section-heading">
            <div>
              <p className="section-label">Trend</p>
              <h4>{selectedTrendLabel}</h4>
            </div>
          </div>
          <EnergyChart data={data.trendSeries ?? []} label={selectedTrendLabel} unit={data.trendParameter?.unit ?? ""} />
        </div>

        <div className="panel">
          <div className="section-heading">
            <div>
              <p className="section-label">Latest readings</p>
              <h4>Main values</h4>
            </div>
          </div>
          <LatestReadingsTable rows={data.latestReadings ?? []} />
        </div>
      </section>

      <section className="dashboard__section">
        <div className="section-heading">
          <div>
            <p className="section-label">Parameter explorer</p>
            <h4>All available meter parameters</h4>
          </div>
        </div>
        <ParameterExplorer
          parameters={data.parameterCatalog ?? []}
          latestReadings={data.latestReadings ?? []}
          selectedKey={trendParameterKey}
          onSelect={(parameterKey) => setTrendParameterKey(parameterKey)}
        />
      </section>

      <section className="dashboard__section">
        <div className="section-heading">
          <div>
            <p className="section-label">Alerts</p>
            <h4>Current alerts</h4>
          </div>
        </div>
        <ActiveAlertsPanel alerts={data.activeAlerts ?? []} />
      </section>
    </section>
  );
}
