const cameraBtn = document.getElementById("cameraBtn");
const uploadBtn = document.getElementById("uploadBtn");
const imageInput = document.getElementById("imageInput");
const refreshHistoryBtn = document.getElementById("refreshHistoryBtn");
const messageBox = document.getElementById("messageBox");

function logMessage(msg) {
  const now = new Date().toLocaleTimeString();
  messageBox.textContent = `[${now}] ${msg}`;
}

function fmtBox(box) {
  if (!box) return "-";
  return `x1:${box.x1}, y1:${box.y1}, x2:${box.x2}, y2:${box.y2}`;
}

function renderResult(data) {
  if (!data) return;

  document.getElementById("detectTime").textContent = data.time || data.created_at || "-";
  document.getElementById("detectSource").textContent = data.source || "-";
  document.getElementById("objectCount").textContent = (data.objects || []).length;

  const events = data.hardware_events || [];
  document.getElementById("hardwareStatus").textContent = events.length ? events.map(e => e.status).join(", ") : "未触发";

  const imageName = data.result_image;
  const resultImage = document.getElementById("resultImage");
  if (imageName) {
    resultImage.src = `/files/result/${imageName}?t=${Date.now()}`;
  }

  const tbody = document.getElementById("objectTable");
  tbody.innerHTML = "";

  const objects = data.objects || [];
  if (!objects.length) {
    tbody.innerHTML = `<tr><td colspan="4">没有检测到目标</td></tr>`;
    return;
  }

  for (const obj of objects) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${obj.class_id}</td>
      <td>${obj.class_name}</td>
      <td>${obj.confidence}</td>
      <td>${fmtBox(obj.box_xyxy)}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function detectCamera() {
  cameraBtn.disabled = true;
  logMessage("正在调用摄像头并进行 YOLO 检测，请稍等...");

  try {
    const res = await fetch("/api/detect/camera", { method: "POST" });
    const json = await res.json();
    if (json.status !== "ok") throw new Error(json.message || "检测失败");
    renderResult(json.data);
    await loadHistory();
    logMessage("摄像头识别完成。结果已保存到 images/、results/images/、results/json/、results/txt/。 ");
  } catch (err) {
    logMessage("错误：" + err.message);
  } finally {
    cameraBtn.disabled = false;
  }
}

async function detectUpload() {
  const file = imageInput.files[0];
  if (!file) {
    alert("请先选择一张图片");
    return;
  }

  uploadBtn.disabled = true;
  logMessage("正在上传图片并进行 YOLO 检测...");

  const form = new FormData();
  form.append("image", file);

  try {
    const res = await fetch("/api/detect/upload", { method: "POST", body: form });
    const json = await res.json();
    if (json.status !== "ok") throw new Error(json.message || "检测失败");
    renderResult(json.data);
    await loadHistory();
    logMessage("上传图片识别完成。结果已保存。 ");
  } catch (err) {
    logMessage("错误：" + err.message);
  } finally {
    uploadBtn.disabled = false;
  }
}

async function loadHistory() {
  try {
    const res = await fetch("/api/history?limit=20");
    const json = await res.json();
    if (json.status !== "ok") throw new Error(json.message || "读取历史失败");

    const tbody = document.getElementById("historyTable");
    tbody.innerHTML = "";

    const rows = json.data || [];
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="8">暂无历史</td></tr>`;
      return;
    }

    for (const item of rows) {
      const classes = (item.objects || []).map(o => o.class_name).join(", ") || "-";
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.id}</td>
        <td>${item.created_at || item.time || "-"}</td>
        <td>${item.source || "-"}</td>
        <td>${item.object_count ?? (item.objects || []).length}</td>
        <td>${classes}</td>
        <td><a href="/files/result/${item.result_image}" target="_blank">查看</a></td>
        <td><a href="/files/json/${item.json_file}" target="_blank">JSON</a></td>
        <td><a href="/files/txt/${item.txt_file}" target="_blank">TXT</a></td>
      `;
      tbody.appendChild(tr);
    }
  } catch (err) {
    logMessage("读取历史失败：" + err.message);
  }
}

async function loadLatest() {
  try {
    const res = await fetch("/api/latest");
    const json = await res.json();
    if (json.status === "ok" && json.data) {
      renderResult(json.data);
    }
  } catch (_) {
    // 页面初始化时失败不弹窗
  }
}

cameraBtn.addEventListener("click", detectCamera);
uploadBtn.addEventListener("click", detectUpload);
refreshHistoryBtn.addEventListener("click", loadHistory);

loadLatest();
loadHistory();
