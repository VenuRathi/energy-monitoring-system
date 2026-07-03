import { useQuery } from "@tanstack/react-query";
import { fetchAlertRules, fetchEmailHealth, fetchEmailSettings, fetchMeters, fetchParameters, fetchReportSchedules } from "../api/energyApi";

export function useMetersData() {
  return useQuery({
    queryKey: ["meters"],
    queryFn: fetchMeters,
    staleTime: 0,
    refetchInterval: 10_000,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
  });
}

export function useParameterCatalog() {
  return useQuery({
    queryKey: ["parameters"],
    queryFn: fetchParameters,
    staleTime: 60_000,
    refetchOnWindowFocus: true,
  });
}

export function useAlertRulesData(meterId: string) {
  return useQuery({
    queryKey: ["alert-rules", meterId],
    queryFn: () => fetchAlertRules(meterId),
    enabled: Boolean(meterId),
    staleTime: 0,
    refetchOnWindowFocus: true,
  });
}

export function useReportSchedulesData() {
  return useQuery({
    queryKey: ["report-schedules"],
    queryFn: fetchReportSchedules,
    staleTime: 0,
    refetchInterval: 15_000,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
  });
}

export function useEmailSettingsData() {
  return useQuery({
    queryKey: ["email-settings"],
    queryFn: fetchEmailSettings,
    staleTime: 0,
    refetchOnWindowFocus: true,
  });
}

export function useEmailHealthData() {
  return useQuery({
    queryKey: ["email-health"],
    queryFn: fetchEmailHealth,
    staleTime: 0,
    refetchInterval: 30_000,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
  });
}
