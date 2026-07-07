async function postForm(url, form) {
  const response = await fetch(url, {
    method: "POST",
    body: new FormData(form)
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || data.detail || "Request failed");
  }
  return data;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || data.detail || "Request failed");
  }
  return data;
}

async function deleteJson(url) {
  const response = await fetch(url, { method: "DELETE" });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || data.detail || "Request failed");
  }
  return data;
}

function showJson(elementId, data) {
  document.getElementById(elementId).textContent = JSON.stringify(data, null, 2);
}

function accessText(allowed) {
  return allowed ? '<span class="status-open">允许开门</span>' : '<span class="status-deny">拒绝开门</span>';
}

async function loadPersons() {
  const response = await fetch("/api/v1/persons");
  const payload = await response.json();
  const body = document.getElementById("persons-body");
  if (!body) return;
  body.innerHTML = "";
  for (const person of payload.data || []) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${person.person_id}</td>
      <td>${person.name}</td>
      <td>${person.role || "-"}</td>
      <td>${person.authorized}</td>
      <td>${person.created_at || "-"}</td>
      <td><button class="danger" data-delete-person-id="${person.person_id}" data-delete-person-name="${person.name}">删除</button></td>
    `;
    body.appendChild(tr);
  }

  body.querySelectorAll("button[data-delete-person-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const personId = button.dataset.deletePersonId;
      const personName = button.dataset.deletePersonName || personId;
      const confirmed = window.confirm(`确定删除 ${personName} 吗？删除后该人员将不能再识别开门。`);
      if (!confirmed) return;

      button.disabled = true;
      try {
        const result = await deleteJson(`/api/v1/persons/${encodeURIComponent(personId)}`);
        const resultBox = document.getElementById("register-result");
        if (resultBox) {
          showJson("register-result", result);
        }
        await loadPersons();
      } catch (error) {
        const resultBox = document.getElementById("register-result");
        if (resultBox) {
          showJson("register-result", { code: 5000, message: error.message, data: null });
        } else {
          alert(error.message);
        }
      } finally {
        button.disabled = false;
      }
    });
  });
}

async function loadLogs() {
  const limit = document.getElementById("limit")?.value || 50;
  const response = await fetch(`/api/v1/access/logs?limit=${encodeURIComponent(limit)}`);
  const payload = await response.json();
  const body = document.getElementById("logs-body");
  if (!body) return;
  body.innerHTML = "";
  for (const log of payload.data || []) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${log.id}</td>
      <td>${log.created_at}</td>
      <td>${log.person_id ?? "-"}</td>
      <td>${log.name || "-"}</td>
      <td>${log.matched}</td>
      <td>${log.confidence}</td>
      <td>${accessText(log.door_allowed)}</td>
      <td>${log.reason}</td>
    `;
    body.appendChild(tr);
  }
}
