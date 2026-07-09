import type { ReactNode } from "react";

type Props = {
  title: string;
  children: ReactNode;
};

export function ResultPanel({ title, children }: Props) {
  return (
    <section className="result-panel">
      <div className="panel-title">
        <h3>{title}</h3>
      </div>
      {children}
    </section>
  );
}
