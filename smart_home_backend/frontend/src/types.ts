export type ApiEnvelope<T> = {
  code: number;
  message: string;
  data: T;
};

export type Person = {
  person_id: number;
  name: string;
  role: string;
  authorized: boolean;
  created_at?: string;
};

export type DeviceStatus = {
  light_on: boolean;
  light_brightness: number;
  fan_on: boolean;
  door_open: boolean;
  window_open: boolean;
  temperature: number | null;
  mode: string;
  raw?: Record<string, unknown>;
};

export type FaceVerifyResult = {
  matched: boolean;
  person_id: number | null;
  name: string | null;
  confidence: number;
  door_allowed: boolean;
  reason: string;
  created_at?: string;
};

export type BoundingBox = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
};

export type DetectionObject = {
  label: string;
  confidence: number;
  bbox: BoundingBox;
};

export type TriggerAction = {
  type?: string;
  action?: string;
  reason?: string;
  targets?: DetectionObject[];
  [key: string]: unknown;
} | null;

export type DetectionRecord = {
  record_id: number;
  image_id: number | null;
  image_path: string;
  objects: DetectionObject[];
  trigger_action: TriggerAction;
  created_at: string;
};

export type SensorRecord = {
  id: number;
  temperature: number | null;
  light_brightness: number | null;
  door_open: boolean;
  window_open: boolean;
  fan_on: boolean;
  type: string;
  created_at: string;
};

export type TelemetryResult = {
  record_id: number;
  fan_on: boolean;
  auto_fan_on: boolean;
  device_status: DeviceStatus;
};

export type DashboardSummary = {
  device_status: DeviceStatus;
  latest_face_access: FaceVerifyResult | null;
  latest_detection: DetectionRecord | null;
};

export type AlertState = {
  type: "success" | "error" | "info";
  message: string;
} | null;
