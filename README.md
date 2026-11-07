# 🌍 El Mundo al Día

Periódico familiar estático en español, accesible desde el celular. Sin base de datos. La edición diaria se genera en n8n; el sitio es un contenedor nginx estático.

## Deploy en Coolify (`noticias.aisolutions.at`)

1. Empuja este repo a GitHub (`grobald/el-mundo-al-dia` o el remoto que uses).
2. En Coolify: **+ New Resource → Application → Public Repository** (o GitHub App si el repo es privado).
3. Ajustes:
   - **Build Pack:** Dockerfile
   - **Branch:** `main`
   - **Ports Exposes:** `80`
   - **Domain:** `https://noticias.aisolutions.at`
   - **Healthcheck Path:** `/health` (opcional; el Dockerfile ya incluye un healthcheck)
4. Deploy. El HTML lee primero el webhook n8n (`/webhook/el-mundo-al-dia`) y, si falla, los JSON en `/data/`.

API token de Coolify (para MCP/automatización): **Keys & Tokens** en el perfil → crear token con permisos de lectura/escritura/deploy → pegarlo en Cursor MCP (`coolify` Authorization header).

## Publicar gratis en GitHub Pages

1. Crea una cuenta en https://github.com y un repositorio **público** llamado `el-mundo-al-dia`.
2. Descomprime este ZIP y sube **todos los archivos y carpetas**, incluida `.github/workflows/daily.yml`, a la raíz del repositorio. Puedes usar **Add file → Upload files**; comprueba que la carpeta `.github` también se haya subido.
3. En el repositorio, abre **Settings → Pages → Build and deployment → Source: Deploy from a branch**. Selecciona `main` y `/(root)`, y guarda.
4. En unos minutos, la dirección será `https://TU-USUARIO.github.io/el-mundo-al-dia/` (sustituye TU-USUARIO). Puedes compartirla por WhatsApp.
5. Para activar la redacción automática, crea una clave de API en https://platform.openai.com/api-keys . La API tiene **facturación independiente de ChatGPT**; configura un límite de gasto.
6. En GitHub: **Settings → Secrets and variables → Actions → New repository secret**. Nombres exactos: `OPENAI_API_KEY` y `SERPAPI_API_KEY`. Pega las claves **solo allí**, nunca en el código ni en el sitio público.
7. Abre **Actions → Actualizar noticias diariamente → Run workflow** para probar. La edición nueva aparecerá después del commit y la publicación de GitHub Pages.

## Qué hace

- Cada mañana intenta ejecutar la actualización a las **08:00, hora de Austria**, con ajuste de horario de verano/invierno.
- Recoge titulares de las **últimas 24 horas** con SerpAPI Google News (incl. site: Reuters/AP/Bloomberg/FT) y RSS directos de **ORF, BBC, DW, Andina y RPP**.
- Usa OpenAI con un prompt editorial de redacción senior para seleccionar 7–10 noticias, marcar el **Top 3**, contrastar fuentes y redactar resúmenes en español y alemán.
- Añade un snapshot de mercados verificado (BTC, ETH, EUR/USD, S&P 500, Nasdaq, oro, Brent).
- Conserva las ediciones anteriores y no reemplaza la última edición si falla la actualización.
- Diseño responsive con briefing del día, destacadas, mercados y sección Perú/Austria.

## Limitaciones importantes

- **No es verificación periodística completa.** SerpAPI aporta titulares, snippets, fechas y enlaces — no el texto completo del artículo. El modelo puede contrastar varias fuentes del pack, pero no sustituye una redacción humana. El sitio señala esta limitación.
- Los feeds pueden fallar, cambiar o incluir duplicados. Las tareas programadas de GitHub Actions pueden retrasarse u omitirse. La página muestra la fecha real de la última edición publicada.
- No garantiza 7–10 noticias si no hay material suficiente. En ese caso puede publicar menos, o conservar la edición anterior.
- La publicación en un repositorio público deja visibles los textos de las ediciones. **Nunca** incluyas secretos en archivos del repositorio.
- La actualización consume tokens de la API de OpenAI (costo variable), aunque GitHub Pages suele ser gratuito para repositorios públicos dentro de sus límites de uso.
- El ejemplo inicial del 6/11/2026 está claramente marcado como **demostración** y no debe interpretarse como noticias reales.
- Si GitHub suspende el workflow por inactividad prolongada, reactívalo desde Actions.

## Archivos

- `index.html`: web completa.
- `data/manifest.json`: lista de ediciones.
- `data/YYYY-MM-DD.json`: noticias de cada día.
- `update.py`: descarga titulares y prepara la edición.
- `.github/workflows/daily.yml`: automatización diaria.

## Personalización

Cambia el nombre, colores o textos en `index.html`. Puedes configurar el modelo con la variable de entorno `OPENAI_MODEL` en el workflow. Para usar dominio propio, configúralo en GitHub Pages y en tu DNS.
