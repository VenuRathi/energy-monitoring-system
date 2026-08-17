import { AlertTriangle } from "lucide-react";
import type { AlertEvent } from "../../types/energy";
import { formatNumber } from "../../lib/formatters";

type ActiveAlertsPanelProps = {
  alerts: AlertEvent[];
};

function formatThreshold(minValue: number | null, maxValue: number | null, unit: string) {
  const suffix = unit ? ` ${unit}` : "";
  if (minValue !== null && maxValue !== null) {
    return `${formatNumber(minValue, 2)} to ${formatNumber(maxValue, 2)}${suffix}`;
  }
  if (minValue !== null) {
    return `>= ${formatNumber(minValue, 2)}${suffix}`;
  }
  if (maxValue !== null) {
    return `<= ${formatNumber(maxValue, 2)}${suffix}`;
  }
  return "n/a";
}

export function ActiveAlertsPanel({ alerts }: ActiveAlertsPanelProps) {
  if (alerts.length === 0) {
    return <div className="page-state page-state--padded">No active alerts for the current dashboard selection.</div>;
  }

  return (
    <div className="alert-card-grid">
      {alerts.map((alert) => (
        <article key={alert.id} className="alert-card">
          <div className="alert-card__icon" aria-hidden="true">
            <AlertTriangle size={19} strokeWidth={2.3} />
          </div>
          <div className="alert-card__body">
            <div className="alert-card__header">
              <div>
                <p className="section-label">{alert.location || alert.meterId}</p>
                <h5>{alert.meterName}</h5>
              </div>
              <span className="status-pill status-pill--warning">{alert.eventType || "active"}</span>
            </div>
            <dl className="alert-card__details">
              <div>
                <dt>Parameter</dt>
                <dd>{alert.parameterLabel}</dd>
              </div>
              <div>
                <dt>Allowed range</dt>
                <dd>{formatThreshold(alert.minValue, alert.maxValue, alert.unit)}</dd>
              </div>
              <div>
                <dt>Current value</dt>
                <dd>{alert.value !== null ? `${formatNumber(alert.value, 2)} ${alert.unit}`.trim() : "n/a"}</dd>
              </div>
              <div>
                <dt>Raised</dt>
                <dd>{alert.date || "n/a"} {alert.time || ""}</dd>
              </div>
            </dl>
          </div>
        </article>
      ))}
    </div>
  );
}
