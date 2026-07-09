import type {
  ApiEnvelope,
  DashboardSummary,
  DetectionRecord,
  DeviceStatus,
  FaceVerifyResult,
  Person,
  SensorRecord,
  TelemetryResult,
} from "./types";

export const API_BASE = "http://127.0.0.1:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);
  const payload = (await response.json()) as ApiEnvelope<T | null>;
  if (!response.ok || payload.code !== 0) {
    throw new Error(payload.message || `Request failed: ${response.status}`);
  }
  return payload.data as T;
}

export const api = {
  dashboard: () => request<DashboardSummary>("/dashboard/summary"),
  persons: () => request<Person[]>("/persons?authorized=true"),
  createPerson: (formData: FormData) =>
    request<Person>("/persons", { method: "POST", body: formData }),
  deletePerson: (personId: number) =>
    request<{ person_id: number; name: string; deleted: boolean }>(`/persons/${personId}`, { method: "DELETE" }),
  verifyFace: (formData: FormData) =>
    request<FaceVerifyResult>("/face/verify", { method: "POST", body: formData }),
  controlDoor: (action: "open" | "close", reason = "frontend control") =>
    request<{ door_open: boolean; action: string; mode: string; command_id: number }>("/devices/door/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, reason, duration_seconds: 3 }),
    }),
  uploadImage: (formData: FormData) =>
    request<{ image_id: number; image_path: string; source: string }>("/images", { method: "POST", body: formData }),
  detectImage: (formData: FormData) =>
    request<DetectionRecord>("/vision/detect", { method: "POST", body: formData }),
  detectionRecords: () => request<DetectionRecord[]>("/vision/records?limit=20"),
  status: () => request<DeviceStatus>("/devices/status"),
  controlLight: (on: boolean, brightness: number) =>
    request<{ device: string; light_on: boolean; brightness: number; mode: string; command_id: number }>(
      "/devices/light/control",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ on, brightness, source: "frontend" }),
      },
    ),
  controlFan: (on: boolean, temperature?: number) =>
    request<{ device: string; fan_on: boolean; mode: string; command_id: number }>("/devices/fan/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ on, source: "frontend", temperature }),
    }),
  telemetry: (payload: {
    temperature?: number;
    light_brightness?: number;
    door_open?: boolean;
    window_open?: boolean;
    fan_on?: boolean;
    type?: string;
  }) =>
    request<TelemetryResult>("/iot/telemetry", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  sensorHistory: (type = "all") => request<SensorRecord[]>(`/sensors/history?type=${type}&limit=100`),
};
