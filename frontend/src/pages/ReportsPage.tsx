import { Download, FileText, MailCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { EmailSettingsPanel } from "../components/reports/EmailSettingsPanel";
import { ReportSchedulePanel } from "../components/reports/ReportSchedulePanel";
import { SharedReportFilters } from "../components/reports/SharedReportFilters";
import { useReportMutations } from "../hooks/useEnergyMutations";
import { useEmailHealthData, useEmailSettingsData, useMetersData, useParameterCatalog, useReportSchedulesData } from "../hooks/useMetersData";
import { ENERGY_PARAMETER_KEYS } from "../lib/energyParameters";
import type { ReportFilters } from "../types/energy";

type ReportsPageProps = {
  selectedMeterId: string;
  onSelectMeter: (meterId: string) => void;
};

const toLocalDateTimeInputValue = (value: Date) => {
  const offsetMs = value.getTimezoneOffset() * 60 * 1000;
  return new Date(value.getTime() - offsetMs).toISOString().slice(0, 16);
};

const nowIso = () => toLocalDateTimeInputValue(new Date());
const startOfTodayIso = () => {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return toLocalDateTimeInputValue(now);
};

export function ReportsPage({ selectedMeterId, onSelectMeter }: ReportsPageProps) {
  const { data: meters = [] } = useMetersData();
  const { data: parameters = [] } = useParameterCatalog();
  const { data: schedules = [] } = useReportSchedulesData();
  const { data: emailSettings } = useEmailSettingsData();
  const { data: emailHealth } = useEmailHealthData();
  const reportMutations = useReportMutations();
  const exportError =
    reportMutations.excelExport.error instanceof Error
      ? reportMutations.excelExport.error.message
      : reportMutations.wordReport.error instanceof Error
        ? reportMutations.wordReport.error.message
        : null;
  const fallbackMeterId = selectedMeterId === "ALL" ? meters[0]?.meter_id ?? "" : selectedMeterId;
  const [filters, setFilters] = useState<ReportFilters>({
    meterId: fallbackMeterId,
    meterIds: fallbackMeterId ? [fallbackMeterId] : [],
    parameterKeys: [...ENERGY_PARAMETER_KEYS, "active_power_total", "voltage_l_minus_n_avg", "current_avg", "power_factor_total"],
    startDateTime: startOfTodayIso(),
    endDateTime: nowIso(),
    intervalHours: 1,
  });

  useEffect(() => {
    if (!fallbackMeterId) {
      return;
    }

    setFilters((current) => {
      if (current.meterIds.length > 0) {
        return current;
      }
      if (current.meterId === fallbackMeterId) {
        return { ...current, meterIds: fallbackMeterId ? [fallbackMeterId] : [] };
      }
      return { ...current, meterId: fallbackMeterId, meterIds: fallbackMeterId ? [fallbackMeterId] : [] };
    });
  }, [fallbackMeterId]);

  const selectedMeterNames = meters
    .filter((meter) => filters.meterIds.includes(meter.meter_id))
    .map((meter) => meter.meter_name);
  const dateRangeInvalid =
    Boolean(filters.startDateTime && filters.endDateTime) &&
    new Date(filters.startDateTime).getTime() > new Date(filters.endDateTime).getTime();
  const reportReady = filters.meterIds.length > 0 && filters.parameterKeys.length > 0 && !dateRangeInvalid;
  const emailReady = Boolean(emailHealth?.configured);

  const submitExport = (format: "excel" | "word") => {
    if (!reportReady) {
      return;
    }
    const meterIds = filters.meterIds.length > 0 ? filters.meterIds : filters.meterId ? [filters.meterId] : fallbackMeterId ? [fallbackMeterId] : [];
    const payload = { ...filters, meterId: meterIds[0] ?? "", meterIds };
    if (format === "excel") {
      reportMutations.excelExport.mutate(payload);
    } else {
      reportMutations.wordReport.mutate(payload);
    }
  };

  return (
    <section className="page-stack">
      <section className="page-toolbar">
        <div>
          <p className="section-label">Reports & Email</p>
          <h3 className="page-title">Report builder</h3>
        </div>
        <div className="report-builder__state">
          <span className="table-subtle">{filters.meterIds.length} meters / {filters.parameterKeys.length} parameters / {schedules.length} schedules</span>
          <span className={`status-pill status-pill--${reportReady ? "online" : "warning"}`}>{reportReady ? "Ready to export" : "Needs selection"}</span>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="section-label">Report setup</p>
            <h4>1. Scope and data</h4>
          </div>
        </div>
        <SharedReportFilters
          meters={meters}
          parameters={parameters}
          filters={filters}
          onChange={setFilters}
          onSelectMeter={onSelectMeter}
        />

        <div className="report-inline-summary report-inline-summary--stacked report-builder__summary">
          <span>
            <strong>Selected meters:</strong> {selectedMeterNames.length > 0 ? selectedMeterNames.join(", ") : "none"}
          </span>
          <span>
            <strong>Range:</strong> {filters.startDateTime} to {filters.endDateTime}
          </span>
          <span>
            <strong>Interval:</strong> {filters.intervalHours === null ? "All readings" : `Every ${filters.intervalHours} hour(s)`}
          </span>
          <span>
            <strong>Parameters:</strong> {filters.parameterKeys.length}
          </span>
        </div>

        <div className={`report-readiness report-readiness--${reportReady ? "ready" : "pending"}`}>
          <strong>{reportReady ? "Report filters ready" : "Finish filter selection"}</strong>
          <p>
            {dateRangeInvalid
              ? "Start date/time must be before end date/time."
              : reportReady
              ? "The selection is ready for file export or delivery."
              : "Choose at least one meter and one parameter before exporting or scheduling reports."}
          </p>
        </div>
      </section>

      <section className="reports-flow">
        <div className="panel">
          <div className="section-heading">
            <div>
              <p className="section-label">3. Output</p>
              <h4>Export files</h4>
            </div>
          </div>

          <div className="report-actions report-actions--wide">
            <button
              type="button"
              className="primary-button"
              onClick={() => submitExport("excel")}
              disabled={!reportReady || reportMutations.excelExport.isPending || reportMutations.wordReport.isPending}
            >
              <Download size={16} aria-hidden="true" />
              {reportMutations.excelExport.isPending ? "Generating..." : "Export Excel"}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => submitExport("word")}
              disabled={!reportReady || reportMutations.excelExport.isPending || reportMutations.wordReport.isPending}
            >
              <FileText size={16} aria-hidden="true" />
              {reportMutations.wordReport.isPending ? "Generating..." : "Generate Word"}
            </button>
          </div>

          {exportError ? <div className="page-state page-state--error page-state--padded">{exportError}</div> : null}

          <div className="report-status report-status--card">
            <p className="section-label">Status</p>
            <h4>{reportMutations.excelExport.data?.filename ?? reportMutations.wordReport.data?.filename ?? "Ready"}</h4>
            <p className="page-copy">
              {reportMutations.excelExport.data
                ? `${reportMutations.excelExport.data.rows} rows prepared for ${reportMutations.excelExport.data.meterName}.`
                : reportMutations.wordReport.data
                  ? `${reportMutations.wordReport.data.rows} rows prepared for ${reportMutations.wordReport.data.meterName}.`
                  : "Choose the filters, then download Excel or Word files."}
            </p>
          </div>
        </div>

        <div className="panel">
          <div className="section-heading">
            <div>
              <p className="section-label">3. Delivery</p>
              <h4>Send or schedule reports</h4>
            </div>
          </div>
          <ReportSchedulePanel
            filters={filters}
            schedules={schedules}
            onSave={(input) => reportMutations.saveReportSchedule.mutate(input)}
            onDelete={(scheduleId) => reportMutations.deleteReportSchedule.mutate(scheduleId)}
            onSendNow={(input) => reportMutations.sendReportEmail.mutate(input)}
            saving={reportMutations.saveReportSchedule.isPending}
            sendingNow={reportMutations.sendReportEmail.isPending}
            errorMessage={
              reportMutations.saveReportSchedule.error instanceof Error ? reportMutations.saveReportSchedule.error.message : null
            }
            sendNowError={reportMutations.sendReportEmail.error instanceof Error ? reportMutations.sendReportEmail.error.message : null}
            sendNowResult={reportMutations.sendReportEmail.data ?? null}
          />
        </div>

        <div className="panel">
          <details className="report-admin">
            <summary>
              <span><MailCheck size={15} aria-hidden="true" /> Email administration</span>
              <span className={`status-pill status-pill--${emailReady ? "online" : "warning"}`}>{emailReady ? "ready" : "setup needed"}</span>
            </summary>
            <EmailSettingsPanel
              settings={emailSettings}
              health={emailHealth}
              saving={reportMutations.saveEmailSettings.isPending}
              testing={reportMutations.sendEmailTest.isPending}
              saveError={
                reportMutations.saveEmailSettings.error instanceof Error ? reportMutations.saveEmailSettings.error.message : null
              }
              testError={reportMutations.sendEmailTest.error instanceof Error ? reportMutations.sendEmailTest.error.message : null}
              testResultMessage={
                reportMutations.sendEmailTest.data
                  ? `Test email sent to ${reportMutations.sendEmailTest.data.recipientEmails.join(", ")} using ${reportMutations.sendEmailTest.data.source} settings.`
                  : null
              }
              onSave={(input) => reportMutations.saveEmailSettings.mutate(input)}
              onSendTest={(recipientEmails) => reportMutations.sendEmailTest.mutate(recipientEmails)}
            />
          </details>
        </div>
      </section>
    </section>
  );
}
