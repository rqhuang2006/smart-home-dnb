import type { AlertState } from "../types";

type Props = {
  alert: AlertState;
  onClose?: () => void;
};

export function ApiErrorAlert({ alert, onClose }: Props) {
  if (!alert) return null;

  return (
    <div className={`alert ${alert.type}`}>
      <span>{alert.message}</span>
      {onClose ? (
        <button className="icon-button" type="button" onClick={onClose} aria-label="关闭提示">
          x
        </button>
      ) : null}
    </div>
  );
}
