import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Camera,
  CheckCircle2,
  DoorOpen,
  Fan,
  Gauge,
  Home,
  Lightbulb,
  LockKeyhole,
  ShieldCheck,
  Thermometer,
  UploadCloud,
  Users,
  Waves,
  XCircle,
} from "lucide-react";
import { api, API_BASE } from "./api";
import { ApiErrorAlert } from "./components/ApiErrorAlert";
import { DeviceCard } from "./components/DeviceCard";
import { ResultPanel } from "./components/ResultPanel";
import { StatusCard } from "./components/StatusCard";
import { UploadBox } from "./components/UploadBox";
import type {
  AlertState,
  DashboardSummary,
  DetectionObject,
  DetectionRecord,
  DeviceStatus,
  FaceVerifyResult,
  Person,
  SensorRecord,
} from "./types";

type PageKey = "dashboard" | "persons" | "face" | "vision" | "devices";

const defaultStatus: DeviceStatus = {
  light_on: false,
  light_brightness: 0,
  fan_on: false,
  door_open: false,
  window_open: false,
  temperature: null,
  mode: "mock",
};

const navItems: Array<{ key: PageKey; label: string; icon: LucideIcon }> = [
  { key: "dashboard", label: "Dashboard", icon: Home },
  { key: "persons", label: "授权人员", icon: Users },
  { key: "face", label: "人脸门禁", icon: LockKeyhole },
  { key: "vision", label: "YOLO 识别", icon: Camera },
  { key: "devices", label: "设备与历史", icon: Gauge },
];

function percent(value?: number | null) {
  return `${Math.round((value ?? 0) * 100)}%`;
}

function timeText(value?: string) {
  if (!value) return "暂无时间";
  return new Date(value).toLocaleString();
}

function boolText(value: boolean, on = "开启", off = "关闭") {
  return value ? on : off;
}

function objectSummary(objects: DetectionObject[] = []) {
  if (objects.length === 0) return "未检测到目标";
  return objects.map((item) => `${item.label} ${percent(item.confidence)}`).join(" / ");
}

function actionText(record?: DetectionRecord | null) {
  const action = record?.trigger_action;
  if (!action) return "未触发动作";
  if (action.action === "turn_on_light") return "已触发开灯";
  if (action.action === "notify") return "已触发视觉告警";
  return String(action.reason || action.action || "已触发动作");
}

