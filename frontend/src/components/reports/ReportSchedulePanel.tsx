import { CalendarClock, Pencil, Power, Send, Trash2, X } from "lucide-react";
import { useMemo, useState } from "react";
import { formatTimestamp } from "../../lib/formatters";
import { getDeliveryTime, toExplicitOffsetDateTime } from "../../lib/reportTime";
import type { ReportEmailResult, ReportFilters, ReportSchedule, ReportScheduleInput } from "../../types/energy";

type ReportSchedulePanelProps = {
  filters: ReportFilters;
  schedules: ReportSchedule[];
  onSave: (input: ReportScheduleInput) => void;
  onDelete: (scheduleId: number) => void;
  onChangeFilters: (next: ReportFilters) => void;
  onSendNow: (input: ReportFilters & { recipientEmails: string[]; sendTime?: string }) => void;
  saving: boolean;
  sendingNow: boolean;
  errorMessage?: string | null;
  sendNowError?: string | null;
  sendNowResult?: ReportEmailResult | null;
  deleteError?: string | null;
  deliveryMode?: "send-now" | "scheduled";
  showSchedules?: boolean;
  emailConfigured?: boolean;
  emailHealthMessage?: string;
  criteriaReady?: boolean;
};

export function ReportSchedulePanel({
  filters,
  schedules,
  onSave,
  onDelete,
  onChangeFilters,
  onSendNow,
  saving,
  sendingNow,
  errorMessage,
  sendNowError,
  sendNowResult,
  deleteError,
  deliveryMode = "send-now",
  showSchedules = false,
  emailConfigured,
  emailHealthMessage,
  criteriaReady = true,
}: ReportSchedulePanelProps) {
  const [recipientText, setRecipientText] = useState("");
  const [sendTime, setSendTime] = useState("08:00");
  const [scheduleName, setScheduleName] = useState("Daily energy report");
  const [editingScheduleId, setEditingScheduleId] = useState<number | null>(null);
  const [pendingDeleteSchedule, setPendingDeleteSchedule] = useState<ReportSchedule | null>(null);
  const [scheduleStartDate, setScheduleStartDate] = useState(() => {
    const today = new Date();
    const month = String(today.getMonth() + 1).padStart(2, "0");
    const day = String(today.getDate()).padStart(2, "0");
    return `${today.getFullYear()}-${month}-${day}`;
  });

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
      id: editingScheduleId ?? undefined,
      meterId: filters.meterId,
      meterIds: filters.meterIds,
      parameterKeys: filters.parameterKeys,
      recipientEmails: recipients,
      scheduleName: scheduleName.trim() || "Daily energy report",
      sendTime,
      scheduleStartDate,
      intervalHours: filters.intervalHours,
      enabled: true,
    });
  };

  const submitSendNow = () => {
    onSendNow({
      ...filters,
      startDateTime: toExplicitOffsetDateTime(filters.startDateTime),
      endDateTime: toExplicitOffsetDateTime(filters.endDateTime),
      recipientEmails: recipients,
    });
  };

  const beginEdit = (schedule: ReportSchedule) => {
    setEditingScheduleId(schedule.id);
    setScheduleName(schedule.scheduleName || "Daily energy report");
    setRecipientText(schedule.recipientEmails.join(", "));
    setSendTime(schedule.sendTime || "08:00");
    setScheduleStartDate(schedule.scheduleStartDate || scheduleStartDate);
    onChangeFilters({
      ...filters,
      meterId: schedule.meterId,
      meterIds: schedule.meterIds,
      parameterKeys: schedule.parameterKeys,
      intervalHours: schedule.intervalHours,
    });
  };

  const cancelEdit = () => {
    setEditingScheduleId(null);
    setScheduleName("Daily energy report");
    setRecipientText("");
  };

  const toggleSchedule = (schedule: ReportSchedule) => {
    onSave({
      id: schedule.id,
      meterId: schedule.meterId,
      meterIds: schedule.meterIds,
      parameterKeys: schedule.parameterKeys,
      recipientEmails: schedule.recipientEmails,
      scheduleName: schedule.scheduleName,
      sendTime: schedule.sendTime,
      scheduleStartDate: schedule.scheduleStartDate,
      intervalHours: schedule.intervalHours,
      enabled: !schedule.enabled,
    });
  };

  const nextSendText = (schedule: ReportSchedule) => {
    if (schedule.nextSendAt) {
      return formatTimestamp(schedule.nextSendAt);
    }

    const [hour, minute] = schedule.deliveryTime.split(":").map(Number);
    const now = new Date();
    const candidate = new Date(now);
    candidate.setHours(hour || 0, minute || 0, 0, 0);
    const startDate = new Date(`${schedule.scheduleStartDate}T00:00:00`);
    const localDateText = (value: Date) => {
      const month = String(value.getMonth() + 1).padStart(2, "0");
      const day = String(value.getDate()).padStart(2, "0");
      return `${value.getFullYear()}-${month}-${day}`;
    };
    if (!Number.isNaN(startDate.getTime()) && localDateText(candidate) <= schedule.scheduleStartDate) {
      candidate.setTime(startDate.getTime());
      candidate.setDate(candidate.getDate() + 1);
      candidate.setHours(hour || 0, minute || 0, 0, 0);
    }
    if (candidate <= now || schedule.lastSentOn === localDateText(candidate)) {
      candidate.setDate(candidate.getDate() + 1);
    }
    return `${candidate.toLocaleDateString()} ${schedule.deliveryTime}`;
  };

  return (
    <section className="page-stack">
      {errorMessage ? <div className="page-state page-state--error page-state--padded">{errorMessage}</div> : null}
      {sendNowError ? <div className="page-state page-state--error page-state--padded">{sendNowError}</div> : null}
      {deleteError ? <div className="page-state page-state--error page-state--padded">{deleteError}</div> : null}
      {sendNowResult ? (
        <div className="page-state page-state--padded">
          {sendNowResult.filename} sent to {sendNowResult.recipientEmails.join(", ")} for {sendNowResult.meterName}.
        </div>
      ) : null}

      {(deliveryMode === "send-now" || deliveryMode === "scheduled") && emailConfigured === false ? (
        <div className="email-readiness-warning">
          <strong>Email delivery is not ready.</strong>
          <span>{emailHealthMessage || "Configure and test SMTP in Email administration before sending or saving a schedule."}</span>
        </div>
      ) : null}
      {(deliveryMode === "send-now" || deliveryMode === "scheduled") && emailConfigured === true ? (
        <div className="email-readiness-warning email-readiness-warning--info">
          <strong>SMTP configured, connection not verified.</strong>
          <span>{emailHealthMessage || "Send a test email from Email administration before relying on delivery."}</span>
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
          {deliveryMode === "scheduled" ? (
            <>
              <label className="editor__field">
                <span>Schedule name</span>
                <input value={scheduleName} onChange={(event) => setScheduleName(event.target.value)} placeholder="Daily energy report" />
              </label>
              <label className="editor__field">
                <span>Start sending from</span>
                <input type="date" value={scheduleStartDate} onChange={(event) => setScheduleStartDate(event.target.value)} />
                <small className="field-help">The first delivery is the next day and contains the previous calendar day.</small>
              </label>
              <label className="editor__field">
                <span>Daily reading time</span>
                <input type="time" value={sendTime} onChange={(event) => setSendTime(event.target.value)} />
                <small className="field-help">Readings close at {sendTime} · Email sends around {getDeliveryTime(sendTime)}.</small>
              </label>
            </>
          ) : null}

        </div>

        <div className="report-email-form__actions">
          {deliveryMode === "send-now" ? (
            <button
              type="button"
              className="primary-button"
              onClick={submitSendNow}
              disabled={sendingNow || !criteriaReady || emailConfigured === false || recipients.length === 0}
            >
              <Send size={16} aria-hidden="true" />
              {sendingNow ? "Sending..." : "Send now"}
            </button>
          ) : (
            <>
              <button
                type="button"
                className="primary-button"
                onClick={submitSchedule}
                disabled={saving || !criteriaReady || emailConfigured === false || recipients.length === 0 || !scheduleStartDate || !sendTime}
              >
                <CalendarClock size={16} aria-hidden="true" />
                {saving ? "Saving..." : editingScheduleId ? "Update schedule" : "Save schedule"}
              </button>
              {editingScheduleId ? (
                <button type="button" className="ghost-button" onClick={cancelEdit}>
                  <X size={16} aria-hidden="true" />
                  Cancel edit
                </button>
              ) : null}
            </>
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
        {deliveryMode === "scheduled" ? (
          <span>
            <strong>Window:</strong> previous calendar day · starts {scheduleStartDate}
          </span>
        ) : (
          <span>
            <strong>Range:</strong> {filters.startDateTime} to {filters.endDateTime}
          </span>
        )}
        <span>
          <strong>Interval:</strong> {filters.intervalHours === null ? "All readings" : `Every ${filters.intervalHours} hour(s)`}
        </span>
        {deliveryMode === "scheduled" ? (
          <span>
            <strong>Daily timing:</strong> readings close at {sendTime} · email around {getDeliveryTime(sendTime)}
          </span>
        ) : (
          <span>
            <strong>Send now:</strong> uses the same date and time range as Excel export
          </span>
        )}
        {deliveryMode === "send-now" ? (
          <span>
            <strong>Delivery:</strong> one-time email
          </span>
        ) : null}
      </div>

      {showSchedules ? <div className="section-heading report-table-heading">
        <div>
          <p className="section-label">Saved schedules</p>
          <h4>Saved schedules</h4>
        </div>
      </div> : null}

      {showSchedules ? <div className="table-shell">
        <table className="latest-table latest-table--compact report-schedule-table">
          <thead>
            <tr>
              <th>Schedule</th>
              <th>Meters</th>
              <th>Parameters</th>
              <th>Window</th>
              <th>Starts</th>
              <th>Interval</th>
              <th>Recipients</th>
              <th>Reading time</th>
              <th>Email time</th>
              <th>Last sent</th>
              <th>Status</th>
              <th>Next send</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {schedules.length === 0 ? (
              <tr>
                <td colSpan={13}>No scheduled reports configured yet.</td>
              </tr>
            ) : (
              schedules.map((schedule) => (
                <tr key={schedule.id}>
                  <td className="latest-table__parameter">
                    <strong>{schedule.scheduleName}</strong>
                  </td>
                  <td>{schedule.meterName}</td>
                  <td>{schedule.parameterKeys.length}</td>
                  <td>Previous day</td>
                  <td>{schedule.scheduleStartDate || "n/a"}</td>
                  <td>{schedule.intervalHours === null ? "All readings" : `Every ${schedule.intervalHours} hour(s)`}</td>
                  <td>{schedule.recipientEmails.join(", ")}</td>
                  <td>{schedule.sendTime}</td>
                  <td>{schedule.deliveryTime}</td>
                  <td>{schedule.lastSentAt ? formatTimestamp(schedule.lastSentAt) : "Not sent yet"}</td>
                  <td>
                    <span className={`status-pill status-pill--${schedule.lastError ? "warning" : schedule.enabled ? "online" : "offline"}`}>
                      {schedule.lastError ? "Error" : schedule.enabled ? "Active" : "Disabled"}
                    </span>
                    {schedule.lastError ? <div className="table-subtle schedule-table__error">{schedule.lastError}</div> : null}
                  </td>
                  <td>{schedule.enabled ? nextSendText(schedule) : "Paused"}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="icon-button" onClick={() => beginEdit(schedule)} aria-label={`Edit ${schedule.scheduleName}`} title="Edit schedule">
                        <Pencil size={15} aria-hidden="true" />
                      </button>
                      <button type="button" className="icon-button" onClick={() => toggleSchedule(schedule)} aria-label={`${schedule.enabled ? "Disable" : "Enable"} ${schedule.scheduleName}`} title={schedule.enabled ? "Disable schedule" : "Enable schedule"}>
                        <Power size={15} aria-hidden="true" />
                      </button>
                      <button type="button" className="icon-button icon-button--danger" onClick={() => setPendingDeleteSchedule(schedule)} aria-label={`Delete ${schedule.scheduleName}`} title="Delete schedule">
                        <Trash2 size={16} aria-hidden="true" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div> : null}
      {pendingDeleteSchedule ? (
        <div className="report-delete-confirm" role="alertdialog" aria-label="Confirm schedule deletion">
          <div>
            <strong>Delete “{pendingDeleteSchedule.scheduleName}”?</strong>
            <span>This removes the saved schedule and stops future deliveries.</span>
          </div>
          <div className="report-delete-confirm__actions">
            <button type="button" className="ghost-button ghost-button--compact" onClick={() => setPendingDeleteSchedule(null)}>
              <X size={15} aria-hidden="true" />
              Cancel
            </button>
            <button
              type="button"
              className="ghost-button ghost-button--compact ghost-button--danger"
              onClick={() => {
                onDelete(pendingDeleteSchedule.id);
                setPendingDeleteSchedule(null);
              }}
            >
              <Trash2 size={15} aria-hidden="true" />
              Delete schedule
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
