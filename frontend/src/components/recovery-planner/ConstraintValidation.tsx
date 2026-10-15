import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import type { RecoveryPlanResult } from "../../types/recoveryPlanner";

interface Props {
  result: RecoveryPlanResult;
}

export default function ConstraintValidation({ result }: Props) {
  const noViolations = result.hardViolationCount === 0;

  return (
    <section className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5">
      <div className="flex items-start gap-3">
        {noViolations ? (
          <CheckCircle2 className="mt-0.5 shrink-0 text-emerald-600" size={22} />
        ) : (
          <XCircle className="mt-0.5 shrink-0 text-red-600" size={22} />
        )}

        <div>
          <h3 className="text-lg font-semibold text-foreground">
            Constraint Validation
          </h3>
          <p className="mt-1 text-sm text-secondary">
            The proposed plan is checked against operational constraints.
          </p>
        </div>
      </div>

      <div className="mt-5 rounded-lg border border-border p-4">
        <p className="text-sm text-secondary">Hard Violations</p>
        <p className="mt-1 text-2xl font-semibold text-foreground">
          {result.hardViolationCount}
        </p>
        <p className="mt-1 text-sm text-secondary">
          {noViolations
            ? "All listed constraints passed for the returned plan."
            : "One or more hard constraints were violated."}
        </p>
      </div>

      <div className="mt-4 grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {result.constraints.map((constraint) => (
          <div
            key={constraint.id}
            className="flex min-w-0 items-start gap-3 rounded-lg border border-border p-3"
          >
            {constraint.passed ? (
              <CheckCircle2
                size={18}
                className="mt-0.5 shrink-0 text-emerald-600"
              />
            ) : (
              <AlertTriangle
                size={18}
                className="mt-0.5 shrink-0 text-red-600"
              />
            )}

            <span className="text-sm font-medium text-foreground">
              {constraint.label}
            </span>
            <span
              className={`ml-auto shrink-0 text-xs ${
                constraint.passed ? "text-emerald-700" : "text-red-700"
              }`}
            >
              {constraint.passed ? "Passed" : "Failed"}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
