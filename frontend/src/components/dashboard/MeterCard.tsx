import { MapPin, Zap } from "lucide-react";
import type { MeterRecord } from "../../types/energy";
import { formatNumber } from "../../lib/formatters";

type MeterCardProps = {
  meter: MeterRecord;
  active?: boolean;
  alertCount?: number;
  onClick?: (meterId: string) => void;
};

export function MeterCard({ meter, active = false, alertCount = 0, onClick }: MeterCardProps) {
  const tone = !meter.enabled ? "offline" : meter.status === "online" && meter.data_quality === "live" ? "online" : meter.status === "offline" ? "offline" : "warning";

  return (
    <button
      type="button"
      className={`meter-card ${active ? "meter-card--active" : ""}`}
      onClick={() => onClick?.(meter.meter_id)}
    >
      <div className="meter-card__top">
        <div>
          <p className="meter-card__plant">{meter.meter_id}</p>
          <h5 className="meter-card__name">{meter.meter_name}</h5>
          <p className="meter-card__detail meter-card__detail--icon">
            <MapPin size={14} aria-hidden="true" />
            {meter.location || "Location not set"}
          </p>
        </div>
        <span className={`status-pill status-pill--${tone}`}>{!meter.enabled ? "disabled" : meter.status}</span>
      </div>

      <dl className="meter-card__metrics">
        <div>
          <dt><Zap size={13} aria-hidden="true" /> Active Energy</dt>
          <dd>{meter.active_energy == null ? "n/a" : `${formatNumber(meter.active_energy, 2)} kWh`}</dd>
        </div>
        <div>
          <dt>Reactive Energy</dt>
          <dd>{meter.reactive_energy == null ? "n/a" : `${formatNumber(meter.reactive_energy, 2)} kVARh`}</dd>
        </div>
        <div>
          <dt>Apparent Energy</dt>
          <dd>{meter.apparent_energy == null ? "n/a" : `${formatNumber(meter.apparent_energy, 2)} kVAh`}</dd>
        </div>
      </dl>

      {alertCount > 0 ? <span className="meter-card__alert-note">{alertCount} active alert{alertCount === 1 ? "" : "s"}</span> : null}
    </button>
  );
}
