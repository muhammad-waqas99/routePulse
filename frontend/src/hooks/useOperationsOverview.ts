import { useCallback, useEffect, useState } from "react";

import { getOperationsOverview } from "../api/operation";
import type { OperationsData } from "../types/operations";

export function useOperationsOverview() {
  const [data, setData] = useState<OperationsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOverview = useCallback(() => getOperationsOverview(), []);

  const fetchOverview = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const overview = await loadOverview();
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
  }, [loadOverview]);

  useEffect(() => {
    let active = true;
    void loadOverview()
      .then((overview) => { if (active) setData(overview); })
      .catch((error: unknown) => {
        if (active) setError(error instanceof Error ? error.message : "Failed to load operations overview.");
      })
      .finally(() => { if (active) setIsLoading(false); });
    return () => { active = false; };
  }, [loadOverview]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchOverview,
  };
}
