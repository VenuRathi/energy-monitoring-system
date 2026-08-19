import { CalendarClock, Download, FileText, MailCheck, Send } from "lucide-react";
import { useEffect, useState } from "react";
import { EmailSettingsPanel } from "../components/reports/EmailSettingsPanel";
import { ReportCriteria } from "../components/reports/ReportCriteria";
import { ReportSchedulePanel } from "../components/reports/ReportSchedulePanel";
import { SharedReportFilters } from "../components/reports/SharedReportFilters";
import { useReportMutations } from "../hooks/useEnergyMutations";
import { useEmailHealthData, useEmailSettingsData, useMetersData, useParameterCatalog, useReportSchedulesData } from "../hooks/useMetersData";
import { ENERGY_PARAMETER_KEYS } from "../lib/energyParameters";
import { toExplicitOffsetDateTime } from "../lib/reportTime";
import type { ReportFilters } from "../types/energy";

type ReportsPageProps = {
  selectedMeterId: string;
  onSelectMeter: (meterId: string) => void;
};

type WorkflowMode = "report" | "send-now" | "scheduled";

const WORKFLOW_MODES: Array<{
  key: WorkflowMode;
  label: string;
  description: string;
}> = [
  { key: "report", label: "Generate report", description: "Download an Excel or Word file without email delivery." },
  { key: "send-now", label: "Email send now", description: "Send one report immediately to selected recipients." },
  { key: "scheduled", label: "Scheduled email", description: "Save a daily delivery at the configured reading time." },
];

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
  const [workflowMode, setWorkflowMode] = useState<WorkflowMode>("report");
  const [emailAdminOpen, setEmailAdminOpen] = useState(false);
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
        return { ...current, meterIds: [fallbackMeterId] };
      }
      return { ...current, meterId: fallbackMeterId, meterIds: [fallbackMeterId] };
    });
  }, [fallbackMeterId]);

  const selectedMeterNames = meters
    .filter((meter) => filters.meterIds.includes(meter.meter_id))
    .map((meter) => meter.meter_name);
  const dateRangeInvalid =
    Boolean(filters.startDateTime && filters.endDateTime) &&
    new Date(filters.startDateTime).getTime() >= new Date(filters.endDateTime).getTime();
  const baseCriteriaReady = filters.meterIds.length > 0 && filters.parameterKeys.length > 0;
  const reportReady = baseCriteriaReady && !dateRangeInvalid;
  const workflowReady = baseCriteriaReady && (workflowMode === "scheduled" || !dateRangeInvalid);
  const emailReady = emailHealth?.configured;
  const activeMode = WORKFLOW_MODES.find((mode) => mode.key === workflowMode) ?? WORKFLOW_MODES[0];

  useEffect(() => {
    if (emailHealth && !emailHealth.configured) {
      setEmailAdminOpen(true);
    }
  }, [emailHealth]);

  const submitExport = (format: "excel" | "word") => {
    if (!reportReady) {
      return;
    }
    const meterIds = filters.meterIds.length > 0 ? filters.meterIds : filters.meterId ? [filters.meterId] : fallbackMeterId ? [fallbackMeterId] : [];
    const payload = {
      ...filters,
      meterId: meterIds[0] ?? "",
      meterIds,
      startDateTime: toExplicitOffsetDateTime(filters.startDateTime),
      endDateTime: toExplicitOffsetDateTime(filters.endDateTime),
    };
    if (format === "excel") {
      reportMutations.excelExport.mutate(payload);
    } else {
      reportMutations.wordReport.mutate(payload);
    }
  };

  const renderCriteria = () => (
    <div className="report-workflow__criteria">
      <div className="section-heading">
        <div>
          <p className="section-label">Step 3</p>
          <h4>Set report details</h4>
        </div>
        <span className="table-subtle">Applies to {activeMode.label.toLowerCase()}</span>
      </div>
      <ReportCriteria parameters={parameters} filters={filters} onChange={setFilters} includeDateRange={workflowMode !== "scheduled"} />
      <div className={`report-readiness report-readiness--${workflowReady ? "ready" : "pending"}`}>
        <strong>{workflowReady ? "Ready to continue" : "Finish the required details"}</strong>
        <p>
          {workflowMode !== "scheduled" && dateRangeInvalid
            ? "Start date/time must be before end date/time."
            : workflowReady
              ? workflowMode === "scheduled"
                ? `${selectedMeterNames.length} meter(s) and ${filters.parameterKeys.length} parameter(s) are ready for the previous-day window.`
                : `${selectedMeterNames.length} meter(s), ${filters.parameterKeys.length} parameter(s), and the selected time range are ready.`
              : "Choose at least one meter and one parameter before continuing."}
        </p>
      </div>
    </div>
  );

  return (
    <section className="page-stack reports-page">
      <section className="page-toolbar">
        <div>
          <p className="section-label">Reports & Email</p>
          <h3 className="page-title">Choose meters, then choose an action</h3>
        </div>
        <div className="report-builder__state">
          <span className="table-subtle">{filters.meterIds.length} meters selected</span>
          <span className={`status-pill status-pill--${workflowReady ? "online" : "warning"}`}>{workflowReady ? "Criteria ready" : "Needs selection"}</span>
        </div>
      </section>

      <section className="panel report-workflow__step">
        <div className="section-heading">
          <div>
            <p className="section-label">Step 1</p>
            <h4>Choose meters</h4>
            <p className="page-copy">Select the meters that should be included in this report or email.</p>
          </div>
        </div>
        <SharedReportFilters
          meters={meters}
          filters={filters}
          onChange={setFilters}
          onSelectMeter={onSelectMeter}
        />
      </section>

      <section className="panel report-workflow__step">
        <div className="section-heading">
          <div>
            <p className="section-label">Step 2</p>
            <h4>Choose what to do</h4>
          </div>
        </div>
        <div className="report-workflow__modes" role="tablist" aria-label="Report action">
          {WORKFLOW_MODES.map((mode) => {
            const Icon = mode.key === "report" ? FileText : mode.key === "send-now" ? Send : CalendarClock;
            return (
              <button
                key={mode.key}
                type="button"
                role="tab"
                aria-selected={workflowMode === mode.key}
                className={`report-workflow__mode ${workflowMode === mode.key ? "report-workflow__mode--active" : ""}`}
                onClick={() => setWorkflowMode(mode.key)}
              >
                <span className="report-workflow__mode-icon"><Icon size={17} aria-hidden="true" /></span>
                <span>
                  <strong>{mode.label}</strong>
                  <small>{mode.description}</small>
                </span>
              </button>
            );
          })}
        </div>
        <div className="report-workflow__active-summary">
          <strong>{activeMode.label}</strong>
          <span>{activeMode.description}</span>
        </div>
      </section>

      {workflowMode === "report" ? (
        <section className="panel report-workflow__action-panel report-workflow__action-panel--report">
          <div className="section-heading">
            <div>
              <p className="section-label">Generate report only</p>
              <h4>Download a report file</h4>
            </div>
          </div>
          {renderCriteria()}
          <p className="report-workflow__quiet-note">This creates a file only. No email is sent and no schedule is changed.</p>
          <div className="report-actions report-actions--wide">
            <button
              type="button"
              className="primary-button"
              onClick={() => submitExport("excel")}
              disabled={!reportReady || reportMutations.excelExport.isPending || reportMutations.wordReport.isPending}
            >
              <Download size={16} aria-hidden="true" />
              {reportMutations.excelExport.isPending ? "Generating..." : "Download Excel"}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => submitExport("word")}
              disabled={!reportReady || reportMutations.excelExport.isPending || reportMutations.wordReport.isPending}
            >
              <FileText size={16} aria-hidden="true" />
              {reportMutations.wordReport.isPending ? "Generating..." : "Download Word"}
            </button>
          </div>
          {exportError ? <div className="page-state page-state--error page-state--padded">{exportError}</div> : null}
          <div className="report-status report-status--card">
            <p className="section-label">Export status</p>
            <h4>{reportMutations.excelExport.data?.filename ?? reportMutations.wordReport.data?.filename ?? "No file generated yet"}</h4>
            <p className="page-copy">
              {reportMutations.excelExport.data
                ? `${reportMutations.excelExport.data.rows} rows prepared for ${reportMutations.excelExport.data.meterName}.`
                : reportMutations.wordReport.data
                  ? `${reportMutations.wordReport.data.rows} rows prepared for ${reportMutations.wordReport.data.meterName}.`
                  : "The file will use the meters, parameters, range, and interval selected above."}
            </p>
          </div>
        </section>
      ) : (
        <section className="panel report-workflow__action-panel">
          <div className="section-heading">
            <div>
              <p className="section-label">{workflowMode === "send-now" ? "Email send now" : "Scheduled email"}</p>
              <h4>{workflowMode === "send-now" ? "Send one report immediately" : "Save a daily report delivery"}</h4>
            </div>
          </div>
          {renderCriteria()}
          <ReportSchedulePanel
            filters={filters}
            schedules={schedules}
            deliveryMode={workflowMode}
            showSchedules={workflowMode === "scheduled"}
            emailConfigured={emailReady}
            emailHealthMessage={emailHealth?.message}
            criteriaReady={workflowReady}
            onChangeFilters={setFilters}
            onSave={(input) => reportMutations.saveReportSchedule.mutate(input)}
            onDelete={(scheduleId) => reportMutations.deleteReportSchedule.mutate(scheduleId)}
            onSendNow={(input) => reportMutations.sendReportEmail.mutate(input)}
            saving={workflowMode === "scheduled" && reportMutations.saveReportSchedule.isPending}
            sendingNow={reportMutations.sendReportEmail.isPending}
            errorMessage={
              workflowMode === "scheduled" && reportMutations.saveReportSchedule.error instanceof Error
                ? reportMutations.saveReportSchedule.error.message
                : null
            }
            deleteError={
              workflowMode === "scheduled" && reportMutations.deleteReportSchedule.error instanceof Error
                ? reportMutations.deleteReportSchedule.error.message
                : null
            }
            sendNowError={
              workflowMode === "send-now" && reportMutations.sendReportEmail.error instanceof Error
                ? reportMutations.sendReportEmail.error.message
                : null
            }
            sendNowResult={workflowMode === "send-now" ? reportMutations.sendReportEmail.data ?? null : null}
          />
        </section>
      )}

      {workflowMode !== "report" ? (
        <details
          className={`report-admin ${emailReady === false ? "report-admin--attention" : ""}`}
          open={emailAdminOpen}
          onToggle={(event) => setEmailAdminOpen((event.currentTarget as HTMLDetailsElement).open)}
        >
          <summary>
            <span><MailCheck size={15} aria-hidden="true" /> Email administration</span>
            {emailHealth ? (
              <span className={`status-pill status-pill--${emailReady ? "configured" : "warning"}`}>{emailReady ? "configured · unverified" : "setup needed"}</span>
            ) : (
              <span className="table-subtle">Checking SMTP</span>
            )}
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
      ) : null}
    </section>
  );
}
