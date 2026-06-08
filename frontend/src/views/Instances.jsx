import { useEffect, useState } from "react";
import { api } from "../api";

const EMPTY = { name: "", instance_name: "", base_url: "", api_key: "" };

export default function Instances() {
  const [list, setList] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [editing, setEditing] = useState(null);
  const [msg, setMsg] = useState(null);
  const [qr, setQr] = useState(null);

  async function load() {
    try {
      setList(await api.listInstances());
    } catch (e) {
      setMsg({ type: "err", text: e.message });
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function save(e) {
    e.preventDefault();
    setMsg(null);
    try {
      if (editing) await api.updateInstance(editing, form);
      else await api.createInstance(form);
      setForm(EMPTY);
      setEditing(null);
      setMsg({ type: "ok", text: "Conexión guardada y webhook configurado." });
      load();
    } catch (e) {
      setMsg({ type: "err", text: e.message });
    }
  }

  async function test(id) {
    setMsg(null);
    try {
      const r = await api.testInstance(id);
      setMsg({ type: "ok", text: `Estado: ${r.state} (${r.connected ? "conectado" : "no conectado"})` });
      load();
    } catch (e) {
      setMsg({ type: "err", text: e.message });
    }
  }

  async function showQr(id) {
    setMsg(null);
    setQr({ id, loading: true });
    try {
      const r = await api.getQr(id);
      setQr({ id, ...r, loading: false });
      if (r.state === "open") load();
    } catch (e) {
      setQr(null);
      setMsg({ type: "err", text: e.message });
    }
  }

  async function sync(id) {
    setMsg(null);
    try {
      const r = await api.syncGroups(id);
      setMsg({ type: "ok", text: `Grupos sincronizados: ${r.new_groups} nuevos de ${r.total}.` });
    } catch (e) {
      setMsg({ type: "err", text: e.message });
    }
  }

  async function remove(id) {
    if (!confirm("¿Eliminar esta conexión y sus grupos?")) return;
    await api.deleteInstance(id);
    load();
  }

  function edit(i) {
    setEditing(i.id);
    setForm({ name: i.name, instance_name: i.instance_name, base_url: i.base_url, api_key: "" });
  }

  return (
    <div>
      <h2>Conexión WhatsApp (Evolution API)</h2>

      <form className="card" onSubmit={save}>
        <h3>{editing ? "Editar conexión" : "Nueva conexión"}</h3>
        <div className="row">
          <div className="field">
            <label>Nombre (etiqueta)</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div className="field">
            <label>Instance name (Evolution)</label>
            <input value={form.instance_name} onChange={(e) => setForm({ ...form, instance_name: e.target.value })} required />
          </div>
        </div>
        <div className="row" style={{ marginTop: 12 }}>
          <div className="field">
            <label>URL del servidor Evolution API</label>
            <input value={form.base_url} placeholder="https://evolution.midominio.com" onChange={(e) => setForm({ ...form, base_url: e.target.value })} required />
          </div>
          <div className="field">
            <label>API Key / Token {editing && "(dejar vacío para no cambiar)"}</label>
            <input value={form.api_key} type="password" onChange={(e) => setForm({ ...form, api_key: e.target.value })} required={!editing} />
          </div>
        </div>
        <div style={{ marginTop: 14, display: "flex", gap: 10 }}>
          <button className="btn">{editing ? "Guardar cambios" : "Crear y configurar webhook"}</button>
          {editing && (
            <button type="button" className="btn secondary" onClick={() => { setEditing(null); setForm(EMPTY); }}>
              Cancelar
            </button>
          )}
        </div>
        {msg && <div className={msg.type}>{msg.text}</div>}
      </form>

      <div className="card">
        <h3>Conexiones</h3>
        <table>
          <thead>
            <tr><th>Nombre</th><th>Instancia</th><th>URL</th><th>Estado</th><th>Acciones</th></tr>
          </thead>
          <tbody>
            {list.map((i) => (
              <tr key={i.id}>
                <td>{i.name}</td>
                <td>{i.instance_name}</td>
                <td className="muted">{i.base_url}</td>
                <td>
                  <span className={`badge ${i.connected ? "processed" : "pending_review"}`}>
                    {i.connected ? "conectado" : i.status}
                  </span>
                </td>
                <td style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  <button className="btn secondary" onClick={() => test(i.id)}>Probar</button>
                  <button className="btn secondary" onClick={() => showQr(i.id)}>QR</button>
                  <button className="btn secondary" onClick={() => sync(i.id)}>Sync grupos</button>
                  <button className="btn secondary" onClick={() => edit(i)}>Editar</button>
                  <button className="btn danger" onClick={() => remove(i.id)}>Eliminar</button>
                </td>
              </tr>
            ))}
            {list.length === 0 && <tr><td colSpan={5} className="muted">Sin conexiones aún.</td></tr>}
          </tbody>
        </table>
      </div>

      {qr && (
        <div className="modal-bg" onClick={() => setQr(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Vincular WhatsApp</h3>
            {qr.loading && <p>Cargando…</p>}
            {qr.state === "open" && <p className="ok">Ya está conectado.</p>}
            {qr.qr && <img className="qr" src={qr.qr} alt="QR" />}
            {qr.code && !qr.qr && <p className="muted">Código de emparejamiento: <b>{qr.code}</b></p>}
            {!qr.loading && !qr.qr && qr.state !== "open" && <p className="muted">Sin QR disponible (¿ya vinculado?).</p>}
            <p className="muted">Escanea desde WhatsApp &gt; Dispositivos vinculados.</p>
            <button className="btn" onClick={() => showQr(qr.id)}>Refrescar</button>
            <button className="btn secondary" onClick={() => setQr(null)} style={{ marginLeft: 8 }}>Cerrar</button>
          </div>
        </div>
      )}
    </div>
  );
}
