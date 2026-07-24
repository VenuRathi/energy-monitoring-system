import type { MeterEnergySummary } from "../../types/energy";
import { formatNumber, formatTimestamp } from "../../lib/formatters";

type AllMetersEnergyPanelProps = {
  meters: MeterEnergySummary[];
};

const ENERGY_FIELDS = [
  { key: "active_energy", label: "Active energy", unit: "kWh" },
  { key: "reactive_energy", label: "Reactive energy", unit: "kVARh" },
  { key: "apparent_energy", label: "Apparent energy", unit: "kVAh" },
] as const;

function formatEnergyValue(value: number | null) {
  return value === null ? "n/a" : formatNumber(value, 2);
}

export function AllMetersEnergyPanel({ meters }: AllMetersEnergyPanelProps) {
  if (meters.length === 0) {
    return <div className="page-state page-state--padded">No registered meters are available.</div>;
  }

  return (
    <section className="all-meter-energy-grid">
      {meters.map((meter) => (
        <article key={meter.meter_id} className="all-meter-energy-card">
          <div className="all-meter-energy-card__header">
            <div>
              <p className="section-label">{meter.meter_id}</p>
              <h5>{meter.meter_name}</h5>
              <span className="table-subtle">{meter.location || "No location set"}</span>
            </div>
            <span className={`status-pill status-pill--${meter.status}`}>{meter.status}</span>
          </div>

          <div className="all-meter-energy-card__values">
            {ENERGY_FIELDS.map((field) => (
              <div key={field.key} className="all-meter-energy-card__value">
                <span>{field.label}</span>
                <strong>{formatEnergyValue(meter[field.key])}</strong>
                <small>{field.unit}</small>
              </div>
            ))}
          </div>

          <div className="all-meter-energy-card__footer">
            <span>{meter.data_quality?.replaceAll("_", " ") ?? "n/a"}</span>
            <span>{formatTimestamp(meter.last_update)}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
