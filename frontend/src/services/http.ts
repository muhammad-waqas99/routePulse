import { API_BASE_URL } from "../config/api";

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

interface ApiEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
}

interface ApiErrorBody {
  success?: boolean;
  message?: string;
  error?: string;
}

async function toApiError(response: Response): Promise<ApiError> {
  let message = `Request failed with status ${response.status}.`;
  let code: string | undefined;

  try {
    const body = (await response.json()) as ApiErrorBody;
    if (typeof body?.message === "string" && body.message.length > 0) {
      message = body.message;
    }
    code = body?.error;
  } catch {
    // Response was not JSON; keep the generic status-based message.
  }

  return new ApiError(message, response.status, code);
}

export async function requestJson<T>(
  path: string,
  init: RequestInit = {},
  signal?: AbortSignal,
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError(
      `Unable to reach the RoutePulse API at ${API_BASE_URL}. Is the backend running?`,
      0,
      "network_error",
    );
  }

  if (!response.ok) {
    throw await toApiError(response);
  }

  return (await response.json()) as T;
}

export async function fetchEnvelope<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  const body = await requestJson<ApiEnvelope<T>>(path, { method: "GET" }, signal);
  return body.data;
}
