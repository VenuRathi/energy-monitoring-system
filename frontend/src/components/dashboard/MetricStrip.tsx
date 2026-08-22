import { Activity, BatteryCharging, Gauge, Zap } from "lucide-react";
import type { MetricCard } from "../../types/energy";
import { formatNumber } from "../../lib/formatters";
import { energyDisplayDecimals, sortMetricsByEnergyPriority } from "../../lib/energyParameters";

type MetricStripProps = {
  metrics: MetricCard[];
  energyOnly?: boolean;
  excludeEnergy?: boolean;
};

export function MetricStrip({ metrics, energyOnly = false, excludeEnergy = false }: MetricStripProps) {
  const energyMetrics = sortMetricsByEnergyPriority(metrics);
  const visibleMetrics = energyOnly
    ? energyMetrics
    : excludeEnergy
      ? metrics.filter((metric) => !energyMetrics.some((energyMetric) => energyMetric.key === metric.key))
      : metrics;

  if (visibleMetrics.length === 0) {
    return <div className="page-state page-state--padded">No readings available yet for this meter.</div>;
  }

  return (
    <section className="metric-strip">
      {visibleMetrics.map((metric, index) => {
        const icons = [Zap, Gauge, Activity, BatteryCharging];
        const Icon = icons[index % icons.length];
        return (
          <article key={metric.key} className="metric-tile">
            <span className="metric-tile__icon" aria-hidden="true">
              <Icon size={18} strokeWidth={2.2} />
            </span>
            <p className="metric-tile__label">{metric.label}</p>
            <strong className="metric-tile__value">
              {typeof metric.value === "number" ? formatNumber(metric.value, energyDisplayDecimals(metric.key)) : metric.value}
            </strong>
            <span className="metric-tile__unit">{metric.unit}</span>
          </article>
        );
      })}
    </section>
  );
}
