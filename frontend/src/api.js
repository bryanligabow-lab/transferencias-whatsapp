const TOKEN_KEY = "tr_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (auth && getToken()) headers["Authorization"] = `Bearer ${getToken()}`;
  const res = await fetch(`/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) {
    setToken(null);
    throw new Error("Sesión expirada");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {}
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

export const api = {
  login: (username, password) =>
    request("/auth/login", { method: "POST", body: { username, password }, auth: false }),

  listInstances: () => request("/instances"),
  createInstance: (data) => request("/instances", { method: "POST", body: data }),
  updateInstance: (id, data) => request(`/instances/${id}`, { method: "PUT", body: data }),
  deleteInstance: (id) => request(`/instances/${id}`, { method: "DELETE" }),
  testInstance: (id) => request(`/instances/${id}/test`, { method: "POST" }),
  getQr: (id) => request(`/instances/${id}/qr`),
  syncGroups: (id) => request(`/instances/${id}/sync-groups`, { method: "POST" }),

  listGroups: (instanceId) =>
    request(`/groups${instanceId ? `?instance_id=${instanceId}` : ""}`),
  updateGroup: (id, data) => request(`/groups/${id}`, { method: "PUT", body: data }),

  listTransfers: (params = {}) => {
    const q = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null && v !== "")
    ).toString();
    return request(`/transfers${q ? `?${q}` : ""}`);
  },
  totals: (date) => request(`/transfers/totals${date ? `?date=${date}` : ""}`),
  updateTransfer: (id, data) => request(`/transfers/${id}`, { method: "PUT", body: data }),
  deleteTransfer: (id) => request(`/transfers/${id}`, { method: "DELETE" }),

  getConfig: () => request("/config"),
  updateConfig: (data) => request("/config", { method: "PUT", body: data }),
  sendReportNow: (date) =>
    request(`/config/send-report-now${date ? `?date=${date}` : ""}`, { method: "POST" }),
};

export function imageUrl(transferId) {
  return `/api/transfers/${transferId}/image`;
}
