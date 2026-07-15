import { useEffect, useMemo, useState } from "react";
import { APP_META } from "../appMeta";
import { Header } from "../../components/layout/Header";
import { Sidebar } from "../../components/layout/Sidebar";
import { DashboardPage } from "../../pages/DashboardPage";
import { HelpPage } from "../../pages/HelpPage";
import { MetersPage } from "../../pages/MetersPage";
import { ReportsPage } from "../../pages/ReportsPage";
import { useMetersData } from "../../hooks/useMetersData";
import type { PageKey } from "../../types/energy";

export function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [page, setPage] = useState<PageKey>("dashboard");
  const [selectedMeterId, setSelectedMeterId] = useState("");
  const { data: meters = [] } = useMetersData();
  const activeMeters = useMemo(() => {
    const enabledMeters = meters.filter((meter) => meter.enabled);
    return enabledMeters.length > 0 ? enabledMeters : meters;
  }, [meters]);

  useEffect(() => {
    if (activeMeters.length === 0) {
      return;
    }

    const isCurrentMeterValid =
      selectedMeterId === "ALL" || activeMeters.some((meter) => meter.meter_id === selectedMeterId);
    if (!selectedMeterId || !isCurrentMeterValid) {
      setSelectedMeterId(activeMeters[0].meter_id);
    }
  }, [activeMeters, selectedMeterId]);

  const pageTitle = useMemo(() => {
    if (page === "dashboard") return "Live View";
    if (page === "meters") return "Meter Setup";
    if (page === "reports") return "Reports & Email";
    return "Help & Guide";
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
        <Header
          pageTitle={pageTitle}
          systemName={APP_META.systemName}
          version={APP_META.version}
          deploymentMode={APP_META.deploymentMode}
          onMenuClick={() => setSidebarOpen((value) => !value)}
        />
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
          {page === "help" ? <HelpPage /> : null}
        </main>
      </div>
    </div>
  );
}
