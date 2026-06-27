<div align="center">
  <a href="https://aidea-labs.com/mcp-for-stata">
    <img src="https://example-data.statamcp.com/logo_with_name.jpg" alt="MCP-for-Stata: Integra Stata en tu agente" width="300"/>
  </a>
</div>

# MCP-for-Stata: Integra Stata en tu agente
Permite que agentes de IA como Claude Code, Codex y OpenClaw invoquen Stata localmente en tu dispositivo para realizar análisis de datos de forma **segura**.

> Stata es una marca registrada de StataCorp LLC. Este proyecto es una herramienta independiente desarrollada por la comunidad y no esta afiliada, respaldada ni patrocinada por StataCorp LLC.

[![es](https://img.shields.io/badge/idioma-Español-green.svg)](README.es.md)
[![en](https://img.shields.io/badge/lang-English-red.svg)](README.md)
[![cn](https://img.shields.io/badge/语言-中文-yellow.svg)](README.zh-CN.md)
[![fr](https://img.shields.io/badge/langue-Français-blue.svg)](README.fr.md)
[![Publish to PyPI](https://github.com/SepineTam/mcp-for-stata/actions/workflows/python-package.yml/badge.svg)](https://github.com/SepineTam/mcp-for-stata/actions/workflows/python-package.yml)
[![PyPI version](https://img.shields.io/pypi/v/stata-mcp.svg)](https://pypi.org/project/stata-mcp/)
[![PyPI Downloads](https://static.pepy.tech/badge/stata-mcp)](https://pepy.tech/projects/stata-mcp)
[![License: AGPL 3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](LICENSE)
[![Issue](https://img.shields.io/badge/Issue-report-green.svg)](https://github.com/sepinetam/mcp-for-stata/issues/new)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/SepineTam/mcp-for-stata)

<!-- mcp-name: io.github.SepineTam/mcp-for-stata -->

---
## 🆕 Novedades
- Encuentra mas en WeChat: [Why I made it?](https://mp.weixin.qq.com/s/VYkykdDgfPMa5KN0_1BeFQ), y [8 figures find out Stata-MCP](https://mp.weixin.qq.com/s/RKPKA4OWAM5SeZmGtbMRew)
- 🦞 **Soporte para OpenClaw**: Herramientas CLI independientes para la integracion con OpenClaw (`stata-mcp tool`), consulta la [guia de OpenClaw](https://sepinetam.github.io/mcp-for-stata/agents/openclaw.md)
- ✨ **Soporte para plugin de Claude Code**: Paquete oficial de plugin con servidor MCP e integracion con Stata LSP
- Usa MCP-for-Stata en Claude Code, mira [la guia de uso avanzado de Claude Code](#advanced-claude-code), o Codex [la guia de uso avanzado de Codex](#advanced-codex)

> ¿Buscas nuestra **investigacion mas reciente**? [Consulta los informes de investigacion mas recientes](https://aidea-labs.com/mcp-for-stata/reports).

<details>
<summary>¿Buscas otros?</summary>

> **MCP o IA sobre Stata**
> - Un servidor MCP basado en sesiones para Stata, [mcp-stata](https://github.com/tmonk/mcp-stata)
> - IDEs (VScode o Cursor) integrados [usa Stata en VSCode](https://github.com/hanlulong/stata-mcp). ¿Confundido? 💡 [Comparacion](#comparacion)
>
> **Conjuntos de datos e informacion**
> - [STOP Dataset](https://opendata.ai4cssci.com): StataMCP-Team Opendata Project 📊, hemos publicado de forma abierta una coleccion integral de conjuntos de datos para la investigacion en ciencias sociales, con el objetivo de impulsar el futuro de los paradigmas de investigacion impulsados por IA y datos.
</details>

<details>
<summary>¿Por que la licencia AGPL 3.0?</summary>

La licencia AGPL 3.0 es un tipo de licencia de codigo abierto. No afecta su uso diario y le permite usar, modificar y distribuir este software de forma gratuita, siempre que cumpla con sus terminos, como conservar los avisos de derechos de autor originales.

**Notas**: Aunque nos esforzamos por hacer que el codigo abierto sea accesible para todos, lamentamos no poder mantener ya la licencia Apache-2.0. Debido a que algunas personas han copiado directamente este proyecto y se han atribuido ser sus mantenedores, hemos decidido cambiar la licencia a AGPL-3.0 para evitar usos indebidos del proyecto que vayan en contra de nuestra vision original.

Motivo:

**Antecedentes**: El [repositorio](https://github.com/jackdark425/aigroup-stata-mcp) de @jackdark425 copio directamente este proyecto y afirmo ser el unico mantenedor. Damos la bienvenida a la colaboracion de codigo abierto basada en forks, incluyendo pero no limitado a agregar nuevas funcionalidades, corregir errores existentes o proporcionar sugerencias valiosas para el proyecto, pero nos oponemos firmemente al plagio y a la atribucion falsa.

**Actualizacion**: El proyecto infractor ha sido retirado mediante DMCA de GitHub. [Ver detalles del retiro DMCA](https://github.com/github/dmca/blob/master/2025/12/2025-12-30-stata-mcp.md).

</details>

## 💡 Inicio rapido
### 🚀 ¡Instalación con un clic para todos los clientes!
Sin configuración ni edición manual de JSON. Un solo comando instala MCP-for-Stata para **todos los agentes compatibles** (Claude Code, Codex, OpenClaw, Cursor, Gemini CLI y más):

```bash
uvx stata-mcp install --all
```

<details>
<summary>Agentes soportados 🤖</summary>
Basado en nuestra propia experiencia y pruebas, recomendamos usar Claude Code, Codex y OpenClaw.
Hemos descubierto que Claude y DeepSeek son los dos mejores modelos en cualquier framework.

| Agente                    | Etiqueta | Comando                           |
|---------------------------|----------|-----------------------------------|
| Claude Desktop            | claude   | uvx stata-mcp install -c claude   |
| Claude Code               | cc       | uvx stata-mcp install -c cc       |
| Gemini CLI                | gemini   | uvx stata-mcp install -c gemini   |
| Cursor                    | cursor   | uvx stata-mcp install -c cursor   |
| Cline (VScode Extension)  | cline    | uvx stata-mcp install -c cline    |
| Codex CLI & Codex Desktop | codex    | uvx stata-mcp install -c codex    |
| OpenCode                  | opencode | uvx stata-mcp install -c opencode |
| OpenClaw                  | openclaw | uvx stata-mcp install -c openclaw |

</details>

Si no tienes `uv`, visita [la guia de instalacion de uv](https://docs.astral.sh/uv/getting-started/installation) para instalarlo.
O bien, usa nuestro script de instalacion beta (instala `uv` automaticamente si falta):

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/SepineTam/mcp-for-stata/master/scripts/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/SepineTam/mcp-for-stata/master/scripts/install.ps1 | iex
```

Si no sabes como usarlos, intenta [descargar los scripts de instalacion](https://github.com/SepineTam/mcp-for-stata/tree/master/scripts) y haz doble clic en tu dispositivo. `install.bat` para usuarios de Windows, y `install.command` para usuarios de macOS.

<a name="advanced-claude-code"></a>

### Avanzado - Claude Code
Dado que consideramos que Claude Code es el mejor agente para MCP-for-Stata por su excelente capacidad agentica, lo recomendamos, y hay muchos usos avanzados a continuacion:

Antes de usarlo, asegurate de haber instalado `Claude Code`, si no sabes como instalarlo, visita [GitHub](https://github.com/anthropics/claude-code)

En general, puedes instalar MCP-for-Stata globalmente una sola vez, puedes ejecutar:
```bash
claude mcp add stata-mcp --scope user -- uvx stata-mcp
```

Luego, no necesitas volver a verlo.

<details>
<summary>Local y compartir con tus colaboradores</summary>

Si deseas instalarlo localmente solo para un espacio de trabajo especifico, puedes hacer `cd` a tu directorio de trabajo y ejecutar:
```bash
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope local -- uvx --directory $(pwd) stata-mcp
```

No pasara nada, puedes escribir `claude` y escribir `/mcp` para encontrar el estado.

Ademas, la colaboracion es una parte esencial de la investigacion. Puedes compartir tu configuracion de MCP con tus coautores usando:
```bash
claude mcp add stata-mcp --scope project -- uvx stata-mcp
```
En tu directorio de trabajo, puedes encontrar un archivo llamado `.mcp.json`, tu configuracion de MCP se colocara aqui.

</details>

Luego, puedes usar MCP-for-Stata en Claude Code. Aqui hay algunos escenarios para usarlo:

- **Replicacion de articulos**: Replicar estudios empiricos de articulos de economia
- **Prueba rapida de hipotesis**: Validar hipotesis economicas mediante analisis de regresion
- **Asistente de aprendizaje de Stata**: Aprender econometria con explicaciones paso a paso en Stata
- **Organizacion de codigo**: Revisar y optimizar archivos do existentes de Stata
- **Interpretacion de resultados**: Comprender salidas estadisticas complejas y resultados de regresion

Si usas Claude Code dentro de IDEs (ya sea el terminal integrado o la Extension de Claude Code), instala nuestro plugin que incluye [MCP-for-Stata](https://github.com/sepinetam/mcp-for-stata) y [Stata LSP](https://github.com/euglevi/stata-language-server) mantenido por @euglevi.

```bash
# Agrega el marketplace de MCP-for-Stata
claude plugin marketplace add SepineTam/mcp-for-stata

# Instala el plugin en alcance local, de proyecto o de usuario
claude plugin install stata-toolbox -s project
```

> El servidor de lenguaje proporciona a los agentes de IA una mejor conciencia sintactica y completado de codigo Stata, lo que mejora la calidad de la salida. Empaquetamos el LSP en cumplimiento con su licencia y damos plena atribucion al autor original.

<a name="advanced-codex"></a>

### Avanzado - Codex
Descubrimos que muchos investigadores estan usando Codex como su agente, por lo tanto tambien proporcionamos instrucciones para usuarios de Codex.

Imagino que los investigadores no estan usando Codex CLI sino Codex Desktop, asi que podemos decir que es mas facil configurar MCP-for-Stata que otros agentes.

Solo necesitas decir `Install MCP-for-Stata for yourself globally from https://www.statamcp.com or visit https://github.com/SepineTam/mcp-for-stata` y luego reiniciar tu Codex Desktop despues de que diga listo.

Ademas, si deseas instalarlo manualmente, aqui hay dos formas:

#### A. Instalar en la GUI de Codex Desktop
1. Abre tu aplicacion Codex Desktop
2. Haz clic en `Settings` en la esquina inferior izquierda
3. Encuentra `MCP servers` en el lado izquierdo
4. Haz clic en `Add server`
5. Rellena con lo siguiente:
    ```
    Name: stata-mcp
    Command to launch: uvx
    Arguments: stata-mcp
    ```
6. Haz clic en `Save`
7. Luego, reinicia tu Codex Desktop y disfrutalo.

#### B. Instalar con Codex CLI
Para el modo CLI, simplemente ejecuta el siguiente comando en tu terminal
```bash
uvx stata-mcp install -c codex
```

O usa
```bash
codex mcp add stata-mcp -- uvx stata-mcp
```

### Otros clientes
> Configuracion estandar requerida: asegurate de que Stata este instalado en la ruta predeterminada, y que la CLI de Stata (para macOS y Linux) exista.

La configuracion JSON estandar es la siguiente, puedes personalizar tu configuracion agregando variables de entorno.
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

Para obtener informacion de uso mas detallada, visita la [guia de uso](https://sepinetam.github.io/mcp-for-stata/usage).

### Requisitos previos
- [uv](https://github.com/astral-sh/uv) - Instalador de paquetes y gestor de entornos virtuales
- Claude Code, Codex, OpenClaw u otros Agentes
- Licencia de Stata
- Tu API-KEY de LLM

Si deseas verificar si tu dispositivo es compatible, puedes ejecutar:
```bash
uvx stata-mcp doctor
```

Muestra informacion basica sobre tu dispositivo y verifica si tu configuracion es compatible.

<details>
<summary>Ejemplo de salida</summary>

```
stata-mcp v1.17.0 — Doctor Report

  [PASS] os: macOS (Darwin 25.3.0, arm64)
  [PASS] python: 3.13.5
  [PASS] uv: uv 0.11.13
  [PASS] dependencies: all required packages available
  [PASS] stata_cli: /usr/local/bin/stata-mp (from env)
  [PASS] stata_execution: OK (0.1s)
  [PASS] config: /Users/sepinetam/.statamcp/config.toml (loaded)
  [PASS] working_dir: /Users/sepinetam/Documents/Github/stata-mcp (writable)
  [PASS] guard: enabled, loaded 27 rules
  [PASS] monitor: disabled (psutil available)
  [PASS] pypi: reachable (4.86s)
  [PASS] cleanup: 0 old files (0 B) found; cleanup disabled (CLEAN_LOG_DAYS=-1)

Summary: 12 passed, 0 failed, 0 warning(s), 0 skipped
```

</details>

> Notas:
> 1. Si te encuentras en China y la descarga de paquetes es lenta, consulta la [solucion](docs/troubleshooting.md#package-download-is-slow-or-fails).
> 2. Claude es la mejor opcion para MCP-for-Stata, para usuarios de chino, recomiendo usar DeepSeek como proveedor de modelo ya que es economico y potente, ademas tiene la puntuacion mas alta entre los proveedores de China, si te interesa, visita el reporte [How to use StataMCP improve your social science research](https://statamcp.com/reports/2025/09/21/stata_mcp_a_research_report_on_ai_assisted_empirical_research).

## Comparacion

Existen varios proyectos MCP relacionados con Stata. La tabla siguiente fue generada por Claude Code despues de analizar directamente cada base de codigo.

| Caracteristica            | MCP-for-Stata (este) | haoyu-haoyu/stata-ai-fusion | hanlulong/stata-mcp | tmonk/mcp-stata |
|---|---|---|---|---|
| **Mejor para** | Analisis impulsado por agentes (Claude Code, Codex, OpenClaw) | Sesiones interactivas, exportacion de graficos y conocimiento curado de Stata | Usuarios que escriben y ejecutan codigo Stata dentro de VSCode ellos mismos | Flujos de trabajo de investigacion (replicacion, robustez, QA de publicacion) |
| **Agentes** | Todos | Todos | La ventana de VSCode debe permanecer activa | Todos |
| **Tipo** | Servidor MCP + toolkit CLI | Servidor MCP + Skill KB + Extension de VS Code | Extension de VSCode (servidor localhost, no MCP independiente) | Servidor MCP basado en sesiones |
| **Ejecucion** | do-file via subprocess | Sesion interactiva pexpect + respaldo por lotes | Ejecutor integrado en IDE via localhost :4000 | pystata (Stata 17+) |
| **Seguridad** | Guardia de comandos + monitor de RAM | Cancelar comando + limpieza de sesion | — | — |
| **Analisis de datos** | Manejadores CSV, DTA, XLSX, SPSS | `inspect_data` / `codebook` en sesion | — | `describe` / `codebook` en sesion |
| **Registros** | Lectores de texto + SMCL | `search_log` en sesion | — | Lector de registros integrado |
| **Graficos** | — | Deteccion automatica + `export_graph` PNG/SVG/PDF | — | Exportar, cache, SVG/PNG |
| **Soporte CLI** | Nativo (mismas herramientas que el servidor MCP) | Punto de entrada basico | — | — |
| **Sesiones** | — | Multiples sesiones nombradas con tiempo de espera de inactividad | — | Multi-sesion, tareas en segundo plano |
| **Plugin de IDE** | — | Extension nativa VS Code / Cursor | VSCode / Cursor nativo | Stata Workbench (VS Code) |
| **Skill / Conocimiento** | Skill centrada en herramientas para MCP-for-Stata (742 lineas) | Base de conocimiento general de Stata de 5,653 lineas | — | Mas de 20 skills especializadas de investigacion (inferencia causal, replicacion, QA de publicacion, etc.) |
| **Instalacion** | `uvx stata-mcp install` | `uvx --from stata-ai-fusion stata-ai-fusion` | VS Code Marketplace | `uvx` o script de instalacion |

## 📝 Documentacion
> Los documentos de MCP-for-Stata estan en https://sepinetam.github.io/mcp-for-stata

### Documentacion principal
- **[Documentacion completa](https://sepinetam.github.io/mcp-for-stata/)**: Sitio de documentacion completo con todas las funcionalidades
- **[Guia de configuracion](https://sepinetam.github.io/mcp-for-stata/configuration)**: Sistema de configuracion unificado basado en TOML
- **[Guardia de seguridad](https://sepinetam.github.io/mcp-for-stata/security)**: Validacion de seguridad para comandos peligrosos
- **[Sistema de monitoreo](https://sepinetam.github.io/mcp-for-stata/monitoring)**: Monitoreo de RAM y limites de recursos
- **[Vision general de la arquitectura](https://sepinetam.github.io/mcp-for-stata/overview)**: Diseno del sistema y patrones de integracion

### Caracteristicas clave
- **[Guardia de seguridad](https://sepinetam.github.io/mcp-for-stata/security)**: Bloquea comandos peligrosos (`!`, `shell`, `erase`, etc.)
- **[Monitoreo de RAM](https://sepinetam.github.io/mcp-for-stata/monitoring)**: Previene el agotamiento de memoria con limites configurables
- **[Configuracion unificada](https://sepinetam.github.io/mcp-for-stata/configuration)**: Configuracion TOML + variables de entorno
- Soporte multiplataforma (macOS, Windows, Linux)
- Captura automatica de registros y reporte de errores

## 🐛 Reportar problemas
Si encuentras algun error o tienes solicitudes de funcionalidades, por favor [abre un issue](https://github.com/sepinetam/mcp-for-stata/issues/new).

## 📄 Licencia
[Licencia Publica General Affero de GNU v3.0](LICENSE)

## 📚 Citacion
Si usas MCP-for-Stata en tu investigacion y realmente te ayuda, puedes citar este repositorio usando uno de los siguientes formatos:

### BibTeX
```bibtex
@software{sepinetam2025stata,
  author = {Song Tan},
  title = {MCP-for-Stata: Integrate Stata into your agent},
  year = {2025},
  url = {https://github.com/sepinetam/mcp-for-stata},
  version = {1.18.0}
}
```

### APA
```
Song Tan. (2025). MCP-for-Stata: Integrate Stata into your agent (Version 1.18.0) [Computer software]. https://github.com/sepinetam/mcp-for-stata
```

### Chicago
```
Song Tan. 2025. "MCP-for-Stata: Integrate Stata into your agent." Version 1.18.0. https://github.com/sepinetam/mcp-for-stata.
```

## 📬 Contacto
Correo electronico: [sepinetam@gmail.com](mailto:sepinetam@gmail.com)

O contribuye directamente enviando un [Pull Request](https://github.com/sepinetam/mcp-for-stata/pulls)! Damos la bienvenida a contribuciones de todo tipo, desde correcciones de errores hasta nuevas funcionalidades.

## 📃 Declaracion
Stata es una marca registrada de [StataCorp LLC](https://www.stata.com/company/). Este proyecto (MCP-for-Stata) es una herramienta de codigo abierto independiente y no esta afiliada, respaldada ni patrocinada por StataCorp LLC. Este proyecto no distribuye el software Stata, su codigo fuente ni ningun paquete de instalacion. Los usuarios deben comprar e instalar de forma independiente una copia con licencia valida de Stata de StataCorp LLC o de sus distribuidores autorizados.

Este proyecto esta licenciado bajo [AGPL-3.0](LICENSE). Los mantenedores del proyecto no aceptan responsabilidad alguna por cualquier perdida o daño que surja unicamente del uso del codigo o la documentacion de este proyecto.

Mas informacion: consulta la version en chino en [README.zh-CN.md](README.zh-CN.md); en caso de cualquier conflicto, prevalecera la version en chino.

## ✨ Historial de estrellas

[![Star History Chart](https://api.star-history.com/svg?repos=sepinetam/stata-mcp&type=Date)](https://www.star-history.com/#sepinetam/stata-mcp&Date)
