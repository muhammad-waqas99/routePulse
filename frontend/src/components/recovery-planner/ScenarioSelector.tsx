import { Check } from "lucide-react";
import type { Scenario } from "../../types/scenarios";

interface ScenarioSelectorProps {
  scenarios: Scenario[];
  selectedScenarioId: string;
  disabled?: boolean;
  onSelect: (scenarioId: string) => void;
}

export default function ScenarioSelector({
  scenarios,
  selectedScenarioId,
  disabled = false,
  onSelect,
}: ScenarioSelectorProps) {
  return (
    <section className="min-w-0 space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-foreground">
          Select Scenario
        </h2>
        <p className="mt-1 text-sm text-secondary">
          Choose an operational condition to evaluate.
        </p>
      </div>

      <div className="grid min-w-0 grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {scenarios.map((scenario) => {
          const selected = scenario.id === selectedScenarioId;

          return (
            <button
              key={scenario.id}
              type="button"
              aria-pressed={selected}
              disabled={disabled}
              onClick={() => onSelect(scenario.id)}
              className={`min-w-0 rounded-xl border bg-white p-4 text-left transition sm:p-5 ${
                selected
                  ? "border-primary bg-blue-50/50 ring-1 ring-primary"
                  : "border-border hover:border-slate-300"
              } disabled:cursor-not-allowed disabled:opacity-60`}
            >
              <div className="flex items-start justify-between gap-3">
                <span className="text-xs font-medium uppercase tracking-wide text-secondary">
                  {scenario.category}
                </span>

                <span
                  className={`flex size-6 shrink-0 items-center justify-center rounded-full border ${
                    selected
                      ? "border-primary bg-primary text-white"
                      : "border-border text-transparent"
                  }`}
                >
                  <Check size={14} />
                </span>
              </div>

              <h3 className="mt-4 font-semibold text-foreground">
                {scenario.name}
              </h3>

              <p className="mt-2 text-sm leading-6 text-secondary">
                {scenario.description}
              </p>

              <p
                className={`mt-4 text-sm font-medium ${
                  selected ? "text-primary" : "text-secondary"
                }`}
              >
                {selected ? "Selected scenario" : "Select scenario"}
              </p>
            </button>
          );
        })}
      </div>
    </section>
  );
}
