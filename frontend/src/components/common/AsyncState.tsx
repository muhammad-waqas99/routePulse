import { AlertTriangle, LoaderCircle, RefreshCw } from "lucide-react";

interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = "Loading data..." }: LoadingStateProps) {
  return (
    <section
      role="status"
      aria-live="polite"
      className="flex min-h-52 flex-col items-center justify-center rounded-xl border border-border bg-white p-6 text-center"
    >
      <LoaderCircle size={26} className="animate-spin text-primary" />
      <p className="mt-3 text-sm font-medium text-foreground">{label}</p>
      <p className="mt-1 text-xs text-secondary">
        Fetching the latest data from the backend.
      </p>
    </section>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <section
      role="alert"
      className="flex min-h-52 flex-col items-center justify-center rounded-xl border border-red-200 bg-white p-6 text-center"
    >
      <div className="rounded-full bg-red-50 p-3 text-red-600">
        <AlertTriangle size={22} />
      </div>

      <h3 className="mt-4 font-semibold text-foreground">
        Unable to load data
      </h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-secondary">
        {message}
      </p>

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-5 inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-foreground transition hover:bg-slate-50"
        >
          <RefreshCw size={16} />
          Retry
        </button>
      )}
    </section>
  );
}
