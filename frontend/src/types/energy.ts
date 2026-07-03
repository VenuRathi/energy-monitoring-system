export type PageKey = "dashboard" | "meters" | "reports";

export type MeterStatus = "online" | "warning" | "offline";

export type MeterRecord = {
  meter_id: string;
  meter_name: string;
  location: string;
  manufacturer: string;
  model: string;
  protocol: string;
  enabled: boolean;
  seu: boolean;
  driver: string;
  com_port: string;
  slave_id: number;
  baud_rate: number;
  parity: string;
  stop_bits: number;
  byte_size: number;
  timeout: number;
  one_based_map: boolean;
  status: MeterStatus;
  data_quality?: "live" | "historical_only" | "zero_primary" | "no_readings" | "stale" | "disabled";
  status_detail?: string;
  has_readings?: boolean;
  live_measurements?: boolean;
  last_update: string;
  base_voltage: number;
  base_current: number;
  base_power: number;
  base_energy: number;
};

export type ParameterCategory =
  | "Voltage"
  | "Current"
  | "Power"
  | "Energy"
  | "Quality"
  | "Demand"
  | "System";

export type ParameterDataType = "number" | "datetime" | "code";

export type ParameterMeta = {
  key: string;
  label: string;
  category: ParameterCategory;
  unit: string;
  dataType: ParameterDataType;
  common: boolean;
  order: number;
};

export type MetricCard = {
  key: string;
  label: string;
  value: number | string;
  unit: string;
};

export type LatestReadingRow = {
  parameterKey: string;
  label: string;
  value: number | string;
  unit: string;
  timestamp: string;
  date: string;
  time: string;
  timestampSource: string;
};

export type TrendPoint = {
  timestamp: string;
  value: number;
};

export type DashboardData = {
  meters: MeterRecord[];
  selectedMeter: MeterRecord | null;
  summary: {
    totalMeters: number;
    onlineMeters: number;
    warningMeters: number;
    offlineMeters: number;
  };
  metrics: MetricCard[];
  latestReadings: LatestReadingRow[];
  parameterCatalog: ParameterMeta[];
  trendParameter: ParameterMeta;
  trendSeries: TrendPoint[];
  activeAlerts: AlertEvent[];
};

export type MeterInput = {
  meter_id?: string;
  meter_name: string;
  location: string;
  manufacturer: string;
  model: string;
  protocol: string;
  enabled: boolean;
  seu: boolean;
  driver: string;
  com_port: string;
  slave_id: number;
  baud_rate: number;
  parity: string;
  stop_bits: number;
  byte_size: number;
  timeout: number;
  one_based_map: boolean;
};

export type MeterDiscoveryInput = {
  com_port: string;
  baud_rate: number;
  parity: string;
  stop_bits: number;
  byte_size: number;
  timeout: number;
  one_based_map: boolean;
  scanStart: number;
  scanEnd: number;
};

export type MeterDiscoveryMatch = {
  slaveId: number;
  probeRegister: number;
  probeLabel: string;
  assignedMeterId: string;
  assignedMeterName: string;
  status?: "responding";
};

export type MeterDiscoveryResult = {
  comPort: string;
  scanStart: number;
  scanEnd: number;
  matches: MeterDiscoveryMatch[];
  recommendedSlaveId: number | null;
  message: string;
  usedSharedClient?: boolean;
};

export type MeterDiscoverySyncResult = {
  comPort: string;
  scanStart: number;
  scanEnd: number;
  respondingSlaveIds: number[];
  createdMeterIds: string[];
  updatedMeterIds: string[];
  offlineMeterIds: string[];
  disabledMeterIds?: string[];
  meters: MeterRecord[];
  message: string;
};

export type ReportFilters = {
  meterId: string;
  meterIds: string[];
  parameterKeys: string[];
  startDateTime: string;
  endDateTime: string;
  intervalHours: number | null;
};

export type AlertRule = {
  id: number;
  meterId: string;
  parameterKey: string;
  parameterLabel: string;
  unit: string;
  category: ParameterCategory;
  minValue: number | null;
  maxValue: number | null;
  enabled: boolean;
  isActive: boolean;
  lastValue: number | null;
  lastTriggeredAt: string;
  lastClearedAt: string;
  createdAt: string;
  updatedAt: string;
};

export type AlertRuleInput = {
  meterId: string;
  parameterKey: string;
  minValue: number | null;
  maxValue: number | null;
  enabled: boolean;
};

export type AlertEvent = {
  id: number;
  meterId: string;
  meterName: string;
  location: string;
  parameterKey: string;
  parameterLabel: string;
  unit: string;
  minValue: number | null;
  maxValue: number | null;
  value: number | null;
  eventType: string;
  timestamp: string;
  date: string;
  time: string;
};

export type ReportSchedule = {
  id: number;
  meterId: string;
  meterIds: string[];
  meterName: string;
  meterNames: string[];
  location: string;
  parameterKeys: string[];
  recipientEmails: string[];
  sendTime: string;
  deliveryTime: string;
  windowHours: number;
  enabled: boolean;
  lastSentOn: string;
  lastSentAt: string;
  lastError: string;
  createdAt: string;
  updatedAt: string;
};

export type ReportScheduleInput = {
  id?: number;
  meterId: string;
  meterIds: string[];
  parameterKeys: string[];
  recipientEmails: string[];
  sendTime: string;
  enabled: boolean;
};

export type ReportEmailInput = {
  meterId: string;
  meterIds: string[];
  parameterKeys: string[];
  recipientEmails: string[];
  startDateTime: string;
  endDateTime: string;
  intervalHours: number | null;
  sendTime?: string;
};

export type ReportEmailResult = {
  sent: boolean;
  recipientEmails: string[];
  meterName: string;
  filename: string;
  rows: number;
  sentAt: string;
};

export type ExportPreview = {
  format: "xlsx" | "docx";
  meterName: string;
  filename: string;
  rows: number;
  generatedAt: string;
};

export type EmailSettings = {
  smtpHost: string;
  smtpPort: number;
  smtpUsername: string;
  smtpFromEmail: string;
  smtpUseTls: boolean;
  smtpUseSsl: boolean;
  hasPassword: boolean;
  source: "env" | "database";
  updatedAt: string;
};

export type EmailSettingsInput = {
  smtpHost: string;
  smtpPort: number;
  smtpUsername: string;
  smtpPassword?: string;
  smtpFromEmail: string;
  smtpUseTls: boolean;
  smtpUseSsl: boolean;
};

export type EmailHealth = {
  configured: boolean;
  source: "env" | "database";
  smtpHost: string;
  smtpPort: number;
  smtpUsername: string;
  smtpFromEmail: string;
  smtpUseTls: boolean;
  smtpUseSsl: boolean;
  lastCheckedAt: string;
  message: string;
};

export type EmailTestResult = {
  sent: boolean;
  recipientEmails: string[];
  source: "env" | "database";
  sentAt: string;
};
