const rawBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;

export const API_BASE_URL =
  rawBaseUrl && rawBaseUrl.trim().length > 0
    ? rawBaseUrl.replace(/\/+$/, "")
    : "http://localhost:8000";

export const apiEndpoints = {
  health: "/api/health",
  operationsOverview: "/api/operations/overview",
  scenarios: "/api/scenarios",
  optimize: "/api/optimize",
  evaluation: "/api/evaluation",
  evaluationRun: (runId: string) => `/api/evaluation/${encodeURIComponent(runId)}`,
} as const;
