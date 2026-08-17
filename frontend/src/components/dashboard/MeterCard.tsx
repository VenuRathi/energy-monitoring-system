import { Clock3, Cpu, MapPin, Zap } from "lucide-react";
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
          <p className="meter-card__detail meter-card__detail--icon">
            <MapPin size={14} aria-hidden="true" />
            {meter.location || "Location not set"}
          </p>
        </div>
        <span className={`status-pill status-pill--${tone}`}>{!meter.enabled ? "disabled" : meter.status}</span>
      </div>

      <dl className="meter-card__metrics">
        <div>
          <dt><Zap size={13} aria-hidden="true" /> Active Power</dt>
          <dd>{formatNumber(meter.base_power, 2)} kW</dd>
        </div>
        <div>
          <dt>Voltage L-N</dt>
          <dd>{formatNumber(meter.base_voltage, 1)} V</dd>
        </div>
        <div>
          <dt>Current</dt>
          <dd>{formatNumber(meter.base_current, 2)} A</dd>
        </div>
      </dl>

      <div className="meter-card__footer">
        <span><Cpu size={14} aria-hidden="true" /> {meter.com_port || "COM n/a"} - Slave {meter.slave_id}</span>
        <span><Clock3 size={14} aria-hidden="true" /> Updated {formatTimestamp(meter.last_update)}</span>
      </div>
    </button>
  );
}
