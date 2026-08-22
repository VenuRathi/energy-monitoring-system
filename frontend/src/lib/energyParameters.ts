import type { LatestReadingRow, MetricCard, ParameterMeta } from "../types/energy";

export const ENERGY_PARAMETER_KEYS = [
  "active_energy_received_out_of_load",
  "reactive_energy_received",
  "apparent_energy_received",
] as const;

export type EnergyParameterKey = (typeof ENERGY_PARAMETER_KEYS)[number];

export const ENERGY_PARAMETER_DEFINITIONS: Record<EnergyParameterKey, { label: string; unit: string }> = {
  active_energy_received_out_of_load: { label: "Active Energy", unit: "kWh" },
  reactive_energy_received: { label: "Reactive Energy", unit: "kVARh" },
  apparent_energy_received: { label: "Apparent Energy", unit: "kVAh" },
};

const ENERGY_PRIORITY = new Map<string, number>(ENERGY_PARAMETER_KEYS.map((key, index) => [key, index]));

export function isEnergyParameterKey(key: string) {
  return ENERGY_PRIORITY.has(key);
}

export function energyDisplayDecimals(key: string) {
  return isEnergyParameterKey(key) ? 3 : 2;
}

export function energyParameterPriority(key: string) {
  return ENERGY_PRIORITY.get(key) ?? ENERGY_PARAMETER_KEYS.length;
}

export function sortParametersByEnergyPriority(parameters: ParameterMeta[]) {
  return [...parameters].sort((left, right) => {
    const priorityDifference = energyParameterPriority(left.key) - energyParameterPriority(right.key);
    if (priorityDifference !== 0) return priorityDifference;
    return left.order - right.order || left.label.localeCompare(right.label);
  });
}

export function sortMetricsByEnergyPriority(metrics: MetricCard[]) {
  return [...metrics]
    .filter((metric) => ENERGY_PRIORITY.has(metric.key))
    .sort((left, right) => energyParameterPriority(left.key) - energyParameterPriority(right.key));
}

export function sortLatestReadingsByEnergyPriority(rows: LatestReadingRow[]) {
  return rows
    .map((row, index) => ({ row, index }))
    .sort((left, right) => energyParameterPriority(left.row.parameterKey) - energyParameterPriority(right.row.parameterKey) || left.index - right.index)
    .map(({ row }) => row);
}
