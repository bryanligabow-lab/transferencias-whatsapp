import { useState } from "react";
import { getToken, setToken } from "./api";
import Login from "./views/Login.jsx";
import Instances from "./views/Instances.jsx";
import Groups from "./views/Groups.jsx";
import Transfers from "./views/Transfers.jsx";
import Config from "./views/Config.jsx";
import Overview from "./views/Overview.jsx";

const VIEWS = [
  { key: "overview", label: "Resumen", comp: Overview },
  { key: "instances", label: "Conexión WhatsApp", comp: Instances },
  { key: "groups", label: "Grupos", comp: Groups },
  { key: "transfers", label: "Transferencias", comp: Transfers },
  { key: "config", label: "Informe / Config", comp: Config },
];

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  const [view, setView] = useState("overview");

  if (!authed) return <Login onLogin={() => setAuthed(true)} />;

  const Current = VIEWS.find((v) => v.key === view).comp;

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>Transferencias WhatsApp</h1>
        {VIEWS.map((v) => (
          <button
            key={v.key}
            className={`nav-btn ${view === v.key ? "active" : ""}`}
            onClick={() => setView(v.key)}
          >
            {v.label}
          </button>
        ))}
        <button
          className="nav-btn logout"
          onClick={() => {
            setToken(null);
            setAuthed(false);
          }}
        >
          Cerrar sesión
        </button>
      </aside>
      <main className="content">
        <Current />
      </main>
    </div>
  );
}
