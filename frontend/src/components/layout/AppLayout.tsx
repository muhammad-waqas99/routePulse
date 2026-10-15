import { useEffect, useState } from "react";
import { Bell, Menu } from "lucide-react";

import { navigationItems, type PageId } from "../../config/navigation";
import { useOperationsOverview } from "../../hooks/useOperationsOverview";
import OperationsPage from "../../pages/OperationPage";
import PerformanceLab from "../../pages/PerformanceLab";
import RecoveryPlanner from "../../pages/RecoveryPlanner";
import AlertItem from "../dashboard/AlertItem";
import Sidebar from "./Sidebar";

export default function AppLayout() {
  const [activePage, setActivePage] = useState<PageId>("operations");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);

  const { data: overview } = useOperationsOverview();

  const activeAlerts = (overview?.alerts ?? []).filter(
    (alert) => alert.status === "active",
  );

  const activeItem = navigationItems.find(
    (item) => item.id === activePage,
  );

  function handleNavigate(pageId: PageId) {
    setActivePage(pageId);
    setIsSidebarOpen(false);
    setIsNotificationsOpen(false);
  }

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsSidebarOpen(false);
        setIsNotificationsOpen(false);
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  return (
    <div className="flex h-dvh overflow-hidden bg-background text-foreground">
      <Sidebar
        activePage={activePage}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onNavigate={handleNavigate}
      />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-3 border-b border-border bg-white px-4 sm:px-6 lg:px-8">
          <button
            type="button"
            aria-label="Open navigation menu"
            aria-controls="app-sidebar"
            aria-expanded={isSidebarOpen}
            onClick={() => setIsSidebarOpen(true)}
            className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-slate-100 lg:hidden"
          >
            <Menu size={22} aria-hidden="true" />
          </button>

          <div className="min-w-0 flex-1">
            <h2 className="truncate text-lg font-semibold text-foreground">
              {activeItem?.label ?? "Operations"}
            </h2>

            <p className="hidden text-xs text-muted-foreground sm:block">
              Campus Transport Intelligence
            </p>
          </div>

          <div className="relative">
            <button
              type="button"
              aria-label="Toggle notifications"
              aria-expanded={isNotificationsOpen}
              onClick={() =>
                setIsNotificationsOpen((open) => !open)
              }
              className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-border bg-white text-muted-foreground transition-colors hover:bg-slate-50 hover:text-foreground"
            >
              <Bell size={20} aria-hidden="true" />

              {activeAlerts.length > 0 && (
                <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-semibold text-white">
                  {activeAlerts.length}
                </span>
              )}
            </button>

            {isNotificationsOpen && (
              <div
                role="region"
                aria-label="Notifications"
                className="absolute right-0 top-full z-50 mt-3 w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-xl border border-border bg-white shadow-lg"
              >
                <div className="flex items-center justify-between border-b border-border px-4 py-3">
                  <h3 className="text-sm font-semibold text-foreground">
                    Notifications
                  </h3>

                  <span className="text-xs text-muted-foreground">
                    {activeAlerts.length} active
                  </span>
                </div>

                <div className="max-h-80 overflow-y-auto p-3">
                  {activeAlerts.length > 0 ? (
                    <div className="space-y-3">
                      {activeAlerts.map((alert) => (
                        <AlertItem key={alert.id} alert={alert} />
                      ))}
                    </div>
                  ) : (
                    <p className="py-6 text-center text-sm text-muted-foreground">
                      No active alerts
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </header>

        <main className="min-h-0 min-w-0 flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold tracking-tight">
              {activeItem?.label ?? "Operations"}
            </h1>

            <p className="mt-1 text-sm text-muted-foreground">
              {activePage === "operations" &&
                "Monitor campus transport operations and network status."}

              {activePage === "recovery-planner" &&
                "Plan recovery scenarios and review proposed schedules."}

              {activePage === "performance-lab" &&
                "Compare baseline performance with optimized results."}
            </p>
          </div>

          {activePage === "operations" ? (
            <OperationsPage />
          ) : activePage === "recovery-planner" ? (
            <RecoveryPlanner
              onViewPerformance={() =>
                handleNavigate("performance-lab")
              }
            />
          ) : (
            <PerformanceLab />
          )}
        </main>
      </div>
    </div>
  );
}
