import { useCallback, useEffect, useState } from "react";

import { api } from "./api/client";
import { Catalog } from "./components/Catalog";
import { EventFeed } from "./components/EventFeed";
import { Leaderboard } from "./components/Leaderboard";
import { Panel } from "./components/Panel";
import { RentalList } from "./components/RentalList";
import { useDashboard } from "./hooks/useDashboard";

const POLL_MS = 2000;

export function App() {
  const { health, dvds, rentals, topRented, neverRented, events, refreshAll } =
    useDashboard(POLL_MS);
  const [userId, setUserId] = useState("diego");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const run = useCallback(
    async (action: () => Promise<unknown>) => {
      setBusy(true);
      setActionError(null);
      try {
        await action();
        await refreshAll();
      } catch (cause) {
        setActionError(cause instanceof Error ? cause.message : String(cause));
      } finally {
        setBusy(false);
      }
    },
    [refreshAll],
  );

  useEffect(() => {
    if (!userId) return;
    void api.visit(userId).catch(() => undefined);
  }, [userId]);

  const onRent = useCallback(
    (dvdId: string) => void run(() => api.rent(dvdId, userId)),
    [run, userId],
  );
  const onReturn = useCallback(
    (rentalId: string) => void run(() => api.giveBack(rentalId)),
    [run],
  );

  return (
    <main>
      <header className="top">
        <h1>DVD Rental</h1>
        <div className="top-controls">
          <label>
            user
            <input value={userId} onChange={(e) => setUserId(e.target.value)} />
          </label>
          <span className={`badge ${health.data?.posthog_enabled ? "badge-active" : "badge-off"}`}>
            posthog {health.data?.posthog_enabled ? "on" : "off"}
          </span>
        </div>
      </header>

      {actionError ? <p className="error">{actionError}</p> : null}

      <div className="grid">
        <Panel
          title="Catalog"
          subtitle={
            health.data ? `rental period ${health.data.rental_period_seconds}s` : undefined
          }
          error={dvds.error}
        >
          <Catalog dvds={dvds.data ?? []} onRent={onRent} busy={busy} />
        </Panel>

        <Panel title="Rentals" error={rentals.error}>
          <RentalList rentals={rentals.data ?? []} onReturn={onReturn} busy={busy} />
        </Panel>

        <Panel title="Top 5 rented" error={topRented.error}>
          <Leaderboard entries={topRented.data ?? []} emptyLabel="Nothing rented yet." />
        </Panel>

        <Panel title="Top 5 never rented" error={neverRented.error}>
          <Leaderboard entries={neverRented.data ?? []} emptyLabel="Every DVD has been rented." />
        </Panel>

        <Panel
          title="PostHog events"
          subtitle={
            health.data
              ? `rollup every ${health.data.rollup_interval_minutes} min`
              : undefined
          }
          error={events.error}
        >
          <EventFeed events={events.data ?? []} />
        </Panel>
      </div>
    </main>
  );
}
