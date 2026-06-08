import { useEffect, useState } from "react";
import { api } from "../api";

export default function Config() {
  const [cfg, setCfg] = useState({ report_phone: "", report_email: "", report_time: "20:00" });
  const [msg, setMsg] = useState(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    api.getConfig().then(setCfg).catch((e) => setMsg({ type: "err", text: e.message }));
  }, []);

  async function save(e) {
    e.preventDefault();
    setMsg(null);
    try {
      await api.updateConfig(cfg);
      setMsg({ type: "ok", text: "Configuración guardada. Informe reprogramado." });
    } catch (e) {
      setMsg({ type: "err", text: e.message });
    }
  }

  async function sendNow() {
    setSending(true);
    setMsg(null);
    try {
      const r = await api.sendReportNow();
      setMsg({
        type: "ok",
        text: `Informe generado: total $${r.total} (${r.count} transf.). WhatsApp: ${r.whatsapp ? "ok" : "no"}, Email: ${r.email ? "ok" : "no"}.`,
      });
    } catch (e) {
      setMsg({ type: "err", text: e.message });
    } finally {
      setSending(false);
    }
  }

  return (
    <div>
      <h2>Informe diario / Configuración global</h2>
      <form className="card" onSubmit={save}>
        <p className="muted">
          Valores por defecto del informe diario. Cada grupo puede sobrescribirlos en la pestaña Grupos.
        </p>
        <div className="row">
          <div className="field">
            <label>Teléfono para informe (con código país, ej. 5939...)</label>
            <input value={cfg.report_phone} onChange={(e) => setCfg({ ...cfg, report_phone: e.target.value })} />
          </div>
          <div className="field">
            <label>Email para informe</label>
            <input value={cfg.report_email} onChange={(e) => setCfg({ ...cfg, report_email: e.target.value })} />
          </div>
          <div className="field" style={{ maxWidth: 140 }}>
            <label>Hora de envío</label>
            <input type="time" value={cfg.report_time} onChange={(e) => setCfg({ ...cfg, report_time: e.target.value })} />
          </div>
        </div>
        <div style={{ marginTop: 14, display: "flex", gap: 10 }}>
          <button className="btn">Guardar</button>
          <button type="button" className="btn green" disabled={sending} onClick={sendNow}>
            {sending ? "Enviando…" : "Enviar informe ahora"}
          </button>
        </div>
        {msg && <div className={msg.type}>{msg.text}</div>}
      </form>
    </div>
  );
}
