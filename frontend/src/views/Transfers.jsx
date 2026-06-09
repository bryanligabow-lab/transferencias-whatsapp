import { useEffect, useState } from "react";
import { api, fetchImageBlob } from "../api";

// Fecha actual en zona de Ecuador (igual que el local_date del backend), no en UTC.
const today = () =>
  new Intl.DateTimeFormat("en-CA", { timeZone: "America/Guayaquil" }).format(new Date());

function AuthImage({ transferId, className, style, onClick, alt = "" }) {
  const [url, setUrl] = useState(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    let objectUrl = null;
    setError(false);
    fetchImageBlob(transferId)
      .then((u) => {
        if (active) {
          objectUrl = u;
          setUrl(u);
        } else {
          URL.revokeObjectURL(u);
        }
      })
      .catch(() => active && setError(true));
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [transferId]);
  if (error) return <span className={className} style={style} title="Imagen no disponible">⚠️</span>;
  if (!url) return <span className={className} style={style} />;
  return <img className={className} style={style} src={url} onClick={onClick} alt={alt} />;
}

export default function Transfers() {
  const [items, setItems] = useState([]);
  const [groups, setGroups] = useState([]);
  const [filters, setFilters] = useState({ date: today(), group_id: "", status: "" });
  const [editRow, setEditRow] = useState(null);
  const [preview, setPreview] = useState(null);
  const [msg, setMsg] = useState(null);

  async function load() {
    try {
      setItems(await api.listTransfers(filters));
    } catch (e) {
      setMsg(e.message);
    }
  }
  useEffect(() => {
    api.listGroups().then(setGroups).catch(() => {});
  }, []);
  useEffect(() => {
    load();
  }, [filters]);

  async function saveEdit() {
    try {
      await api.updateTransfer(editRow.id, {
        sender_name: editRow.sender_name,
        reference: editRow.reference,
        account: editRow.account,
        bank: editRow.bank,
        transfer_datetime: editRow.transfer_datetime,
        amount: editRow.amount === "" ? null : parseFloat(editRow.amount),
        status: editRow.status,
      });
      setEditRow(null);
      load();
    } catch (e) {
      setMsg(e.message);
    }
  }

  async function remove(id) {
    if (!confirm("¿Eliminar transferencia?")) return;
    await api.deleteTransfer(id);
    load();
  }

  const groupName = (id) => groups.find((g) => g.id === id)?.name || "-";

  return (
    <div>
      <h2>Transferencias</h2>
      <div className="toolbar">
        <div className="field" style={{ maxWidth: 170 }}>
          <label>Fecha</label>
          <input type="date" value={filters.date} onChange={(e) => setFilters({ ...filters, date: e.target.value })} />
        </div>
        <div className="field" style={{ maxWidth: 200 }}>
          <label>Grupo</label>
          <select value={filters.group_id} onChange={(e) => setFilters({ ...filters, group_id: e.target.value })}>
            <option value="">Todos</option>
            {groups.map((g) => <option key={g.id} value={g.id}>{g.name || g.group_jid}</option>)}
          </select>
        </div>
        <div className="field" style={{ maxWidth: 180 }}>
          <label>Estado</label>
          <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <option value="">Todos</option>
            <option value="processed">Procesada</option>
            <option value="pending_review">Pendiente de revisión</option>
            <option value="invalid">Inválida</option>
          </select>
        </div>
        <button className="btn secondary" onClick={load}>Refrescar</button>
      </div>
      {msg && <div className="err">{msg}</div>}

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Img</th><th>Nombre</th><th>Referencia</th><th>Cuenta</th>
              <th>Banco</th><th>Fecha</th><th>Monto</th><th>Grupo</th><th>Estado</th><th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id}>
                <td><AuthImage className="thumb" transferId={t.id} onClick={() => setPreview(t.id)} /></td>
                <td>{t.sender_name || "-"}</td>
                <td>{t.reference || "-"}</td>
                <td>{t.account || "-"}</td>
                <td>{t.bank || "-"}</td>
                <td>{t.transfer_datetime || "-"}</td>
                <td>{t.amount != null ? `$${t.amount.toFixed(2)}` : "-"}</td>
                <td className="muted">{groupName(t.group_id)}</td>
                <td>
                  <span className={`badge ${t.status}`}>{t.status}</span>
                  {t.review_reason && <div className="muted">{t.review_reason}</div>}
                </td>
                <td style={{ whiteSpace: "nowrap" }}>
                  <button className="btn secondary" onClick={() => setEditRow({ ...t })}>Editar</button>{" "}
                  <button className="btn danger" onClick={() => remove(t.id)}>X</button>
                </td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={10} className="muted">Sin transferencias.</td></tr>}
          </tbody>
        </table>
      </div>

      {editRow && (
        <div className="modal-bg" onClick={() => setEditRow(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Revisar / corregir transferencia</h3>
            {[
              ["sender_name", "Nombre"],
              ["reference", "Referencia"],
              ["account", "Cuenta"],
              ["bank", "Banco"],
              ["transfer_datetime", "Fecha y hora"],
              ["amount", "Monto"],
            ].map(([k, label]) => (
              <div key={k} className="field" style={{ marginBottom: 10 }}>
                <label>{label}</label>
                <input
                  value={editRow[k] ?? ""}
                  onChange={(e) => setEditRow({ ...editRow, [k]: e.target.value })}
                />
              </div>
            ))}
            <div className="field" style={{ marginBottom: 12 }}>
              <label>Estado</label>
              <select value={editRow.status} onChange={(e) => setEditRow({ ...editRow, status: e.target.value })}>
                <option value="processed">Procesada</option>
                <option value="pending_review">Pendiente de revisión</option>
                <option value="invalid">Inválida</option>
              </select>
            </div>
            <button className="btn green" onClick={saveEdit}>Guardar</button>
            <button className="btn secondary" onClick={() => setEditRow(null)} style={{ marginLeft: 8 }}>Cancelar</button>
          </div>
        </div>
      )}

      {preview && (
        <div className="modal-bg" onClick={() => setPreview(null)}>
          <AuthImage transferId={preview} style={{ maxHeight: "85vh", borderRadius: 8 }} alt="comprobante" />
        </div>
      )}
    </div>
  );
}
