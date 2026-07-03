import { useQuery } from "@tanstack/react-query";
import { fetchDashboardData } from "../api/energyApi";

export function useDashboardData(meterId: string, trendParameterKey = "active_power_total") {
  return useQuery({
    queryKey: ["dashboard", meterId, trendParameterKey],
    queryFn: () => fetchDashboardData(meterId, trendParameterKey),
    staleTime: 0,
    refetchInterval: 5_000,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
  });
}
