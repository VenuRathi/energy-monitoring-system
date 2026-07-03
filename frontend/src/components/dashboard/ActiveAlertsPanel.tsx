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
    <div className="table-shell">
      <table className="latest-table latest-table--compact">
        <thead>
          <tr>
            <th>Meter</th>
            <th>Parameter</th>
            <th>Range</th>
            <th>Value</th>
            <th>Date</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => (
            <tr key={alert.id}>
              <td className="latest-table__parameter">
                <strong>{alert.meterName}</strong>
                <div className="table-subtle">{alert.location || alert.meterId}</div>
              </td>
              <td>
                <strong>{alert.parameterLabel}</strong>
                <div className="table-subtle">{alert.parameterKey}</div>
              </td>
              <td>{formatThreshold(alert.minValue, alert.maxValue, alert.unit)}</td>
              <td className="latest-table__value">
                {alert.value !== null ? `${formatNumber(alert.value, 2)} ${alert.unit}`.trim() : "n/a"}
              </td>
              <td>{alert.date || "n/a"}</td>
              <td>{alert.time || "n/a"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
