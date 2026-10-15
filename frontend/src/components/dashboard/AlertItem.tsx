import { AlertTriangle, Info, CircleAlert } from "lucide-react";
import type { TransportAlert } from "../../types/operations";

interface AlertItemProps {
  alert: TransportAlert;
}

const severityStyles = {
  info: {
    icon: Info,
    className: "bg-sky-50 text-sky-700",
    label: "Info",
  },
  warning: {
    icon: AlertTriangle,
    className: "bg-amber-50 text-amber-700",
    label: "Warning",
  },
  critical: {
    icon: CircleAlert,
    className: "bg-red-50 text-red-700",
    label: "Critical",
  },
};

export default function AlertItem({ alert }: AlertItemProps) {
  const severity = severityStyles[alert.severity];
  const Icon = severity.icon;

  return (
    <article className="flex items-start gap-3 rounded-lg border border-border p-4">
      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${severity.className}`}>
        <Icon size={18} aria-hidden="true" />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-foreground">
            {alert.title}
          </h3>

          <span className={`rounded-full px-2 py-1 text-xs font-medium ${severity.className}`}>
            {severity.label}
          </span>
        </div>

        <p className="mt-1 text-sm text-muted-foreground">
          {alert.description}
        </p>
      </div>
    </article>
  );
}