export default function App() {
  const [page, setPage] = useState<PageKey>("dashboard");
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [status, setStatus] = useState<DeviceStatus>(defaultStatus);
  const [persons, setPersons] = useState<Person[]>([]);
  const [faceResult, setFaceResult] = useState<FaceVerifyResult | null>(null);
  const [detection, setDetection] = useState<DetectionRecord | null>(null);
  const [records, setRecords] = useState<DetectionRecord[]>([]);
  const [history, setHistory] = useState<SensorRecord[]>([]);
  const [alert, setAlert] = useState<AlertState>(null);
  const [loading, setLoading] = useState(false);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [summary, personList, deviceStatus, detectionRecords, sensorHistory] = await Promise.all([
        api.dashboard(),
        api.persons(),
        api.status(),
        api.detectionRecords(),
        api.sensorHistory(),
      ]);
      setDashboard(summary);
      setStatus(summary.device_status ?? deviceStatus);
      setPersons(personList);
      setRecords(detectionRecords);
      setHistory(sensorHistory);
      setAlert({ type: "success", message: "系统数据已刷新" });
    } catch (error) {
      setAlert({ type: "error", message: error instanceof Error ? error.message : "系统数据刷新失败" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const healthTone = useMemo(() => {
    if ((status.temperature ?? 0) >= 30) return "danger";
    if (status.door_open || status.window_open) return "warn";
    return "good";
  }, [status]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Home size={24} /></div>
          <div>
            <strong>Smart Home DNB</strong>
            <span>Design and Build Console</span>
          </div>
        </div>

        <nav>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button className={page === item.key ? "active" : ""} key={item.key} type="button" onClick={() => setPage(item.key)}>
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="api-card">
          <span>API Base</span>
          <code>{API_BASE}</code>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div>
            <p className="eyebrow">小学期智能家居项目</p>
            <h1>智能家居 Web 管理界面</h1>
          </div>
          <div className="top-actions">
            <span className={`system-pill ${healthTone}`}>{loading ? "同步中" : "系统运行正常"}</span>
            <button type="button" onClick={() => void loadAll()} disabled={loading}>
              <Activity size={18} />
              刷新数据
            </button>
          </div>
        </header>

        <ApiErrorAlert alert={alert} onClose={() => setAlert(null)} />

        {page === "dashboard" ? <DashboardPage summary={dashboard} status={status} /> : null}
        {page === "persons" ? <PersonsPage persons={persons} setPersons={setPersons} setDashboard={setDashboard} setAlert={setAlert} /> : null}
        {page === "face" ? <FacePage result={faceResult} setResult={setFaceResult} setDashboard={setDashboard} setStatus={setStatus} setAlert={setAlert} /> : null}
        {page === "vision" ? <VisionPage detection={detection} setDetection={setDetection} records={records} setRecords={setRecords} setDashboard={setDashboard} setAlert={setAlert} /> : null}
        {page === "devices" ? <DevicesPage status={status} setStatus={setStatus} history={history} setHistory={setHistory} setAlert={setAlert} /> : null}
      </main>
    </div>
  );
}

function DashboardPage({ summary, status }: { summary: DashboardSummary | null; status: DeviceStatus }) {
  const latestFace = summary?.latest_face_access;
  const latestDetection = summary?.latest_detection;
  const temp = status.temperature;

  return (
    <div className="page-grid">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Live Overview</p>
          <h2>家庭状态一屏总览</h2>
          <p>当前系统处于 {status.mode} 模式。温度、门窗、人脸门禁和 YOLO 检测记录会从 <code>/dashboard/summary</code> 汇总展示。</p>
        </div>
        <div className={`hero-state ${(temp ?? 0) >= 30 ? "hot" : ""}`}>
          <Thermometer size={36} />
          <strong>{temp == null ? "--" : `${temp}°C`}</strong>
          <span>{(temp ?? 0) >= 30 ? "温度偏高，建议开启风扇" : "环境温度正常"}</span>
        </div>
      </section>

      <div className="status-grid">
        <StatusCard title="当前温度" value={temp == null ? "--" : `${temp}°C`} detail={(temp ?? 0) >= 30 ? "高温提醒" : "正常"} tone={(temp ?? 0) >= 30 ? "danger" : "good"} icon={Thermometer} />
        <StatusCard title="风扇状态" value={boolText(status.fan_on)} detail={status.fan_on ? "空气循环中" : "待机"} tone={status.fan_on ? "good" : "normal"} icon={Fan} />
        <StatusCard title="灯光状态" value={boolText(status.light_on)} detail={`亮度 ${status.light_brightness}%`} tone={status.light_on ? "good" : "normal"} icon={Lightbulb} />
        <StatusCard title="门窗状态" value={status.door_open || status.window_open ? "有开启" : "已关闭"} detail={`门 ${boolText(status.door_open, "开", "关")} / 窗 ${boolText(status.window_open, "开", "关")}`} tone={status.door_open || status.window_open ? "warn" : "good"} icon={DoorOpen} />
      </div>

      <section className="split-grid">
        <ResultPanel title="最近一次人脸识别">
          {latestFace ? (
            <div className={`decision ${latestFace.door_allowed ? "allow" : "deny"}`}>
              {latestFace.door_allowed ? <CheckCircle2 size={34} /> : <XCircle size={34} />}
              <div>
                <strong>{latestFace.door_allowed ? "允许进入" : "拒绝进入"}</strong>
                <span>{latestFace.name || "未知人员"} / 置信度 {percent(latestFace.confidence)}</span>
                <small>{latestFace.reason}，{timeText(latestFace.created_at)}</small>
              </div>
            </div>
          ) : <EmptyState text="暂无人脸识别记录" />}
        </ResultPanel>

        <ResultPanel title="最近一次 YOLO 检测">
          {latestDetection ? (
            <div className="record-card">
              <strong>{objectSummary(latestDetection.objects)}</strong>
              <span>{actionText(latestDetection)}</span>
              <small>{timeText(latestDetection.created_at)}</small>
            </div>
          ) : <EmptyState text="暂无 YOLO 检测记录" />}
        </ResultPanel>
      </section>
    </div>
  );
}

function PersonsPage({ persons, setPersons, setDashboard, setAlert }: { persons: Person[]; setPersons: (persons: Person[]) => void; setDashboard: (summary: DashboardSummary) => void; setAlert: (alert: AlertState) => void }) {
  const [name, setName] = useState("");
  const [role, setRole] = useState("resident");
  const [authorized, setAuthorized] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const preview = useObjectUrl(file);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setAlert({ type: "error", message: "请先选择人脸图片" });
      return;
    }
    const form = new FormData();
    form.append("name", name);
    form.append("role", role);
    form.append("authorized", String(authorized));
    form.append("face_image", file);
    try {
      await api.createPerson(form);
      setPersons(await api.persons());
      setDashboard(await api.dashboard());
      setName("");
      setFile(null);
      setAlert({ type: "success", message: "授权人员添加成功" });
    } catch (error) {
      setAlert({ type: "error", message: error instanceof Error ? error.message : "添加人员失败" });
    }
  }

  async function remove(personId: number) {
    try {
      await api.deletePerson(personId);
      setPersons(await api.persons());
      setAlert({ type: "success", message: "人员已删除" });
    } catch (error) {
      setAlert({ type: "error", message: error instanceof Error ? error.message : "删除失败" });
    }
  }

  return (
    <div className="content-grid two">
      <section className="panel">
        <div className="panel-title"><h2>添加授权人员</h2><span>POST /persons</span></div>
        <form className="form-grid" onSubmit={(event) => void submit(event)}>
          <label>姓名<input value={name} onChange={(event) => setName(event.target.value)} required placeholder="例如 zhangsan" /></label>
          <label>角色<input value={role} onChange={(event) => setRole(event.target.value)} placeholder="resident" /></label>
          <label className="switch-row"><span>授权状态</span><input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} /></label>
          <UploadBox label="上传注册人脸 face_image" file={file} preview={preview} onChange={setFile} />
          <button type="submit"><ShieldCheck size={18} />添加授权人员</button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-title"><h2>授权人员列表</h2><button type="button" onClick={() => void api.persons().then(setPersons)}>刷新列表</button></div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>姓名</th><th>角色</th><th>授权</th><th>操作</th></tr></thead>
            <tbody>
              {persons.map((person) => (
                <tr key={person.person_id}>
                  <td>{person.person_id}</td><td>{person.name}</td><td>{person.role}</td><td><span className="state-pill on">{String(person.authorized)}</span></td>
                  <td><button className="danger small" type="button" onClick={() => void remove(person.person_id)}>删除</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function FacePage({ result, setResult, setDashboard, setStatus, setAlert }: { result: FaceVerifyResult | null; setResult: (result: FaceVerifyResult) => void; setDashboard: (summary: DashboardSummary) => void; setStatus: (status: DeviceStatus) => void; setAlert: (alert: AlertState) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const preview = useObjectUrl(file);

  async function verify(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setAlert({ type: "error", message: "请选择待验证人脸图片" });
      return;
    }
    const form = new FormData();
    form.append("face_image", file);
    try {
      const data = await api.verifyFace(form);
      setResult(data);
      setDashboard(await api.dashboard());
      setAlert({ type: data.door_allowed ? "success" : "error", message: data.door_allowed ? "识别成功，允许进入" : "识别失败，拒绝进入" });
    } catch (error) {
      setAlert({ type: "error", message: error instanceof Error ? error.message : "人脸验证失败" });
    }
  }

  async function openDoor() {
    try {
      await api.controlDoor("open", "face verification allowed");
      setStatus(await api.status());
      setAlert({ type: "success", message: "已发送开门指令" });
    } catch (error) {
      setAlert({ type: "error", message: error instanceof Error ? error.message : "开门失败" });
    }
  }

  return (
    <div className="content-grid two">
      <section className="panel">
        <div className="panel-title"><h2>人脸识别门禁</h2><span>POST /face/verify</span></div>
        <form className="form-grid" onSubmit={(event) => void verify(event)}>
          <UploadBox label="上传验证图片 face_image" file={file} preview={preview} onChange={setFile} />
          <button type="submit"><UploadCloud size={18} />开始验证</button>
        </form>
      </section>

      <ResultPanel title="识别结果">
        {result ? (
          <div className={`face-result ${result.door_allowed ? "allow" : "deny"}`}>
            <div className="decision-line">
              {result.door_allowed ? <CheckCircle2 size={42} /> : <XCircle size={42} />}
              <div><strong>{result.door_allowed ? "允许进入" : "拒绝进入"}</strong><span>{result.reason}</span></div>
            </div>
            <div className="fact-grid">
              <Metric label="matched" value={String(result.matched)} />
              <Metric label="person_id" value={result.person_id ?? "null"} />
              <Metric label="name" value={result.name ?? "未知"} />
              <Metric label="confidence" value={percent(result.confidence)} />
            </div>
            {result.door_allowed ? <button type="button" onClick={() => void openDoor()}><DoorOpen size={18} />开门</button> : null}
          </div>
        ) : <EmptyState text="上传图片后会显示 matched、person_id、name、confidence、door_allowed、reason" />}
      </ResultPanel>
    </div>
  );
}

function VisionPage({ detection, setDetection, records, setRecords, setDashboard, setAlert }: { detection: DetectionRecord | null; setDetection: (record: DetectionRecord) => void; records: DetectionRecord[]; setRecords: (records: DetectionRecord[]) => void; setDashboard: (summary: DashboardSummary) => void; setAlert: (alert: AlertState) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const preview = useObjectUrl(file);

  async function detect(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setAlert({ type: "error", message: "请选择 YOLO 待识别图片" });
      return;
    }
    const uploadForm = new FormData();
    uploadForm.append("image", file);
    uploadForm.append("source", "frontend");
    try {
      const uploaded = await api.uploadImage(uploadForm);
      const detectForm = new FormData();
      detectForm.append("image_id", String(uploaded.image_id));
      detectForm.append("source", "frontend");
      const data = await api.detectImage(detectForm);
      setDetection(data);
      setRecords(await api.detectionRecords());
      setDashboard(await api.dashboard());
      setAlert({ type: "success", message: `识别完成：${objectSummary(data.objects)}` });
    } catch (error) {
      setAlert({ type: "error", message: error instanceof Error ? error.message : "YOLO 检测失败" });
    }
  }

  return (
    <div className="content-grid two">
      <section className="panel">
        <div className="panel-title"><h2>YOLO 目标识别</h2><span>POST /vision/detect</span></div>
        <form className="form-grid" onSubmit={(event) => void detect(event)}>
          <UploadBox label="上传识别图片 image" file={file} preview={preview} onChange={setFile} />
          <button type="submit"><Camera size={18} />上传并检测</button>
        </form>
        <DetectionVisual preview={preview} objects={detection?.objects ?? []} />
      </section>

      <section className="panel">
        <div className="panel-title"><h2>识别结果</h2><button type="button" onClick={() => void api.detectionRecords().then(setRecords)}>刷新记录</button></div>
        {detection ? <DetectionResult record={detection} /> : <EmptyState text="请选择灭火器或无人机图片进行识别" />}
        <div className="record-list">
          {records.map((record) => (
            <button className="record-row" key={record.record_id} type="button" onClick={() => setDetection(record)}>
              <span>#{record.record_id}</span><strong>{objectSummary(record.objects)}</strong><small>{timeText(record.created_at)}</small>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

function DevicesPage({ status, setStatus, history, setHistory, setAlert }: { status: DeviceStatus; setStatus: (status: DeviceStatus) => void; history: SensorRecord[]; setHistory: (records: SensorRecord[]) => void; setAlert: (alert: AlertState) => void }) {
  const [brightness, setBrightness] = useState(status.light_brightness || 60);
  const [temperature, setTemperature] = useState(26);
  const [windowOpen, setWindowOpen] = useState(status.window_open);
  const [doorOpen, setDoorOpen] = useState(status.door_open);

  useEffect(() => {
    setBrightness(status.light_brightness || 60);
    setWindowOpen(status.window_open);
    setDoorOpen(status.door_open);
  }, [status]);

  async function refreshStatus() {
    setStatus(await api.status());
    setHistory(await api.sensorHistory());
  }

  async function controlLight(on: boolean) {
    try {
      await api.controlLight(on, brightness);
      await refreshStatus();
      setAlert({ type: "success", message: on ? "灯光已开启" : "灯光已关闭" });
    } catch (error) {
      setAlert({ type: "error", message: error instanceof Error ? error.message : "灯光控制失败" });
    }
  }

  async function controlFan(on: boolean) {
    try {
      await api.controlFan(on, temperature);
      await refreshStatus();
      setAlert({ type: "success", message: on ? "风扇已开启" : "风扇已关闭" });
    } catch (error) {
      setAlert({ type: "error", message: error instanceof Error ? error.message : "风扇控制失败" });
    }
  }

  async function sendTelemetry(event: FormEvent) {
    event.preventDefault();
    try {
      const result = await api.telemetry({ temperature, light_brightness: brightness, door_open: doorOpen, window_open: windowOpen, fan_on: status.fan_on, type: "telemetry" });
      setStatus(result.device_status);
      setHistory(await api.sensorHistory());
      setAlert({ type: result.auto_fan_on ? "info" : "success", message: result.auto_fan_on ? "温度超过阈值，系统已自动开启风扇" : "telemetry 已上报" });
    } catch (error) {
      setAlert({ type: "error", message: error instanceof Error ? error.message : "telemetry 上报失败" });
    }
  }

  return (
    <div className="content-grid two">
      <section className="panel">
        <div className="panel-title"><h2>设备控制</h2><button type="button" onClick={() => void refreshStatus()}>刷新状态</button></div>
        <div className="device-stack">
          <DeviceCard title="灯光" description={`当前亮度 ${brightness}%`} active={status.light_on} icon={Lightbulb}>
            <div className="range-head"><span>亮度调节</span><strong>{brightness}%</strong></div>
            <input type="range" min={0} max={100} value={brightness} onChange={(event) => setBrightness(Number(event.target.value))} />
            <small className="range-note">已应用亮度：{status.light_brightness}%</small>
            <div className="button-row"><button type="button" onClick={() => void controlLight(true)}>开灯</button><button className="secondary" type="button" onClick={() => void controlLight(false)}>关灯</button></div>
          </DeviceCard>
          <DeviceCard title="风扇" description="支持手动控制和温度自动触发" active={status.fan_on} icon={Fan}>
            <div className="button-row"><button type="button" onClick={() => void controlFan(true)}>开风扇</button><button className="secondary" type="button" onClick={() => void controlFan(false)}>关风扇</button></div>
          </DeviceCard>
        </div>
      </section>

      <section className="panel">
        <div className="panel-title"><h2>模拟 Telemetry</h2><span>POST /iot/telemetry</span></div>
        {(temperature >= 30 || (status.temperature ?? 0) >= 30) ? <div className="alert danger">温度偏高，答辩演示时可展示自动风扇逻辑。</div> : null}
        <form className="form-grid" onSubmit={(event) => void sendTelemetry(event)}>
          <label>温度<input type="number" value={temperature} onChange={(event) => setTemperature(Number(event.target.value))} /></label>
          <label>灯光亮度<input type="number" min={0} max={100} value={brightness} onChange={(event) => setBrightness(Number(event.target.value))} /></label>
          <label className="switch-row"><span>门状态</span><input type="checkbox" checked={doorOpen} onChange={(event) => setDoorOpen(event.target.checked)} /></label>
          <label className="switch-row"><span>窗状态</span><input type="checkbox" checked={windowOpen} onChange={(event) => setWindowOpen(event.target.checked)} /></label>
          <button type="submit"><Waves size={18} />上报数据</button>
        </form>
      </section>

      <section className="panel full">
        <div className="panel-title"><h2>历史数据</h2><button type="button" onClick={() => void api.sensorHistory().then(setHistory)}>查询历史</button></div>
        <div className="sparkline">
          {history.slice(0, 20).reverse().map((item) => <span key={item.id} style={{ height: `${Math.max(8, ((item.temperature ?? 0) / 40) * 100)}%` }} title={`${item.temperature ?? "--"}°C`} />)}
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>时间</th><th>温度</th><th>亮度</th><th>门</th><th>窗</th><th>风扇</th></tr></thead>
            <tbody>
              {history.map((item) => <tr key={item.id}><td>{timeText(item.created_at)}</td><td>{item.temperature ?? "--"}</td><td>{item.light_brightness ?? "--"}</td><td>{boolText(item.door_open, "开", "关")}</td><td>{boolText(item.window_open, "开", "关")}</td><td>{boolText(item.fan_on)}</td></tr>)}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function DetectionResult({ record }: { record: DetectionRecord }) {
  return (
    <div className="detection-result">
      <div className={`alert ${record.trigger_action ? "info" : "success"}`}>{actionText(record)}</div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>label</th><th>confidence</th><th>bbox</th></tr></thead>
          <tbody>
            {record.objects.map((item, index) => (
              <tr key={`${item.label}-${index}`}><td><span className="object-tag">{item.label}</span></td><td>{percent(item.confidence)}</td><td>{`${item.bbox.x1}, ${item.bbox.y1}, ${item.bbox.x2}, ${item.bbox.y2}`}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DetectionVisual({ preview, objects }: { preview: string | null; objects: DetectionObject[] }) {
  return (
    <div className="visual-box">
      {preview ? <img src={preview} alt="YOLO 图片预览" /> : <div className="upload-placeholder">Detection Preview</div>}
      <div className="visual-overlay">{objects.map((object, index) => <span className="object-tag" key={`${object.label}-${index}`}>{object.label}</span>)}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number | null }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

function EmptyState({ text }: { text: string }) {
  return <div className="empty-state">{text}</div>;
}

function useObjectUrl(file: File | null) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!file) {
      setUrl(null);
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);
  return url;
}
