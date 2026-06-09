import { useEffect, useState } from "react";
import { api } from "../api";

// Fecha actual en zona de Ecuador (igual que el local_date del backend), no en UTC.
const today = () =>
  new Intl.DateTimeFormat("en-CA", { timeZone: "America/Guayaquil" }).format(new Date());

export default function Overview() {
  const [date, setDate] = useState(today());
  const [totals, setTotals] = useState(null);
  const [groups, setGroups] = useState([]);
  const [msg, setMsg] = useState(null);

  async function load() {
    try {
      setTotals(await api.totals(date));
      setGroups(await api.listGroups());
    } catch (e) {
      setMsg(e.message);
    }
  }
  useEffect(() => {
    load();
  }, [date]);

  const groupName = (id) => groups.find((g) => g.id === id)?.name || "Sin grupo";

  return (
    <div>
      <h2>Resumen</h2>
      <div className="toolbar">
        <div className="field" style={{ maxWidth: 180 }}>
          <label>Fecha</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </div>
      </div>
      {msg && <div className="err">{msg}</div>}
      {totals && (
        <>
          <div className="card stat">
            <div>
              <div className="muted">Total vendido por transferencias</div>
              <div className="big">${totals.total.toFixed(2)}</div>
            </div>
            <div>
              <div className="muted">Transferencias</div>
              <div className="big">{totals.count}</div>
            </div>
          </div>
          <div className="card">
            <h3>Por grupo</h3>
            <table>
              <thead><tr><th>Grupo</th><th>Cantidad</th><th>Total</th></tr></thead>
              <tbody>
                {totals.by_group.map((g) => (
                  <tr key={g.group_id ?? "none"}>
                    <td>{groupName(g.group_id)}</td>
                    <td>{g.count}</td>
                    <td>${g.total.toFixed(2)}</td>
                  </tr>
                ))}
                {totals.by_group.length === 0 && <tr><td colSpan={3} className="muted">Sin datos.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
