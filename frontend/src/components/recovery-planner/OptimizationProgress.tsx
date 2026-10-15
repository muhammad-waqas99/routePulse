import { CheckCircle2, LoaderCircle } from "lucide-react";
import {
  optimizationStages,
} from "../../hooks/useMockOptimization";
import type { RunStage } from "../../types/recoveryPlanner";

interface OptimizationProgressProps {
  stage: RunStage;
}

export default function OptimizationProgress({
  stage,
}: OptimizationProgressProps) {
  const currentIndex = optimizationStages.findIndex(
    (item) => item.id === stage,
  );

  return (
    <div
      className="mt-6 rounded-xl border border-border p-4 sm:p-5"
      role="status"
      aria-live="polite"
    >
      <h3 className="font-semibold text-foreground">
        Preparing recovery plan
      </h3>
      <p className="mt-1 text-sm text-secondary">
        Processing each stage of the demo.
      </p>

      <div className="mt-5 space-y-4">
        {optimizationStages.map((item, index) => {
          const complete = index < currentIndex;
          const current = index === currentIndex;

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

              <div>
                <p className="text-sm font-medium text-foreground">
                  {item.title}
                  {complete && (
                    <span className="ml-2 text-xs text-emerald-700">
                      Complete
                    </span>
                  )}
                </p>
                <p className="mt-1 text-sm text-secondary">
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
            width: `${((currentIndex + 1) / optimizationStages.length) * 100}%`,
          }}
        />
      </div>

      <p className="mt-2 text-right text-xs text-secondary">
        Step {currentIndex + 1} of {optimizationStages.length}
      </p>
    </div>
  );
}
