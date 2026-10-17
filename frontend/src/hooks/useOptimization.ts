import { useState } from "react";

import { runOptimization } from "../api/optimization";

import type { OptimizationResult } from "../types/optimization";
import type { RunStage } from "../types/recoveryPlanner";

export function useOptimization() {
  const [stage, setStage] = useState<RunStage>("idle");
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isRunning =
    stage === "loading-scenario" ||
    stage === "optimizing" ||
    stage === "validating" ||
    stage === "evaluating";

  async function run(scenarioId: string) {
    if (isRunning || !scenarioId) return;

    setResult(null);
    setError(null);
    setStage("optimizing");

    try {
      const data = await runOptimization(scenarioId);

      setResult(data);
      setStage("completed");
    } catch (error: unknown) {
      const message =
        error instanceof Error
          ? error.message
          : "Optimization failed. Please try again.";

      setError(message);
      setStage("idle");
    }
  }

  function reset() {
    if (isRunning) return;

    setResult(null);
    setError(null);
    setStage("idle");
  }

  return {
    stage,
    result,
    error,
    isRunning,
    run,
    reset,
  };
}
