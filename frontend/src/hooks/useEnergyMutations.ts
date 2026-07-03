import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createExcelExport,
  discoverMeters,
  sendReportEmail,
  createWordReport,
  deleteAlertRule,
  removeMeter,
  removeReportSchedule,
  saveEmailSettings,
  saveAlertRule,
  saveReportSchedule,
  sendEmailTest,
  syncDiscoveredMeters,
  upsertMeter,
} from "../api/energyApi";
import type { AlertRuleInput, EmailSettingsInput, MeterDiscoveryInput, MeterInput, ReportFilters, ReportScheduleInput } from "../types/energy";

export function useMeterMutations() {
  const queryClient = useQueryClient();

  const invalidateMeters = async () => {
    await queryClient.invalidateQueries({ queryKey: ["meters"] });
    await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  return {
    saveMeter: useMutation({
      mutationFn: (input: MeterInput) => upsertMeter(input),
      onSuccess: invalidateMeters,
    }),
    deleteMeter: useMutation({
      mutationFn: (meterId: string) => removeMeter(meterId),
      onSuccess: invalidateMeters,
    }),
    discoverMeters: useMutation({
      mutationFn: (input: MeterDiscoveryInput) => discoverMeters(input),
    }),
    syncDiscoveredMeters: useMutation({
      mutationFn: (input: MeterDiscoveryInput) => syncDiscoveredMeters(input),
      onSuccess: invalidateMeters,
    }),
  };
}

export function useReportMutations() {
  const queryClient = useQueryClient();

  return {
    excelExport: useMutation({
      mutationFn: (filters: ReportFilters) => createExcelExport(filters),
    }),
    wordReport: useMutation({
      mutationFn: (filters: ReportFilters) => createWordReport(filters),
    }),
    sendReportEmail: useMutation({
      mutationFn: (input: ReportFilters & { recipientEmails: string[]; sendTime?: string }) =>
        sendReportEmail({
          meterId: input.meterId,
          meterIds: input.meterIds,
          parameterKeys: input.parameterKeys,
          recipientEmails: input.recipientEmails,
          startDateTime: input.startDateTime,
          endDateTime: input.endDateTime,
          intervalHours: input.intervalHours,
          sendTime: input.sendTime,
        }),
    }),
    saveAlertRule: useMutation({
      mutationFn: (input: AlertRuleInput) => saveAlertRule(input),
      onSuccess: async (_, variables) => {
        await queryClient.invalidateQueries({ queryKey: ["alert-rules", variables.meterId] });
        await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      },
    }),
    deleteAlertRule: useMutation({
      mutationFn: (ruleId: number) => deleteAlertRule(ruleId),
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: ["alert-rules"] });
        await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      },
    }),
    saveReportSchedule: useMutation({
      mutationFn: (input: ReportScheduleInput) => saveReportSchedule(input),
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: ["report-schedules"] });
      },
    }),
    deleteReportSchedule: useMutation({
      mutationFn: (scheduleId: number) => removeReportSchedule(scheduleId),
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: ["report-schedules"] });
      },
    }),
    saveEmailSettings: useMutation({
      mutationFn: (input: EmailSettingsInput) => saveEmailSettings(input),
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: ["email-settings"] });
        await queryClient.invalidateQueries({ queryKey: ["email-health"] });
      },
    }),
    sendEmailTest: useMutation({
      mutationFn: (recipientEmails: string[]) => sendEmailTest(recipientEmails),
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: ["email-health"] });
      },
    }),
  };
}
