import { useCallback, useEffect, useState } from "react";

import { getOperationsOverview } from "../api/operation";
import type { OperationsData } from "../types/operations";

export function useOperationsOverview() {
  const [data, setData] = useState<OperationsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const overview = await getOperationsOverview();
      setData(overview);
    } catch (error: unknown) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load operations overview.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchOverview();
  }, [fetchOverview]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchOverview,
  };
}
