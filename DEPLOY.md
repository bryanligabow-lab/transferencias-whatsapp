# Despliegue permanente en easypanel

El sistema se empaqueta en **un solo contenedor** (Dockerfile en la raíz) que sirve a la vez
el **dashboard** y la **API**, e incluye **Tesseract OCR**. Lo despliegas en el mismo easypanel
donde tienes Evolution API y obtienes un **dominio fijo**, así el webhook nunca cambia.

## 1. Subir el código a GitHub
Desde la carpeta del proyecto:
```bash
git init
git add .
git commit -m "Sistema de transferencias por WhatsApp"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/transferencias-whatsapp.git
git push -u origin main
```
> El `.gitignore` ya excluye `.env`, `node_modules`, `.venv` y la base de datos local.

## 2. Crear el servicio en easypanel
1. **Create Service → App**.
2. **Source → GitHub**: elige el repositorio y la rama `main`.
3. **Build → Dockerfile**. Ruta del Dockerfile: `Dockerfile` (contexto = raíz del repo).
4. **Deploy**. La primera vez easypanel construye la imagen (instala Tesseract, compila el dashboard).

## 3. Volumen persistente (importante)
La base de datos y las imágenes viven en `/data`. Añade un **Volume**:
- **Mount path:** `/data`
Así no se pierden los datos al redesplegar.

## 4. Dominio
En la pestaña **Domains** del servicio, easypanel te da un dominio (o pon uno propio).
El puerto interno es **8000**. Copia ese dominio, p. ej.:
`https://transferencias-whatsapp.dtuoap.easypanel.host`

## 5. Variables de entorno
En **Environment** del servicio, pega estas (usa las claves generadas más abajo):

```
ENCRYPTION_KEY=ghKHpptIeqCXKeMnSJhxZPoVUBGnYmLcqv-VEzyR11g=
JWT_SECRET=F5nNNrbI_byDBKfE7MSRj1Y5v9huHYgvpkkPpvbBOTOUhdtzHwaBvqNvV2qL3xoV
ADMIN_USERNAME=admin
ADMIN_PASSWORD=pon_una_clave_fuerte
TIMEZONE=America/Guayaquil
PUBLIC_BASE_URL=https://TU-DOMINIO.easypanel.host

# Email (opcional, para el informe por correo)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tucorreo@gmail.com
SMTP_PASSWORD=tu_app_password
SMTP_FROM=tucorreo@gmail.com
SMTP_USE_TLS=true
```

> **PUBLIC_BASE_URL** debe ser EXACTAMENTE el dominio del paso 4 (con `https://`).
> Tras ponerla, vuelve a **Deploy** para que tome el valor.

⚠️ **Guarda `ENCRYPTION_KEY` y no la cambies nunca**: con ella se encriptan las credenciales
de Evolution en la base de datos. Si la cambias, no se podrán desencriptar.

## 6. Conectar WhatsApp desde el dashboard
1. Abre `https://TU-DOMINIO.easypanel.host` y entra con `admin` / tu clave.
2. **Conexión WhatsApp → Nueva conexión**:
   - URL: `https://contabilidad-mateai-evolution-api.dtuoap.easypanel.host`
   - Instance name: `85ce522d-9188-424e-9f9a-ac0fd1961b42` (o el nombre de tu instancia)
   - API Key: tu API key de Evolution
   - Guardar → el **webhook se registra solo** apuntando a tu dominio permanente.
3. **Sync grupos** y activa los grupos a monitorear.
4. **Informe / Config**: teléfono, email y hora del informe diario.

## 7. Comprobar
Envía una captura de transferencia a un grupo activo y revisa la pestaña **Transferencias**.

---
### Notas
- Como Evolution y este servicio están en el mismo easypanel, la conexión es estable y el
  webhook no vuelve a cambiar.
- Para activar el modo híbrido OCR + modelo local (sin tokens), añade un servicio Ollama en
  easypanel y pon `PARSE_MODE=hybrid`, `OLLAMA_BASE_URL=http://NOMBRE_SERVICIO_OLLAMA:11434`.
- Para PostgreSQL en vez de SQLite: define `DATABASE_URL=postgresql+psycopg://...` (añade
  `psycopg[binary]` a requirements).
