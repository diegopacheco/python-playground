import type { RankedDvd } from "../api/types";

type LeaderboardProps = {
  entries: RankedDvd[];
  emptyLabel: string;
};

export function Leaderboard({ entries, emptyLabel }: LeaderboardProps) {
  if (entries.length === 0) return <p className="empty">{emptyLabel}</p>;

  return (
    <ol className="list">
      {entries.map((entry) => (
        <li key={entry.dvd_id} className="row">
          <div>
            <strong>
              {entry.rank}. {entry.title}
            </strong>
            <span className="meta">{entry.genre}</span>
          </div>
          <span className="count">{entry.rentals}</span>
        </li>
      ))}
    </ol>
  );
}
