import type { Dvd } from "../api/types";

type CatalogProps = {
  dvds: Dvd[];
  onRent: (dvdId: string) => void;
  busy: boolean;
};

export function Catalog({ dvds, onRent, busy }: CatalogProps) {
  return (
    <ul className="list">
      {dvds.map((dvd) => (
        <li key={dvd.dvd_id} className="row">
          <div>
            <strong>{dvd.title}</strong>
            <span className="meta">
              {dvd.year} · {dvd.genre}
            </span>
          </div>
          <button type="button" disabled={busy || !dvd.available} onClick={() => onRent(dvd.dvd_id)}>
            {dvd.available ? "Rent" : "Out"}
          </button>
        </li>
      ))}
    </ul>
  );
}
