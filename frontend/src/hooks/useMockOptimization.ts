
import { useEffect, useState } from "react";
import { recoveryPlannerMockResult } from "../mocks/recoveryPlanner";
import type {
  RecoveryPlanResult,
  RunStage,
} from "../types/recoveryPlanner";

export const optimizationStages = [
  {
    id: "loading-scenario",
    title: "Load scenario",
    description: "Preparing network and initial conditions.",
  },
  {
    id: "optimizing",
    title: "Optimize schedule",
    description: "Generating a candidate transportation plan.",
  },
  {
    id: "validating",
    title: "Validate constraints",
    description: "Checking operational constraints.",
  },
  {
    id: "evaluating",
    title: "Evaluate plan",
    description: "Calculating simulated evaluation metrics.",
  },
] as const;

export function useMockOptimization() {
  const [stage, setStage] = useState<RunStage>("idle");
  const [result, setResult] = useState<RecoveryPlanResult | null>(
    null,
  );

  const isRunning = optimizationStages.some(
    (item) => item.id === stage,
  );

  useEffect(() => {
    if (!isRunning) return;

    const timer = window.setTimeout(() => {
      switch (stage) {
        case "loading-scenario":
          setStage("optimizing");
          break;
        case "optimizing":
          setStage("validating");
          break;
        case "validating":
          setStage("evaluating");
          break;
        case "evaluating":
          setResult(recoveryPlannerMockResult);
          setStage("completed");
          break;
      }
    }, 900);

    return () => window.clearTimeout(timer);
  }, [stage, isRunning]);

  function run() {
    if (isRunning) return;

    setResult(null);
    setStage("loading-scenario");
  }

  function reset() {
    setResult(null);
    setStage("idle");
  }

  return { stage, result, isRunning, run, reset };
}
