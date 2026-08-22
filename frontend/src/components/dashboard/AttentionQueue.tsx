import { AlertTriangle, RadioTower, TimerReset } from "lucide-react";
import type { AlertEvent, MeterRecord, SystemStatusMeter } from "../../types/energy";
import { formatNumber, formatTimestamp } from "../../lib/formatters";

type AttentionQueueProps = {
  alerts: AlertEvent[];
  meters: MeterRecord[];
  systemMeters: SystemStatusMeter[];
  meterId?: string;
  backendError?: string;
};

type AttentionItem = {
  key: string;
  tone: "warning" | "offline";
  icon: typeof AlertTriangle;
  title: string;
  meter: string;
  cause: string;
  action: string;
  age: string;
};

function thresholdText(alert: AlertEvent) {
  if (alert.minValue !== null && alert.maxValue !== null) return `${formatNumber(alert.minValue, 2)} to ${formatNumber(alert.maxValue, 2)} ${alert.unit}`;
  if (alert.minValue !== null) return `at least ${formatNumber(alert.minValue, 2)} ${alert.unit}`;
  if (alert.maxValue !== null) return `at most ${formatNumber(alert.maxValue, 2)} ${alert.unit}`;
  return "configured threshold";
}

export function AttentionQueue({ alerts, meters, systemMeters, meterId, backendError }: AttentionQueueProps) {
  const items: AttentionItem[] = [];

  if (backendError) {
    items.push({
      key: "backend",
      tone: "offline",
      icon: RadioTower,
      title: "Runtime status unavailable",
      meter: "Backend",
      cause: backendError,
      action: "Check the API and polling service.",
      age: "Now",
    });
  }

  alerts.filter((alert) => !meterId || alert.meterId === meterId).forEach((alert) => {
    items.push({
      key: `alert-${alert.id}`,
      tone: "warning",
      icon: AlertTriangle,
      title: alert.eventType || "Threshold alarm",
      meter: alert.meterName,
      cause: `${alert.parameterLabel} is outside ${thresholdText(alert)}.`,
      action: "Review the reading and trend before changing the threshold.",
      age: alert.timestamp ? formatTimestamp(alert.timestamp) : `${alert.date} ${alert.time}`,
    });
  });

  const meterById = new Map(meters.map((meter) => [meter.meter_id, meter]));
  systemMeters.filter((systemMeter) => !meterId || systemMeter.meterId === meterId).forEach((systemMeter) => {
    const meter = meterById.get(systemMeter.meterId);
    if (!meter || (systemMeter.communicationStatus === "online" && !systemMeter.staleWarning)) return;
    const offline = !systemMeter.enabled || systemMeter.communicationStatus === "offline";
    items.push({
      key: `meter-${systemMeter.meterId}`,
      tone: offline ? "offline" : "warning",
      icon: offline ? RadioTower : TimerReset,
      title: offline ? "Communication fault" : "Data freshness warning",
      meter: systemMeter.meterName,
      cause: systemMeter.diagnosticMessage || systemMeter.lastErrorMessage || (offline ? "No successful response from the meter." : "The latest reading is older than the polling expectation."),
      action: offline ? "Check COM port, slave ID, and RS485 wiring." : "Check the polling cycle and line stability.",
      age: formatTimestamp(systemMeter.lastSuccessfulReadingTime || systemMeter.lastPollAttemptTime),
    });
  });

  if (items.length === 0) {
    return <div className="attention-queue__empty">No active issues. All monitored meters are within expected state.</div>;
  }

  return (
    <div className="attention-queue">
      {items.slice(0, 8).map((item) => {
        const Icon = item.icon;
        return (
          <article key={item.key} className={`attention-item attention-item--${item.tone}`}>
            <span className="attention-item__marker"><Icon size={15} aria-hidden="true" /></span>
            <div className="attention-item__body">
              <div className="attention-item__top">
                <strong>{item.title}</strong>
                <span>{item.age}</span>
              </div>
              <span className="attention-item__meter">{item.meter}</span>
              <p>{item.cause}</p>
              <small>{item.action}</small>
            </div>
          </article>
        );
      })}
    </div>
  );
}
