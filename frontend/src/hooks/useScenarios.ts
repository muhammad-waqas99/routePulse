import { fetchScenarios } from "../services/scenarios";
import { useAsync } from "./useAsync";

export function useScenarios() {
  return useAsync(fetchScenarios);
}
