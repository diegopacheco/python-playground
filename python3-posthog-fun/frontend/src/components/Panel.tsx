import type { ReactNode } from "react";

type PanelProps = {
  title: string;
  subtitle?: string;
  error?: string | null;
  children: ReactNode;
};

export function Panel({ title, subtitle, error, children }: PanelProps) {
  return (
    <section className="panel">
      <header className="panel-head">
        <h2>{title}</h2>
        {subtitle ? <span className="panel-sub">{subtitle}</span> : null}
      </header>
      {error ? <p className="error">{error}</p> : null}
      {children}
    </section>
  );
}
