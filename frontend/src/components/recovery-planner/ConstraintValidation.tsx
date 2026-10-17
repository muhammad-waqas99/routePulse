import { AlertTriangle, CheckCircle2, CircleHelp, XCircle } from "lucide-react";
import type { OptimizationResult } from "../../types/optimization";

interface Props {
  result: OptimizationResult;
}

export default function ConstraintValidation({ result }: Props) {
  const validation = result.validation;
  const constraints = validation.constraints;
  const failedCount = constraints.filter((constraint) => constraint.status === "failed").length;
  const unverifiedCount = validation.unverifiedConstraints.length;
  const passed = validation.valid && validation.hardViolationCount === 0;

  if (!constraints.length && unverifiedCount === 0) return null;

  return (
    <section className="space-y-4 rounded-xl border border-border bg-white p-4 sm:p-5">
      <div className="flex items-start gap-3">
        {passed ? <CheckCircle2 className="mt-0.5 text-emerald-600" size={21} /> : <XCircle className="mt-0.5 text-red-600" size={21} />}
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-foreground">Constraint validation</h3>
          <p className="mt-1 text-sm text-secondary">
            {passed
              ? "All verified hard constraints passed."
              : `${validation.hardViolationCount} hard violation(s); ${unverifiedCount} constraint type(s) could not be verified.`}
          </p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${passed ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"}`}>
          {passed ? "Passed" : "Review"}
        </span>
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        <span className="rounded-full bg-red-50 px-3 py-1.5 text-red-800">{failedCount} failed type(s)</span>
        <span className="rounded-full bg-amber-50 px-3 py-1.5 text-amber-800">{unverifiedCount} unverified type(s)</span>
      </div>

      {constraints.length > 0 && (
        <details className="rounded-lg border border-border">
          <summary className="cursor-pointer p-3 text-sm font-medium text-foreground">Show grouped findings ({constraints.length})</summary>
          <ul className="space-y-2 border-t border-border p-3">
            {constraints.map((constraint) => (
              <li key={constraint.id} className="flex gap-2 rounded bg-slate-50 p-3 text-sm">
                {constraint.status === "unverified" ? <CircleHelp className="mt-0.5 shrink-0 text-amber-600" size={16} /> : constraint.passed ? <CheckCircle2 className="mt-0.5 shrink-0 text-emerald-600" size={16} /> : <AlertTriangle className="mt-0.5 shrink-0 text-red-600" size={16} />}
                <div className="min-w-0">
                  <p className="font-medium text-foreground">{constraint.label} · {constraint.status}</p>
                  {constraint.detail && <p className="mt-1 break-words text-xs text-secondary">{constraint.detail}</p>}
                </div>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
