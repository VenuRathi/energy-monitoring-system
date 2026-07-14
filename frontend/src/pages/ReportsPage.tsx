import { useEffect, useState } from "react";
import { EmailSettingsPanel } from "../components/reports/EmailSettingsPanel";
import { ReportSchedulePanel } from "../components/reports/ReportSchedulePanel";
import { SharedReportFilters } from "../components/reports/SharedReportFilters";
import { useReportMutations } from "../hooks/useEnergyMutations";
import { useEmailHealthData, useEmailSettingsData, useMetersData, useParameterCatalog, useReportSchedulesData } from "../hooks/useMetersData";
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
  const enabledMeters = meters.filter((meter) => meter.enabled).length;
  const [filters, setFilters] = useState<ReportFilters>({
    meterId: fallbackMeterId,
    meterIds: fallbackMeterId ? [fallbackMeterId] : [],
    parameterKeys: ["active_power_total", "voltage_l_minus_n_avg", "current_avg", "power_factor_total"],
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

  const submitExport = (format: "excel" | "word") => {
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
      <section className="dashboard__hero dashboard__hero--compact">
        <div className="dashboard__hero-copy">
          <p className="section-label">Reports and email</p>
          <h3 className="dashboard__headline">Prepare exports and scheduled report delivery</h3>
          <p className="dashboard__copy">
            Choose the meters and time range first, then download files or send the same report by email.
          </p>
        </div>

        <div className="dashboard__hero-actions">
          <div className="dashboard__summary dashboard__summary--compact">
            <div className="summary-card">
              <span className="summary-card__label">Enabled meters</span>
              <strong>{enabledMeters}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-card__label">Schedules</span>
              <strong>{schedules.length}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-card__label">Selected meters</span>
              <strong>{filters.meterIds.length}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-card__label">Selected parameters</span>
              <strong>{filters.parameterKeys.length}</strong>
            </div>
          </div>

          <div className="dashboard__control-card">
            <div className="dashboard__control-copy">
              <p className="section-label">Current export range</p>
              <h4>{filters.meterIds.length > 0 ? `${filters.meterIds.length} meter(s) selected` : "No meter selected"}</h4>
              <p className="dashboard__control-note">
                {filters.startDateTime} to {filters.endDateTime}
              </p>
            </div>
            <div className="dashboard__control-row">
              <span className={`status-pill status-pill--${emailHealth?.configured ? "online" : "warning"}`}>
                {emailHealth?.configured ? "email ready" : "email needs setup"}
              </span>
            </div>
            <p className="page-copy">
              Interval: {filters.intervalHours === null ? "All readings" : `Every ${filters.intervalHours} hour(s)`}
            </p>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="section-label">Report setup</p>
            <h4>Choose meter, time, and values</h4>
            <p className="page-copy">Work from top to bottom: select the meters, choose the time range, then download or email the report.</p>
          </div>
        </div>
        <SharedReportFilters
          meters={meters}
          parameters={parameters}
          filters={filters}
          onChange={setFilters}
          onSelectMeter={onSelectMeter}
        />
      </section>

      <section className="reports-flow">
        <div className="panel">
          <div className="section-heading">
            <div>
              <p className="section-label">Step 1</p>
              <h4>Download report files</h4>
            </div>
          </div>

          <div className="report-actions report-actions--wide">
            <button
              type="button"
              className="primary-button"
              onClick={() => submitExport("excel")}
              disabled={reportMutations.excelExport.isPending || reportMutations.wordReport.isPending}
            >
              {reportMutations.excelExport.isPending ? "Generating..." : "Export Excel"}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => submitExport("word")}
              disabled={reportMutations.excelExport.isPending || reportMutations.wordReport.isPending}
            >
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
              <p className="section-label">Step 2</p>
              <h4>Send or schedule email reports</h4>
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
          <div className="section-heading">
            <div>
              <p className="section-label">Step 3</p>
              <h4>Email account settings</h4>
            </div>
          </div>
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
        </div>
      </section>
    </section>
  );
}
