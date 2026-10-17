import { Clock3, ShieldCheck, TrendingUp, BusFront } from "lucide-react";
import type { Scenario } from "../../types/scenarios";

interface ScenarioDetailsProps {
  scenario: Scenario;
}

const categoryStyles: Record<Scenario["category"], string> = {
  Normal: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  "Stress Test": "bg-amber-50 text-amber-700 ring-amber-600/20",
  Disruption: "bg-red-50 text-red-700 ring-red-600/20",
};


export default function ScenarioDetails({
  scenario,
}: ScenarioDetailsProps) {
  const details = [
    {
      label: "Stops affected",
      value: Object.keys(scenario.demandMultipliers).length
        ? `${Object.keys(scenario.demandMultipliers).length} stops`
        : "None",
      icon: TrendingUp,
    },
    {
      label: "Vehicles unavailable",
      value: scenario.unavailableVehicleIds.length
        ? String(scenario.unavailableVehicleIds.length)
        : "None",
      icon: BusFront,
    },
    {
      label: "Routes slowed",
      value: Object.keys(scenario.travelTimeMultipliers).length
        ? `${Object.keys(scenario.travelTimeMultipliers).length} routes`
        : "None",
      icon: Clock3,
    },
    {
      label: "Duration",
      value: `${scenario.evaluationHorizonMin} min`,
      icon: Clock3,
    },
    ...Object.entries(scenario.demandMultipliers).slice(0, 3).map(([stopId, multiplier]) => ({
      label: `Demand · ${stopId}`,
      value: `${multiplier > 1 ? "+" : ""}${Math.round((multiplier - 1) * 100)}%`,
      icon: TrendingUp,
    })),
    ...Object.entries(scenario.travelTimeMultipliers).slice(0, 3).map(([routeId, multiplier]) => ({
      label: `Travel time · ${routeId}`,
      value: `${multiplier.toFixed(2)}×`,
      icon: Clock3,
    })),
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
        {details.filter((detail) => detail.value !== "None").map((detail) => {
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

    </section>
  );
}
