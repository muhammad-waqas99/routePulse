
import { Activity, BusFront, X } from "lucide-react";
import { navigationItems, type PageId } from "../../config/navigation";

interface SidebarProps {
  activePage: PageId;
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (pageId: PageId) => void;
  status: "loading" | "connected" | "unavailable";
}

export default function Sidebar({
  activePage,
  isOpen,
  onClose,
  onNavigate,
  status,
}: SidebarProps) {
  return (
    <>
  
      {isOpen && (
        <button
          type="button"
          aria-label="Close navigation menu"
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden"
        />
      )}

      <aside
        id="app-sidebar"
        aria-label="Main navigation"
        className={`fixed inset-y-0 left-0 z-50 flex w-62 flex-col border-r border-border bg-white transition-transform duration-200 lg:static lg:z-auto lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
      
        <div className="flex h-18 shrink-0 items-center justify-between border-b border-border px-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <BusFront size={22} aria-hidden="true" />
            </div>

            <div>
              <h1 className="text-lg font-semibold tracking-tight text-foreground">
                RoutePulse
              </h1>
              <p className="text-xs text-muted-foreground">
                Campus Transport
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close sidebar"
            className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-slate-100 lg:hidden"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-6">
          <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Workspace
          </p>

          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;

            return (
              <button
                key={item.id}
                type="button"
                aria-current={isActive ? "page" : undefined}
                onClick={() => onNavigate(item.id)}
                className={`flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary-soft text-primary"
                    : "text-slate-600 hover:bg-slate-50 hover:text-foreground"
                }`}
              >
                <Icon size={19} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>


        <div className="shrink-0 border-t border-border p-4">
          <div className={`rounded-lg border p-3 ${status === "connected" ? "border-success-border bg-success-soft" : "border-border bg-slate-50"}`}>
            <div className="flex items-center gap-2">
              <Activity
                size={17}
                className={status === "connected" ? "text-success" : "text-muted-foreground"}
                aria-hidden="true"
              />
              <span className="text-sm font-medium text-foreground">
                System Status
              </span>
            </div>

            <div className="mt-2 flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${status === "connected" ? "bg-success" : status === "loading" ? "bg-amber-500" : "bg-red-500"}`} />
              <span className="text-xs text-muted-foreground">
                {status === "connected" ? "API connected" : status === "loading" ? "Checking API" : "API unavailable"}
              </span>
            </div>
          </div>

          <p className="mt-3 text-center text-xs text-muted-foreground">
            RoutePulse · Campus Operations
          </p>
        </div>
      </aside>
    </>
  );
}
