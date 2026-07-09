import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type Props = {
  title: string;
  description: string;
  active: boolean;
  icon: LucideIcon;
  children?: ReactNode;
};

export function DeviceCard({ title, description, active, icon: Icon, children }: Props) {
  return (
    <section className={`device-card ${active ? "active" : ""}`}>
      <div className="device-head">
        <div className="device-icon">
          <Icon size={22} />
        </div>
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
        <span className={`state-pill ${active ? "on" : "off"}`}>{active ? "运行中" : "关闭"}</span>
      </div>
      {children}
    </section>
  );
}
