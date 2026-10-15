import { fetchOperationsOverview } from "../services/operations";
import { useAsync } from "./useAsync";

export function useOperationsOverview() {
  return useAsync(fetchOperationsOverview);
}
