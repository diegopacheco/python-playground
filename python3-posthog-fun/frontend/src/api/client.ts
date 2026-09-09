import type { Dvd, EmittedEvent, Health, RankedDvd, Rental } from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "content-type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => request<Health>("/health"),
  dvds: () => request<Dvd[]>("/dvds"),
  rentals: () => request<Rental[]>("/rentals"),
  topRented: () => request<RankedDvd[]>("/stats/top-rented"),
  neverRented: () => request<RankedDvd[]>("/stats/never-rented"),
  events: () => request<EmittedEvent[]>("/events"),
  rent: (dvdId: string, userId: string) =>
    request<Rental>("/rentals", {
      method: "POST",
      body: JSON.stringify({ dvd_id: dvdId, user_id: userId }),
    }),
  giveBack: (rentalId: string) =>
    request<Rental>(`/rentals/${rentalId}/return`, { method: "POST" }),
};
