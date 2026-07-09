import type { LucideIcon } from "lucide-react";

type Props = {
  title: string;
  value: string;
  detail?: string;
  tone?: "normal" | "good" | "warn" | "danger";
  icon: LucideIcon;
};

export function StatusCard({ title, value, detail, tone = "normal", icon: Icon }: Props) {
  return (
    <section className={`status-card ${tone}`}>
      <div className="status-icon">
        <Icon size={22} />
      </div>
      <div>
        <p>{title}</p>
        <strong>{value}</strong>
        {detail ? <span>{detail}</span> : null}
      </div>
    </section>
  );
}
