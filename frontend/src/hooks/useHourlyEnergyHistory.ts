import { useQuery } from "@tanstack/react-query";
import { fetchHourlyEnergyHistory } from "../api/energyApi";

export function useHourlyEnergyHistory(meterId: string, hours = 72, enabled = true) {
  return useQuery({
    queryKey: ["hourly-energy", meterId, hours],
    queryFn: () => fetchHourlyEnergyHistory(meterId, hours),
    enabled: enabled && Boolean(meterId),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
