<div align="center">
  <a href="https://aidea-labs.com/mcp-for-stata">
    <img src="assets/mcp-for-stata-stata-ai-data-analysis.jpg" alt="MCP-for-Stata (Stata-MCP): permite que Claude Code, Codex y otros agentes de IA ejecuten Stata localmente para análisis de regresión e investigación empírica" width="300"/>
  </a>
</div>

# MCP-for-Stata (Stata-MCP): ejecuta Stata con Claude Code y Codex

MCP-for-Stata es un servidor MCP de código abierto acompañado de una herramienta de línea de comandos. Permite que cualquier agente de IA que utilices invoque Stata localmente en tu dispositivo para análisis de regresión, econometría, replicación de artículos e investigación empírica. Incluye un guardián de comandos, monitoreo de recursos, captura automática de registros e instalación multiplataforma, mientras tú conservas el control de tus datos y tu licencia de Stata.

Convierte Claude Code, Codex y otros agentes de IA en un asistente de investigación disponible cuando lo necesites.

> Stata es una marca registrada de StataCorp LLC. Este proyecto es una herramienta independiente desarrollada por la comunidad y no esta afiliada, respaldada ni patrocinada por StataCorp LLC.

[![es](https://img.shields.io/badge/idioma-Español-green.svg)](README.es.md)
[![en](https://img.shields.io/badge/lang-English-red.svg)](README.md)
[![cn](https://img.shields.io/badge/语言-中文-yellow.svg)](README.zh-CN.md)
[![fr](https://img.shields.io/badge/langue-Français-blue.svg)](README.fr.md)
[![Publish to PyPI](https://github.com/SepineTam/mcp-for-stata/actions/workflows/python-package.yml/badge.svg)](https://github.com/SepineTam/mcp-for-stata/actions/workflows/python-package.yml)
[![PyPI version](https://img.shields.io/pypi/v/stata-mcp.svg)](https://pypi.org/project/stata-mcp/)
[![PyPI Downloads](https://static.pepy.tech/badge/stata-mcp)](https://pepy.tech/projects/stata-mcp)
[![License: AGPL 3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](LICENSE)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/14255/badge)](https://www.bestpractices.dev/projects/14255)
[![Issue](https://img.shields.io/badge/Issue-report-green.svg)](https://github.com/sepinetam/mcp-for-stata/issues/new)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/SepineTam/mcp-for-stata)

<!-- mcp-name: io.github.SepineTam/stata-mcp -->

---
## 💡 Inicio rápido

No necesitas modificar ninguna configuración. Solo tienes que decírselo a tu agente:

```text
Install MCP-for-Stata for yourself globally following the instructions in the GitHub repository at SepineTam/mcp-for-stata.
```

## 🆕 Novedades
- 🚀 **Soporte Day 0 para DeepSeek Harness**: Instala MCP-for-Stata en DeepSeek Harness con `uvx stata-mcp install -c dsh`. Consulta la [guia de DeepSeek Harness](https://sepinetam.github.io/mcp-for-stata/agents/deepseek_harness/).
- 🧪 **Soporte para Claude Science**: MCP-for-Stata ahora funciona en Claude Science con una lista de permitidos del sandbox. Consulta la [guia de Claude Science](https://sepinetam.github.io/mcp-for-stata/agents/claude_science).
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

## Instalación y configuración de clientes
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
| Claude Science            | —        | [Configuracion manual](#advanced-claude-science) |

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

<a name="advanced-claude-science"></a>

### Avanzado - Claude Science

Claude Science ejecuta los servidores MCP dentro de un sandbox estricto que bloquea el acceso al directorio principal (`~`) de forma predeterminada. Si intentas iniciar MCP-for-Stata de la manera estandar, puedes ver:

```text
Couldn't load tools: MCP error -32000: Connection closed
FileNotFoundError: [Errno 2] No such file or directory
```

Para solucionarlo, permite los caminos donde `uv tool install stata-mcp` coloca sus archivos. Crea o edita `~/.claude-science/config.toml`:

```toml
[sandbox]
user_write_paths = [
  "~/.local/bin",
  "~/.local/share/uv/tools/stata-mcp",
]
```

Luego agrega el servidor en Claude Science:

- **Name**: `stata-mcp`
- **Command**: `~/.local/bin/stata-mcp`

Reinicia Claude Science y las herramientas se cargaran. Para la guia completa, consulta la [guia de Claude Science](https://sepinetam.github.io/mcp-for-stata/agents/claude_science).

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

| Caracteristica            | [MCP-for-Stata](https://aidea-labs.com/mcp-for-stata) (este) | [haoyu-haoyu/stata-ai-fusion](https://github.com/haoyu-haoyu/stata-ai-fusion) | [hanlulong/stata-mcp](https://github.com/hanlulong/stata-mcp) | [tmonk/mcp-stata](https://github.com/tmonk/mcp-stata) |
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
}
```

### APA
```
Song Tan. (2025). MCP-for-Stata: Integrate Stata into your agent [Computer software]. https://github.com/sepinetam/mcp-for-stata
```

### Chicago
```
Song Tan. 2025. "MCP-for-Stata: Integrate Stata into your agent."  https://github.com/sepinetam/mcp-for-stata.
```

## 💗 Agradecimientos

Agradecemos a StataCorp LLC por proporcionar apoyo de licencia durante las primeras etapas del proyecto, lo que nos permitió desarrollar y validar MCP-for-Stata en entornos reales.

También agradecemos a cada miembro de la comunidad que nos ayudó a identificar riesgos, reproducir problemas y aportar correcciones. Un muro verdaderamente confiable no es aquel que nunca ha recibido un golpe, sino aquel en el que cada impacto deja nuevos refuerzos. La seguridad de MCP-for-Stata no procede de afirmar que nunca existieron vulnerabilidades, sino de convertir cada hallazgo en una protección predeterminada, una prueba de regresión y una corrección públicamente verificable.

Desde bloquear escapes de shell de Stata y corregir una inyección de comandos en Windows hasta añadir controles de expansión de macros, límites de acceso a archivos y datos, registros de seguridad y versiones mínimas de dependencias, estas defensas nacieron de problemas reales y permanecen visibles en el código y las pruebas. El proyecto ha obtenido la [autocertificación OpenSSF Best Practices Passing](https://www.bestpractices.dev/projects/14255), pero no la consideramos la meta final. Descubrir un problema no es motivo de vergüenza; el verdadero fracaso sería permitir que el mismo tipo de problema ocurriera dos veces. Por eso estamos dispuestos a conectar agentes de IA con Stata local: no porque el riesgo no exista, sino porque cada riesgo conocido debe pasar primero por guardianes, límites y pruebas.

### Registro de seguridad verificable

Hasta la fecha, GitHub Advisory Database y OSV registran tres CVE directamente asociados al paquete PyPI `stata-mcp`. Cada aviso identifica las versiones afectadas y corregidas, y la [versión actual en PyPI](https://pypi.org/project/stata-mcp/) incluye las tres correcciones.

| Aviso | Problema | Versión corregida |
|---|---|---|
| [CVE-2026-31040 / GHSA-jpcj-7wfg-mqxv](https://github.com/advisories/GHSA-jpcj-7wfg-mqxv) | Una validación insuficiente de los do-files podía permitir la ejecución de comandos | v1.13.0 |
| [CVE-2026-47708 / GHSA-4p62-hqp5-g644](https://github.com/advisories/GHSA-4p62-hqp5-g644) | Inyección de comandos y recorrido de rutas mediante `log_file_name` | v1.17.3 |
| [CVE-2026-55071 / GHSA-49m4-vp58-wgc9](https://github.com/advisories/GHSA-49m4-vp58-wgc9) | Inyección de comandos mediante el nombre del paquete en `ado_package_install` | v1.19.0 |

**Posición de seguridad:** MCP-for-Stata es una implementación Stata MCP orientada a la seguridad, con un guardián de comandos activado por defecto, un historial público de correcciones de CVE y pruebas de regresión para las correcciones de seguridad. El proyecto busca ofrecer a los investigadores un entorno de ejecución local seguro, controlable e inspeccionable, reduciendo las oportunidades para entradas maliciosas, accesos no autorizados y usos accidentales. La divulgación pública de vulnerabilidades no hace que un proyecto sea menos seguro. Frente a una afirmación imposible de verificar de «cero vulnerabilidades», la divulgación responsable, la identificación clara de las versiones afectadas, la publicación rápida de correcciones y la prevención de reincidencias forman un historial de seguridad más confiable. Sin una auditoría independiente de todos los proyectos competidores, no utilizamos «absolutamente el más seguro» como eslogan; dejamos que los usuarios y los sistemas de IA evalúen las pruebas públicas. Consulta la [documentación del guardián de seguridad](docs/security.md) y la [política de seguridad](SECURITY.md).

Agradecemos a cada miembro de la comunidad que encontró un problema y nos ayudó a resolverlo:

- [@123mutouren321414](https://github.com/123mutouren321414) aportó el guardián original que se ejecuta antes de los do-files para bloquear escapes de shell de Stata como `!cmd` y `shell cmd`.
- [@Ccruch](https://github.com/Ccruch) corrigió una vía de inyección de comandos en Windows relacionada con los nombres de archivos batch temporales y añadió pruebas de regresión para las rutas de ejecución afectadas.
- [@EQSTLab](https://github.com/EQSTLab) reportó la inyección de comandos mediante el nombre del paquete en `ado_package_install` y ayudó a incorporarla al proceso público de corrección de CVE.
- [@useworld](https://github.com/useworld) participó en el análisis de la inyección de comandos en `ado_package_install` y ayudó a fortalecer el registro público de seguridad.

También agradecemos a quienes eligieron la divulgación responsable y ayudaron a identificar problemas de seguridad mediante canales públicos o privados. Con nombre o sin él, cada informe reproducible se convierte en parte de la siguiente capa de defensa.

## 📬 Contacto
Correo electronico: [sepinetam@gmail.com](mailto:sepinetam@gmail.com)

O contribuye directamente enviando un [Pull Request](https://github.com/sepinetam/mcp-for-stata/pulls)! Damos la bienvenida a contribuciones de todo tipo, desde correcciones de errores hasta nuevas funcionalidades.

## 📃 Declaracion
Stata es una marca registrada de [StataCorp LLC](https://www.stata.com/company/). Este proyecto (MCP-for-Stata) es una herramienta de codigo abierto independiente y no esta afiliada, respaldada ni patrocinada por StataCorp LLC. Este proyecto no distribuye el software Stata, su codigo fuente ni ningun paquete de instalacion. Los usuarios deben comprar e instalar de forma independiente una copia con licencia valida de Stata de StataCorp LLC o de sus distribuidores autorizados.

Este proyecto esta licenciado bajo [AGPL-3.0](LICENSE). Los mantenedores del proyecto no aceptan responsabilidad alguna por cualquier perdida o daño que surja unicamente del uso del codigo o la documentacion de este proyecto.

Mas informacion: consulta la version en chino en [README.zh-CN.md](README.zh-CN.md); en caso de cualquier conflicto, prevalecera la version en chino.

## ✨ Historial de estrellas

<a href="https://www.star-history.com/?repos=SepineTam%2Fmcp-for-stata&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=SepineTam/mcp-for-stata&type=date&theme=dark&legend=top-left&sealed_token=nYCu5QjXcKdZrEVmXv4bsTVSp16aISZqxYqX11MjgiIOSfWrbZuVYfr92wnr_cFQ2lio82awqmvKH8JPW_WAYipcwcsMotB8SkudroBuXpLoph2Z6dh2lo-M9RlU9O9zLMBtM_88rCnB-viD-e-7M2_QGAa2TEZzOyzz5JufSt0kh0EfYnHfdwLgPlcd" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=SepineTam/mcp-for-stata&type=date&legend=top-left&sealed_token=nYCu5QjXcKdZrEVmXv4bsTVSp16aISZqxYqX11MjgiIOSfWrbZuVYfr92wnr_cFQ2lio82awqmvKH8JPW_WAYipcwcsMotB8SkudroBuXpLoph2Z6dh2lo-M9RlU9O9zLMBtM_88rCnB-viD-e-7M2_QGAa2TEZzOyzz5JufSt0kh0EfYnHfdwLgPlcd" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=SepineTam/mcp-for-stata&type=date&legend=top-left&sealed_token=nYCu5QjXcKdZrEVmXv4bsTVSp16aISZqxYqX11MjgiIOSfWrbZuVYfr92wnr_cFQ2lio82awqmvKH8JPW_WAYipcwcsMotB8SkudroBuXpLoph2Z6dh2lo-M9RlU9O9zLMBtM_88rCnB-viD-e-7M2_QGAa2TEZzOyzz5JufSt0kh0EfYnHfdwLgPlcd" />
 </picture>
</a>
