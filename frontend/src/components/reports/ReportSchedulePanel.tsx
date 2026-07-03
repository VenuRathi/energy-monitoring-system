import { useMemo, useState } from "react";
import { formatTimestamp } from "../../lib/formatters";
import type { ReportEmailResult, ReportFilters, ReportSchedule, ReportScheduleInput } from "../../types/energy";

type ReportSchedulePanelProps = {
  filters: ReportFilters;
  schedules: ReportSchedule[];
  onSave: (input: ReportScheduleInput) => void;
  onDelete: (scheduleId: number) => void;
  onSendNow: (input: ReportFilters & { recipientEmails: string[]; sendTime?: string }) => void;
  saving: boolean;
  sendingNow: boolean;
  errorMessage?: string | null;
  sendNowError?: string | null;
  sendNowResult?: ReportEmailResult | null;
};

export function ReportSchedulePanel({
  filters,
  schedules,
  onSave,
  onDelete,
  onSendNow,
  saving,
  sendingNow,
  errorMessage,
  sendNowError,
  sendNowResult,
}: ReportSchedulePanelProps) {
  const [recipientText, setRecipientText] = useState("");
  const [sendTime, setSendTime] = useState("08:00");
  const [deliveryMode, setDeliveryMode] = useState<"now" | "schedule">("now");

  const recipients = useMemo(
    () =>
      recipientText
        .split(/[\n,;]+/)
        .map((value) => value.trim())
        .filter(Boolean),
    [recipientText],
  );
  const selectedMeterSummary = filters.meterIds.length === 0 ? "n/a" : `${filters.meterIds.length} meter${filters.meterIds.length === 1 ? "" : "s"}`;

  const submitSchedule = () => {
    onSave({
      meterId: filters.meterId,
      meterIds: filters.meterIds,
      parameterKeys: filters.parameterKeys,
      recipientEmails: recipients,
      sendTime,
      enabled: true,
    });
  };

  const submitSendNow = () => {
    onSendNow({
      ...filters,
      recipientEmails: recipients,
    });
  };

  return (
    <section className="page-stack">
      {errorMessage ? <div className="page-state page-state--error page-state--padded">{errorMessage}</div> : null}
      {sendNowError ? <div className="page-state page-state--error page-state--padded">{sendNowError}</div> : null}
      {sendNowResult ? (
        <div className="page-state page-state--padded">
          {sendNowResult.filename} sent to {sendNowResult.recipientEmails.join(", ")} for {sendNowResult.meterName}.
        </div>
      ) : null}

      <div className="report-email-form">
        <label className="editor__field report-email-form__recipients">
          <span>Recipients</span>
          <textarea
            className="editor__textarea"
            value={recipientText}
            onChange={(event) => setRecipientText(event.target.value)}
            placeholder="ops@example.com, energy@example.com"
          />
        </label>

        <div className="report-email-form__controls">
          <label className="editor__field">
            <span>Delivery</span>
            <select value={deliveryMode} onChange={(event) => setDeliveryMode(event.target.value as "now" | "schedule")}>
              <option value="now">Send now</option>
              <option value="schedule">Scheduled sending</option>
            </select>
          </label>

          {deliveryMode === "schedule" ? (
            <label className="editor__field">
              <span>Reading time</span>
              <input type="time" value={sendTime} onChange={(event) => setSendTime(event.target.value)} />
            </label>
          ) : null}

        </div>

        <div className="report-email-form__actions">
          {deliveryMode === "now" ? (
            <button
              type="button"
              className="primary-button"
              onClick={submitSendNow}
              disabled={sendingNow || filters.meterIds.length === 0 || filters.parameterKeys.length === 0 || recipients.length === 0}
            >
              {sendingNow ? "Sending..." : "Send now"}
            </button>
          ) : (
            <button
              type="button"
              className="primary-button"
              onClick={submitSchedule}
              disabled={saving || filters.meterIds.length === 0 || filters.parameterKeys.length === 0 || recipients.length === 0}
            >
              {saving ? "Saving..." : "Save schedule"}
            </button>
          )}
        </div>
      </div>

      <div className="report-inline-summary">
        <span>
          <strong>{filters.parameterKeys.length}</strong> parameters
        </span>
        <span>
          <strong>Meters:</strong> {selectedMeterSummary}
        </span>
        <span>
          <strong>Range:</strong> {filters.startDateTime} to {filters.endDateTime}
        </span>
        <span>
          <strong>Interval:</strong> {filters.intervalHours === null ? "All readings" : `Every ${filters.intervalHours} hour(s)`}
        </span>
        {deliveryMode === "schedule" ? (
          <span>
            <strong>Email time:</strong> about 5 minutes after {sendTime}
          </span>
        ) : (
          <span>
            <strong>Send now:</strong> uses the same date and time range as Excel export
          </span>
        )}
      </div>

      {filters.parameterKeys.length > 0 ? (
        <div className="report-selected report-selected--compact">
          <span className="report-selected__label">Selected parameters</span>
          <div className="report-selected__chips">
            {filters.parameterKeys.map((parameterKey) => (
              <span key={parameterKey} className="report-selected__chip report-selected__chip--static">
                <span>{parameterKey}</span>
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div className="section-heading report-table-heading">
        <div>
          <p className="section-label">Saved schedules</p>
          <h4>Saved schedules</h4>
        </div>
      </div>

      <div className="table-shell">
        <table className="latest-table latest-table--compact">
          <thead>
            <tr>
              <th>Meter</th>
              <th>Recipients</th>
              <th>Reading time</th>
              <th>Email time</th>
              <th>Last sent</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {schedules.length === 0 ? (
              <tr>
                <td colSpan={7}>No scheduled reports configured yet.</td>
              </tr>
            ) : (
              schedules.map((schedule) => (
                <tr key={schedule.id}>
                  <td className="latest-table__parameter">
                    <strong>{schedule.meterName}</strong>
                    <div className="table-subtle">{schedule.parameterKeys.length} parameter(s)</div>
                  </td>
                  <td>{schedule.recipientEmails.join(", ")}</td>
                  <td>{schedule.sendTime}</td>
                  <td>{schedule.deliveryTime}</td>
                  <td>{schedule.lastSentAt ? formatTimestamp(schedule.lastSentAt) : "Not sent yet"}</td>
                  <td>{schedule.lastError ? schedule.lastError : schedule.enabled ? "Ready" : "Disabled"}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="ghost-button ghost-button--danger" onClick={() => onDelete(schedule.id)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
