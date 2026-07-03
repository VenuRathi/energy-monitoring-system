import { useMemo, useState } from "react";
import { ActiveAlertsPanel } from "../components/dashboard/ActiveAlertsPanel";
import { EnergyChart } from "../components/dashboard/EnergyChart";
import { LatestReadingsTable } from "../components/dashboard/LatestReadingsTable";
import { MeterCard } from "../components/dashboard/MeterCard";
import { MeterSelector } from "../components/dashboard/MeterSelector";
import { MetricStrip } from "../components/dashboard/MetricStrip";
import { ParameterExplorer } from "../components/dashboard/ParameterExplorer";
import { useDashboardData } from "../hooks/useDashboardData";

type DashboardPageProps = {
  selectedMeterId: string;
  onSelectMeter: (meterId: string) => void;
  onConfigureMeters: () => void;
};

export function DashboardPage({ selectedMeterId, onSelectMeter, onConfigureMeters }: DashboardPageProps) {
  const [trendParameterKey, setTrendParameterKey] = useState("active_power_total");
  const { data, isLoading, isError, error, refetch } = useDashboardData(selectedMeterId, trendParameterKey);

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
  const statusTone =
    selectedMeter?.data_quality === "live"
      ? "online"
      : selectedMeter?.data_quality ?? selectedMeter?.status ?? "offline";

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
          <button type="button" className="ghost-button" onClick={onConfigureMeters}>
            Open Meter Setup
          </button>
          <MeterSelector meters={data.meters} value={selectedMeterId} onChange={onSelectMeter} />
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
            <h4>{selectedMeter?.meter_name ?? "No meter selected"}</h4>
          </div>
          <div className="dashboard__meter-meta">
            <span>{selectedMeter?.location ?? "n/a"}</span>
            <span>{selectedMeter?.manufacturer ?? "n/a"}</span>
            <span>{selectedMeter?.model ?? "n/a"}</span>
          </div>
        </div>
        {selectedMeter?.status_detail ? (
          <div className={`dashboard__status-note dashboard__status-note--${statusTone}`}>
            {selectedMeter.status_detail}
          </div>
        ) : null}
        {noReadingsYet ? (
          <div className="dashboard__status-note dashboard__status-note--no_readings">
            No readings available yet for this meter.
          </div>
        ) : null}
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
