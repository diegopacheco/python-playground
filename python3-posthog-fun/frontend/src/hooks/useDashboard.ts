import { useCallback } from "react";

import { api } from "../api/client";
import { usePolling } from "./usePolling";

export function useDashboard(intervalMs: number) {
  const health = usePolling(api.health, intervalMs);
  const dvds = usePolling(api.dvds, intervalMs);
  const rentals = usePolling(api.rentals, intervalMs);
  const topRented = usePolling(api.topRented, intervalMs);
  const neverRented = usePolling(api.neverRented, intervalMs);
  const events = usePolling(api.events, intervalMs);

  const refreshAll = useCallback(async () => {
    await Promise.all([
      dvds.refresh(),
      rentals.refresh(),
      topRented.refresh(),
      neverRented.refresh(),
      events.refresh(),
    ]);
  }, [dvds.refresh, rentals.refresh, topRented.refresh, neverRented.refresh, events.refresh]);

  return { health, dvds, rentals, topRented, neverRented, events, refreshAll };
}
