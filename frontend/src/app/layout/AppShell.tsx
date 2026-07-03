import { useEffect, useMemo, useState } from "react";
import { Header } from "../../components/layout/Header";
import { Sidebar } from "../../components/layout/Sidebar";
import { DashboardPage } from "../../pages/DashboardPage";
import { MetersPage } from "../../pages/MetersPage";
import { ReportsPage } from "../../pages/ReportsPage";
import { useMetersData } from "../../hooks/useMetersData";
import type { PageKey } from "../../types/energy";

export function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [page, setPage] = useState<PageKey>("dashboard");
  const [selectedMeterId, setSelectedMeterId] = useState("");
  const { data: meters = [] } = useMetersData();

  useEffect(() => {
    if (meters.length === 0) {
      return;
    }

    const isCurrentMeterValid = selectedMeterId === "ALL" || meters.some((meter) => meter.meter_id === selectedMeterId);
    if (!selectedMeterId || !isCurrentMeterValid) {
      setSelectedMeterId(meters[0].meter_id);
    }
  }, [meters, selectedMeterId]);

  const pageTitle = useMemo(() => {
    if (page === "dashboard") return "Dashboard";
    if (page === "meters") return "Meters";
    return "Reports";
  }, [page]);

  return (
    <div className="app-shell">
      <Sidebar
        activePage={page}
        open={sidebarOpen}
        onNavigate={(nextPage) => {
          setPage(nextPage);
          setSidebarOpen(false);
        }}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="app-shell__main">
        <Header pageTitle={pageTitle} onMenuClick={() => setSidebarOpen((value) => !value)} />
        <main className="app-shell__content">
          {page === "dashboard" ? (
            <DashboardPage
              selectedMeterId={selectedMeterId}
              onSelectMeter={setSelectedMeterId}
              onConfigureMeters={() => setPage("meters")}
            />
          ) : null}
          {page === "meters" ? (
            <MetersPage selectedMeterId={selectedMeterId} onSelectMeter={setSelectedMeterId} />
          ) : null}
          {page === "reports" ? (
            <ReportsPage selectedMeterId={selectedMeterId} onSelectMeter={setSelectedMeterId} />
          ) : null}
        </main>
      </div>
    </div>
  );
}
