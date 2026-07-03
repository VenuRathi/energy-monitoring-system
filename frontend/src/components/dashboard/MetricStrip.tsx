import type { MetricCard } from "../../types/energy";
import { formatNumber } from "../../lib/formatters";

type MetricStripProps = {
  metrics: MetricCard[];
};

export function MetricStrip({ metrics }: MetricStripProps) {
  if (metrics.length === 0) {
    return <div className="page-state page-state--padded">No meter readings available yet for this meter.</div>;
  }

  return (
    <section className="metric-strip">
      {metrics.map((metric) => (
        <article key={metric.key} className="metric-tile">
          <p className="metric-tile__label">{metric.label}</p>
          <strong className="metric-tile__value">
            {typeof metric.value === "number" ? formatNumber(metric.value, 2) : metric.value}
          </strong>
          <span className="metric-tile__unit">{metric.unit}</span>
        </article>
      ))}
    </section>
  );
}
