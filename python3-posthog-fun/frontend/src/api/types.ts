export type Dvd = {
  dvd_id: string;
  title: string;
  year: number;
  genre: string;
  available: boolean;
};

export type RentalStatus = "active" | "returned" | "overdue";

export type Rental = {
  rental_id: string;
  dvd_id: string;
  title: string;
  user_id: string;
  rented_at: string;
  due_at: string;
  status: RentalStatus;
  returned_at: string | null;
  overdue_seconds: number;
};

export type RankedDvd = {
  rank: number;
  dvd_id: string;
  title: string;
  genre: string;
  rentals: number;
};

export type EmittedEvent = {
  event: string;
  distinct_id: string;
  properties: Record<string, unknown>;
  at: string;
};

export type Health = {
  status: string;
  posthog_enabled: boolean;
  rental_period_seconds: number;
  rollup_interval_minutes: number;
  deadline_scan_seconds: number;
};
