import { useEffect, useState } from "react";
import { api } from "../api";

export default function Groups() {
  const [groups, setGroups] = useState([]);
  const [instances, setInstances] = useState([]);
  const [msg, setMsg] = useState(null);

  async function load() {
    setInstances(await api.listInstances());
    setGroups(await api.listGroups());
  }
  useEffect(() => {
    load().catch((e) => setMsg(e.message));
  }, []);

  async function patch(id, data) {
    try {
      const updated = await api.updateGroup(id, data);
      setGroups((gs) => gs.map((g) => (g.id === id ? updated : g)));
    } catch (e) {
      setMsg(e.message);
    }
  }

  const instName = (id) => instances.find((i) => i.id === id)?.name || id;

  return (
    <div>
      <h2>Grupos de WhatsApp</h2>
      <p className="muted">
        Activa los grupos de los que quieres extraer transferencias. Usa "Sync grupos" en
        Conexión WhatsApp para traer la lista desde Evolution API.
      </p>
      {msg && <div className="err">{msg}</div>}
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Activo</th><th>Grupo</th><th>Conexión</th>
              <th>Tel. informe</th><th>Email informe</th><th>Hora</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <tr key={g.id}>
                <td>
                  <input
                    type="checkbox"
                    style={{ width: 18 }}
                    checked={g.active}
                    onChange={(e) => patch(g.id, { active: e.target.checked })}
                  />
                </td>
                <td>{g.name || g.group_jid}</td>
                <td className="muted">{instName(g.instance_id)}</td>
                <td>
                  <input
                    defaultValue={g.report_phone || ""}
                    placeholder="(global)"
                    onBlur={(e) => patch(g.id, { report_phone: e.target.value || null })}
                  />
                </td>
                <td>
                  <input
                    defaultValue={g.report_email || ""}
                    placeholder="(global)"
                    onBlur={(e) => patch(g.id, { report_email: e.target.value || null })}
                  />
                </td>
                <td style={{ width: 90 }}>
                  <input
                    defaultValue={g.report_time || ""}
                    placeholder="(global)"
                    onBlur={(e) => patch(g.id, { report_time: e.target.value || null })}
                  />
                </td>
              </tr>
            ))}
            {groups.length === 0 && (
              <tr><td colSpan={6} className="muted">No hay grupos. Sincroniza desde una conexión.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
