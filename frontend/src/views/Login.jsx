import { useState } from "react";
import { api, setToken } from "../api";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      const { access_token } = await api.login(username, password);
      setToken(access_token);
      onLogin();
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="card login-card" onSubmit={submit}>
        <h2>Iniciar sesión</h2>
        <div className="field" style={{ marginBottom: 12 }}>
          <label>Usuario</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </div>
        <div className="field" style={{ marginBottom: 12 }}>
          <label>Contraseña</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button className="btn" disabled={loading} style={{ width: "100%" }}>
          {loading ? "Ingresando..." : "Entrar"}
        </button>
        {err && <div className="err">{err}</div>}
      </form>
    </div>
  );
}
