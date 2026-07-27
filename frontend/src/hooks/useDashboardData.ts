import { useQuery } from "@tanstack/react-query";
import { fetchDashboardData } from "../api/energyApi";

export function useDashboardData(meterId: string, trendParameterKey = "active_power_total", trendHours?: number) {
  return useQuery({
    queryKey: ["dashboard", meterId, trendParameterKey, trendHours ?? 0],
    queryFn: () => fetchDashboardData(meterId, trendParameterKey, trendHours),
    staleTime: 0,
    refetchInterval: 5_000,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
  });
}
