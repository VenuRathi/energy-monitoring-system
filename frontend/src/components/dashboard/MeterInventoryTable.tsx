import type { AlertEvent, MeterRecord, SystemStatusMeter } from "../../types/energy";
import { formatNumber, formatTimestamp } from "../../lib/formatters";

type MeterInventoryTableProps = {
  meters: MeterRecord[];
  alerts: AlertEvent[];
  systemMeters?: SystemStatusMeter[];
  selectedMeterId: string;
  onSelect: (meterId: string) => void;
};

function statusTone(meter: MeterRecord, runtime?: SystemStatusMeter) {
  if (runtime && !runtime.enabled) return "offline";
  if (runtime?.communicationStatus === "offline") return "offline";
  if (runtime?.communicationStatus === "warning" || runtime?.staleWarning) return "warning";
  if (runtime?.communicationStatus === "online") return "online";
  if (!meter.enabled) return "offline";
  if (meter.status === "online" && meter.data_quality === "live") return "online";
  if (meter.status === "offline") return "offline";
  return "warning";
}

function freshnessLabel(meter: MeterRecord, runtime?: SystemStatusMeter) {
  if (runtime && !runtime.enabled) return "Disabled";
  if (runtime?.staleWarning) return "Stale";
  if (runtime?.communicationStatus === "offline") return "No response";
  if (!meter.enabled || meter.data_quality === "disabled") return "Disabled";
  if (meter.data_quality === "live") return "Fresh";
  if (meter.data_quality === "stale") return "Stale";
  if (meter.data_quality === "historical_only") return "Historical";
  if (meter.data_quality === "no_readings") return "No readings";
  return "Needs review";
}

function valueText(value: number | null | undefined, unit: string) {
  return value == null ? "n/a" : `${formatNumber(value, 2)} ${unit}`;
}

export function MeterInventoryTable({ meters, alerts, systemMeters = [], selectedMeterId, onSelect }: MeterInventoryTableProps) {
  const alertCounts = new Map<string, number>();
  alerts.forEach((alert) => alertCounts.set(alert.meterId, (alertCounts.get(alert.meterId) ?? 0) + 1));
  const runtimeByMeterId = new Map(systemMeters.map((meter) => [meter.meterId, meter]));

  if (meters.length === 0) {
    return <div className="page-state page-state--padded">No configured meters are available.</div>;
  }

  return (
    <div className="table-shell meter-inventory__shell">
      <table className="meter-inventory">
        <thead>
          <tr>
            <th>Meter</th>
            <th>State</th>
            <th>Freshness</th>
            <th>kWh</th>
            <th>kVARh</th>
            <th>kVAh</th>
            <th>Alerts</th>
            <th>Last update</th>
          </tr>
        </thead>
        <tbody>
          {meters.map((meter) => {
            const runtime = runtimeByMeterId.get(meter.meter_id);
            const tone = statusTone(meter, runtime);
            return (
              <tr
                key={meter.meter_id}
                className={selectedMeterId === meter.meter_id ? "meter-inventory__row--selected" : ""}
                onClick={() => onSelect(meter.meter_id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelect(meter.meter_id);
                  }
                }}
                tabIndex={0}
                role="button"
              >
                <td>
                  <strong>{meter.meter_name}</strong>
                  <span className="table-subtle">{meter.location || meter.meter_id}</span>
                </td>
                <td><span className={`status-marker status-marker--${tone}`}>{runtime && !runtime.enabled ? "disabled" : runtime?.communicationStatus ?? meter.status}</span></td>
                <td><span className={`freshness-marker freshness-marker--${runtime && !runtime.staleWarning && runtime.communicationStatus === "online" ? "fresh" : "attention"}`}>{freshnessLabel(meter, runtime)}</span></td>
                <td className="meter-inventory__number">{valueText(meter.active_energy, "kWh")}</td>
                <td className="meter-inventory__number">{valueText(meter.reactive_energy, "kVARh")}</td>
                <td className="meter-inventory__number">{valueText(meter.apparent_energy, "kVAh")}</td>
                <td className="meter-inventory__alerts">{alertCounts.get(meter.meter_id) ?? 0}</td>
                <td className="table-subtle meter-inventory__updated">{formatTimestamp(runtime?.latestReadingTimestamp || meter.last_update)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
