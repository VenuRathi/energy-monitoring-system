import type {
  AlertEvent,
  AlertRule,
  AlertRuleInput,
  DashboardData,
  EmailHealth,
  EmailSettings,
  EmailSettingsInput,
  EmailTestResult,
  ExportPreview,
  LatestReadingRow,
  MeterDiscoveryInput,
  MeterDiscoveryResult,
  MeterDiscoverySyncResult,
  MeterInput,
  MeterRecord,
  ParameterMeta,
  ReportFilters,
  ReportEmailInput,
  ReportEmailResult,
  ReportSchedule,
  ReportScheduleInput,
  TrendPoint,
} from "../types/energy";
import { requestJson, requestReportDownload } from "./httpClient";

export function fetchMeters(): Promise<MeterRecord[]> {
  return requestJson<MeterRecord[]>("/api/meters");
}

export function discoverMeters(input: MeterDiscoveryInput): Promise<MeterDiscoveryResult> {
  return requestJson<MeterDiscoveryResult>("/api/meters/discover", {
    method: "POST",
    body: JSON.stringify({
      com_port: input.com_port,
      baud_rate: input.baud_rate,
      parity: input.parity,
      stop_bits: input.stop_bits,
      byte_size: input.byte_size,
      timeout: input.timeout,
      one_based_map: input.one_based_map,
      scanStart: input.scanStart,
      scanEnd: input.scanEnd,
    }),
  });
}

export function syncDiscoveredMeters(input: MeterDiscoveryInput): Promise<MeterDiscoverySyncResult> {
  return requestJson<MeterDiscoverySyncResult>("/api/meters/discover/sync", {
    method: "POST",
    body: JSON.stringify({
      com_port: input.com_port,
      baud_rate: input.baud_rate,
      parity: input.parity,
      stop_bits: input.stop_bits,
      byte_size: input.byte_size,
      timeout: input.timeout,
      one_based_map: input.one_based_map,
      scanStart: input.scanStart,
      scanEnd: input.scanEnd,
    }),
  });
}

export function fetchParameters(): Promise<ParameterMeta[]> {
  return requestJson<ParameterMeta[]>("/api/parameters");
}

export function fetchDashboardData(meterId: string, trendParameterKey = "active_power_total"): Promise<DashboardData> {
  const query = new URLSearchParams({
    meterId,
    trendParameterKey,
  });
  return requestJson<DashboardData>(`/api/dashboard?${query.toString()}`);
}

export function fetchMeterReadings(meterId: string): Promise<LatestReadingRow[]> {
  return requestJson<LatestReadingRow[]>(`/api/meters/${encodeURIComponent(meterId)}/readings`);
}

export function fetchTrendSeries(meterId: string, parameterKey: string): Promise<TrendPoint[]> {
  const query = new URLSearchParams({
    parameterKey,
  });
  return requestJson<TrendPoint[]>(`/api/meters/${encodeURIComponent(meterId)}/trend?${query.toString()}`);
}

export function fetchAlertRules(meterId: string): Promise<AlertRule[]> {
  return requestJson<AlertRule[]>(`/api/meters/${encodeURIComponent(meterId)}/alert-rules`);
}

export function saveAlertRule(input: AlertRuleInput): Promise<AlertRule> {
  return requestJson<AlertRule>(`/api/meters/${encodeURIComponent(input.meterId)}/alert-rules`, {
    method: "POST",
    body: JSON.stringify({
      meterId: input.meterId,
      parameterKey: input.parameterKey,
      minValue: input.minValue,
      maxValue: input.maxValue,
      enabled: input.enabled,
    }),
  });
}

export function deleteAlertRule(ruleId: number): Promise<void> {
  return requestJson<void>(`/api/alert-rules/${ruleId}`, {
    method: "DELETE",
  });
}

export function fetchActiveAlerts(meterId?: string): Promise<AlertEvent[]> {
  const query = meterId ? `?${new URLSearchParams({ meterId }).toString()}` : "";
  return requestJson<AlertEvent[]>(`/api/alerts/active${query}`);
}

export function fetchReportSchedules(): Promise<ReportSchedule[]> {
  return requestJson<ReportSchedule[]>("/api/report-schedules");
}

export function saveReportSchedule(input: ReportScheduleInput): Promise<ReportSchedule> {
  const payload = {
    meterId: input.meterId,
    meterIds: input.meterIds,
    parameterKeys: input.parameterKeys,
    recipientEmails: input.recipientEmails,
    sendTime: input.sendTime,
    enabled: input.enabled,
  };

  if (input.id) {
    return requestJson<ReportSchedule>(`/api/report-schedules/${input.id}`, {
      method: "PUT",
      body: JSON.stringify({ ...payload, id: input.id }),
    });
  }

  return requestJson<ReportSchedule>("/api/report-schedules", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function removeReportSchedule(scheduleId: number): Promise<void> {
  return requestJson<void>(`/api/report-schedules/${scheduleId}`, {
    method: "DELETE",
  });
}

export function fetchEmailSettings(): Promise<EmailSettings> {
  return requestJson<EmailSettings>("/api/email/settings");
}

export function saveEmailSettings(input: EmailSettingsInput): Promise<EmailSettings> {
  return requestJson<EmailSettings>("/api/email/settings", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function fetchEmailHealth(): Promise<EmailHealth> {
  return requestJson<EmailHealth>("/api/email/health");
}

export function sendEmailTest(recipientEmails: string[]): Promise<EmailTestResult> {
  return requestJson<EmailTestResult>("/api/email/test", {
    method: "POST",
    body: JSON.stringify({ recipientEmails }),
  });
}

export function sendReportEmail(input: ReportEmailInput): Promise<ReportEmailResult> {
  return requestJson<ReportEmailResult>("/api/reports/email", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function upsertMeter(input: MeterInput): Promise<MeterRecord> {
  const payload = {
    meter_id: input.meter_id,
    meter_name: input.meter_name,
    location: input.location,
    manufacturer: input.manufacturer,
    model: input.model,
    protocol: input.protocol,
    enabled: input.enabled,
    seu: input.seu,
    driver: input.driver,
    com_port: input.com_port,
    slave_id: input.slave_id,
    baud_rate: input.baud_rate,
    parity: input.parity,
    stop_bits: input.stop_bits,
    byte_size: input.byte_size,
    timeout: input.timeout,
    one_based_map: input.one_based_map,
  };

  if (input.meter_id) {
    return requestJson<MeterRecord>(`/api/meters/${encodeURIComponent(input.meter_id)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }

  return requestJson<MeterRecord>("/api/meters", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function removeMeter(meterId: string): Promise<void> {
  return requestJson<void>(`/api/meters/${encodeURIComponent(meterId)}`, {
    method: "DELETE",
  });
}

export function createExcelExport(filters: ReportFilters): Promise<ExportPreview> {
  return requestReportDownload<ExportPreview>("/api/reports/excel", filters, "energy_report.xlsx");
}

export function createWordReport(filters: ReportFilters): Promise<ExportPreview> {
  return requestReportDownload<ExportPreview>("/api/reports/word", filters, "energy_report.docx");
}
