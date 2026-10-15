
import { CheckCircle2, LoaderCircle } from "lucide-react";

import type { RunStage } from "../../types/recoveryPlanner";

const optimizationStages = [
  {
    id: "loading-scenario",
    title: "Load scenario",
    description: "Preparing the selected scenario and initial conditions.",
  },
  {
    id: "optimizing",
    title: "Optimize schedule",
    description: "Generating a candidate transportation plan.",
  },
  {
    id: "validating",
    title: "Validate constraints",
    description: "Checking the proposed plan against operational constraints.",
  },
  {
    id: "evaluating",
    title: "Evaluate plan",
    description: "Calculating performance metrics and comparing plans.",
  },
] as const;

interface OptimizationProgressProps {
  stage: RunStage;
}

export default function OptimizationProgress({
  stage,
}: OptimizationProgressProps) {
  const currentIndex = optimizationStages.findIndex(
    (item) => item.id === stage,
  );

  const safeIndex = Math.max(currentIndex, 0);

  return (
    <div
      className="mt-6 rounded-xl border border-border p-4 sm:p-5"
      role="status"
      aria-live="polite"
    >
      <h3 className="font-semibold text-foreground">
        Running optimization
      </h3>

      <p className="mt-1 text-sm text-secondary">
        Processing the selected scenario and preparing the recovery plan.
      </p>

      <div className="mt-5 space-y-4">
        {optimizationStages.map((item, index) => {
          const complete = index < safeIndex;
          const current = index === safeIndex;

          return (
            <div key={item.id} className="flex items-start gap-3">
              {complete ? (
                <CheckCircle2
                  size={20}
                  className="shrink-0 text-emerald-600"
                />
              ) : current ? (
                <LoaderCircle
                  size={20}
                  className="shrink-0 animate-spin text-primary"
                />
              ) : (
                <span className="flex size-5 shrink-0 items-center justify-center rounded-full border border-border text-xs text-secondary">
                  {index + 1}
                </span>
              )}

              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground">
                  {item.title}

                  {complete && (
                    <span className="ml-2 text-xs text-emerald-700">
                      Complete
                    </span>
                  )}

                  {current && (
                    <span className="ml-2 text-xs text-primary">
                      In progress
                    </span>
                  )}
                </p>

                <p className="mt-1 text-sm leading-5 text-secondary">
                  {item.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{
            width: `${((safeIndex + 1) / optimizationStages.length) * 100}%`,
          }}
        />
      </div>

      <p className="mt-2 text-right text-xs text-secondary">
        Step {safeIndex + 1} of {optimizationStages.length}
      </p>
    </div>
  );
}
