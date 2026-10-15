import { fetchEvaluationRuns } from "../services/evaluation";
import { useAsync } from "./useAsync";

export function useEvaluationRuns() {
  return useAsync(fetchEvaluationRuns);
}
