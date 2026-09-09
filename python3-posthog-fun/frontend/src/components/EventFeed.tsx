import type { EmittedEvent } from "../api/types";

type EventFeedProps = {
  events: EmittedEvent[];
};

export function EventFeed({ events }: EventFeedProps) {
  if (events.length === 0) return <p className="empty">No events emitted yet.</p>;

  return (
    <ul className="feed">
      {events.slice(0, 40).map((event, index) => (
        <li key={`${event.at}-${index}`}>
          <span className={`tag tag-${event.event}`}>{event.event}</span>
          <span className="meta">{new Date(event.at).toLocaleTimeString()}</span>
          <code>{JSON.stringify(event.properties)}</code>
        </li>
      ))}
    </ul>
  );
}
