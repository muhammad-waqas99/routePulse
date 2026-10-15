import {
  Clock3,
  ShieldCheck,
  TrendingUp,
  BusFront,
  RotateCcw,
} from "lucide-react";
import type { Scenario } from "../../types/scenarios";

interface ScenarioDetailsProps {
  scenario: Scenario;
}

const categoryStyles = {
  Normal: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  "Stress Test": "bg-amber-50 text-amber-700 ring-amber-600/20",
  Disruption: "bg-red-50 text-red-700 ring-red-600/20",
};


export default function ScenarioDetails({
  scenario,
}: ScenarioDetailsProps) {
  const details = [
    {
      label: "Demand Multiplier",
      value: `+${scenario.demandMultiplierPercent}%`,
      icon: TrendingUp,
    },
    {
      label: "Available Vehicles",
      value: String(scenario.availableVehicles),
      icon: BusFront,
    },
    {
      label: "Affected Period",
      value: scenario.affectedPeriod,
      icon: Clock3,
    },
    {
      label: "Evaluation Horizon",
      value: `${scenario.evaluationHorizonMin} min`,
      icon: RotateCcw,
    },
  ];

  return (
    <section className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-sm text-secondary">Selected Scenario</p>
          <h2 className="mt-1 text-xl font-semibold text-foreground">
            {scenario.name}
          </h2>
          <p className="mt-2 text-sm text-secondary">
            {scenario.description}
          </p>
        </div>


<span
  className={`inline-flex w-fit shrink-0 items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium ring-1 ring-inset ${
    categoryStyles[scenario.category]
  }`}
>
  <ShieldCheck size={15} />
  {scenario.category}
</span>

      </div>

      <div className="mt-6 grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {details.map((detail) => {
          const Icon = detail.icon;

          return (
            <div
              key={detail.label}
              className="min-w-0 rounded-lg border border-border p-4"
            >
              <div className="flex items-center gap-2 text-secondary">
                <Icon size={16} />
                <span className="text-xs">{detail.label}</span>
              </div>

              <p className="mt-3 wrap-break-words text-lg font-semibold text-foreground">
                {detail.value}
              </p>
            </div>
          );
        })}
      </div>

      <p className="mt-4 text-xs leading-5 text-secondary">
        Scenario configuration provided by the backend.
      </p>
    </section>
  );
}
