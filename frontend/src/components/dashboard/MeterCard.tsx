import type { MeterRecord } from "../../types/energy";
import { formatNumber, formatTimestamp } from "../../lib/formatters";

type MeterCardProps = {
  meter: MeterRecord;
  active?: boolean;
  onClick?: (meterId: string) => void;
};

export function MeterCard({ meter, active = false, onClick }: MeterCardProps) {
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
          <p className="meter-card__detail">{meter.location || "Location not set"}</p>
          {meter.status_detail ? <p className="meter-card__detail">{meter.status_detail}</p> : null}
        </div>
        <span className={`status-pill status-pill--${tone}`}>{!meter.enabled ? "disabled" : meter.status}</span>
      </div>

      <dl className="meter-card__metrics">
        <div>
          <dt>Active Energy</dt>
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
        <div>
          <dt>Power Factor</dt>
          <dd>{meter.power_factor == null ? "n/a" : formatNumber(meter.power_factor, 3)}</dd>
        </div>
      </dl>

      <div className="meter-card__footer">
        <span>{meter.com_port || "COM n/a"} - Slave {meter.slave_id}</span>
        <span>{meter.seu ? "SEU" : "Non-SEU"}</span>
        <span>Updated {formatTimestamp(meter.last_update)}</span>
      </div>
    </button>
  );
}
