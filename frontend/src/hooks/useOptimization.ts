import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "../services/http";
import { runOptimization } from "../services/optimization";
import type { OptimizeResult } from "../services/optimization";
import type { RunStage } from "../types/recoveryPlanner";

const RUNNING_STAGES: RunStage[] = [
  "loading-scenario",
  "optimizing",
  "validating",
  "evaluating",
];

export interface OptimizationState {
  stage: RunStage;
  result: OptimizeResult | null;
  error: string | null;
  isRunning: boolean;
  run: (scenarioId: string) => Promise<void>;
  reset: () => void;
}

export function useOptimization(): OptimizationState {
  const [stage, setStage] = useState<RunStage>("idle");
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const controllerRef = useRef<AbortController | null>(null);
  const mountTimerRef = useRef<number | null>(null);

  const isRunning = RUNNING_STAGES.includes(stage);

  useEffect(() => {
    return () => {
      controllerRef.current?.abort();
      if (mountTimerRef.current !== null) {
        window.clearTimeout(mountTimerRef.current);
      }
    };
  }, []);

  const reset = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    if (mountTimerRef.current !== null) {
      window.clearTimeout(mountTimerRef.current);
      mountTimerRef.current = null;
    }
    setResult(null);
    setError(null);
    setStage("idle");
  }, []);

  const run = useCallback(async (scenarioId: string) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    setResult(null);
    setError(null);
    setStage("loading-scenario");

    // The backend performs optimize -> validate -> simulate -> evaluate inside a
    // single request. The stage indicator is presentational; the returned plan,
    // validation and metrics are always computed server-side.
    mountTimerRef.current = window.setTimeout(() => {
      setStage("optimizing");
    }, 250);

    try {
      const data = await runOptimization(scenarioId, controller.signal);
      if (controller.signal.aborted) return;

      if (mountTimerRef.current !== null) {
        window.clearTimeout(mountTimerRef.current);
        mountTimerRef.current = null;
      }

      setStage("validating");
      setStage("evaluating");
      setResult(data);
      setStage("completed");
    } catch (err: unknown) {
      if (controller.signal.aborted) return;

      if (mountTimerRef.current !== null) {
        window.clearTimeout(mountTimerRef.current);
        mountTimerRef.current = null;
      }

      setError(
        err instanceof ApiError
          ? err.message
          : "An unexpected error occurred while optimizing the scenario.",
      );
      setStage("error");
    }
  }, []);

  return { stage, result, error, isRunning, run, reset };
}
