import type { Rental } from "../api/types";

type RentalListProps = {
  rentals: Rental[];
  onReturn: (rentalId: string) => void;
  busy: boolean;
};

function formatOverdue(seconds: number): string {
  if (seconds <= 0) return "on time";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const parts: string[] = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  parts.push(`${Math.floor(seconds % 60)}s`);
  return `${parts.join(" ")} late`;
}

function formatDue(due: string): string {
  return new Date(due).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function RentalList({ rentals, onReturn, busy }: RentalListProps) {
  if (rentals.length === 0) return <p className="empty">No rentals yet.</p>;

  return (
    <ul className="list">
      {rentals.map((rental) => (
        <li key={rental.rental_id} className="row">
          <div>
            <strong>{rental.title}</strong>
            <span className="meta">
              {rental.user_id} · due {formatDue(rental.due_at)} ·{" "}
              {formatOverdue(rental.overdue_seconds)}
            </span>
          </div>
          <div className="row-end">
            <span className={`badge badge-${rental.status}`}>{rental.status}</span>
            {rental.returned_at === null ? (
              <button type="button" disabled={busy} onClick={() => onReturn(rental.rental_id)}>
                Return
              </button>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}
