# Sistema de extracción y reporte de transferencias por WhatsApp

Monitorea grupos de WhatsApp (vía **Evolution API**), extrae datos de las
**capturas de transferencias** con **OCR local (Tesseract)** —sin consumir tokens de
ninguna API de IA—, los guarda en base de datos y envía un **informe diario** (total +
PDF) por **WhatsApp** y **correo**. Todo se administra desde un **dashboard web**.

```
extraccion tr/
├── backend/    FastAPI + OCR + parser + scheduler + Evolution API
└── frontend/   Dashboard React (Vite)
```

## Arquitectura

- **Backend:** Python / FastAPI.
- **OCR:** Tesseract (local) vía pytesseract. Opcional: modelo local con **Ollama** (modo híbrido).
- **Base de datos:** SQLite por defecto (cambiable a PostgreSQL con `DATABASE_URL`).
- **PDF:** ReportLab. **Email:** smtplib (SMTP). **Cron:** APScheduler (zona horaria Ecuador).
- **Seguridad:** login con JWT; credenciales de Evolution API **encriptadas con Fernet** en la BD.

### Flujo
1. El dashboard crea una conexión a Evolution API (URL, API key, instancia). El backend
   **registra automáticamente el webhook** en Evolution.
2. Llega un mensaje con imagen a un grupo activo → webhook → descarga imagen →
   `Tesseract OCR` → `parser` por banco (regex) → (opcional Ollama) → se guarda la transferencia.
3. Campos faltantes o baja confianza ⇒ estado **pendiente de revisión**. Imágenes que no
   parecen comprobantes ⇒ **inválida**. Se evitan duplicados (referencia o hash de imagen).
4. A la hora configurada, APScheduler genera el total + PDF del día y lo envía por WhatsApp y email.

## Requisitos previos

- **Python 3.11+**
- **Node.js 18+**
- **Tesseract OCR** instalado en el servidor:
  - macOS: `brew install tesseract tesseract-lang`
  - Ubuntu/Debian: `sudo apt install tesseract-ocr tesseract-ocr-spa`
- (Opcional, modo híbrido) **Ollama** con un modelo pequeño: `ollama pull llama3.2:3b`
- Un servidor de **Evolution API** accesible y una instancia creada.

## Backend — instalación y ejecución

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate   # o: uv venv .venv
pip install -r requirements.txt                          # o: uv pip install -r requirements.txt

cp .env.example .env
# Edita .env: genera ENCRYPTION_KEY y JWT_SECRET, configura SMTP, TIMEZONE,
# PUBLIC_BASE_URL (URL pública alcanzable por Evolution API) y ADMIN_USERNAME/PASSWORD.

# Generar clave de encriptación:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

La BD y sus tablas se crean solas al arrancar. Salud: `GET /health`.

### Variables de entorno (`.env`)
| Variable | Descripción |
|---|---|
| `DATABASE_URL` | SQLite (por defecto) o PostgreSQL. |
| `ENCRYPTION_KEY` | Clave Fernet para encriptar credenciales de Evolution API. **Obligatoria.** |
| `JWT_SECRET` | Secreto para los tokens del login. |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Acceso al dashboard. |
| `TIMEZONE` | Zona horaria del corte diario (`America/Guayaquil`). |
| `SMTP_*` | Servidor de correo para enviar el PDF. |
| `PUBLIC_BASE_URL` | URL pública del backend; se usa para registrar el webhook en Evolution. |
| `TESSERACT_CMD` / `TESSERACT_LANG` | Binario e idiomas de OCR (`spa+eng`). |
| `PARSE_MODE` | `rules` (solo OCR+regex) o `hybrid` (OCR + modelo local Ollama). |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | Para el modo híbrido. |

> **Nota:** La conexión a Evolution API (URL, token, instancia) **NO** se pone en variables
> de entorno: se configura desde el dashboard y se guarda **encriptada** en la BD.

## Frontend — instalación y ejecución

```bash
cd frontend
npm install
npm run dev      # desarrollo en http://localhost:5173 (proxy /api -> :8000)
# Producción:
npm run build    # genera frontend/dist (servir con cualquier servidor estático)
```

## Uso del dashboard
1. **Iniciar sesión** con `ADMIN_USERNAME`/`ADMIN_PASSWORD`.
2. **Conexión WhatsApp:** crea una conexión (URL, API key, instance name). El webhook se
   configura solo. Usa **Probar** para ver el estado y **QR** para vincular WhatsApp.
3. **Sync grupos** trae los grupos desde Evolution API.
4. **Grupos:** activa los grupos a monitorear; opcionalmente define tel./email/hora por grupo.
5. **Informe / Config:** define teléfono, email y hora del informe global. "Enviar informe
   ahora" lo genera al instante.
6. **Transferencias:** filtra por fecha/grupo/estado, revisa y corrige las pendientes, ve la imagen.
7. **Resumen:** total vendido del día y desglose por grupo.

## Añadir un banco nuevo al parser
Edita `backend/app/parser.py`, lista `BANKS`: agrega un `BankRule` con `keywords` de
detección y, si hace falta, `patterns` (regex con grupo 1 = valor) por campo. Las regex
genéricas de respaldo cubren monto, referencia, cuenta, fecha y nombre.

## Casos borde cubiertos
- Imágenes que no son transferencias → estado **inválida**.
- OCR de baja confianza o campos faltantes → **pendiente de revisión** (no se descarta).
- Anti-duplicados por referencia o hash de imagen.
- Zona horaria de Ecuador para el corte diario.
- Credenciales encriptadas y dashboard protegido con login JWT.

## Despliegue (resumen)
- Backend detrás de HTTPS (Nginx/Caddy) con `PUBLIC_BASE_URL` apuntando al dominio público.
- Servir `frontend/dist` como estático (mismo dominio o configurar CORS).
- Para producción, usar PostgreSQL en `DATABASE_URL` y un proceso supervisado
  (systemd, Docker, etc.) para `uvicorn`.
