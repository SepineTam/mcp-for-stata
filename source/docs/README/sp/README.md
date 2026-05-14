<h1 align="center">
  <a href="https://www.statamcp.com">
    <img src="https://example-data.statamcp.com/logo_with_name.jpg" alt="logo" width="300"/>
  </a>
</h1>

<h1 align="center">Stata-MCP</h1>

<p align="center"> Deja que LLM te ayude a realizar tu análisis de regresión con Stata. ✨</p>

[![en](https://img.shields.io/badge/lang-English-red.svg)](../../../../README.md)
[![cn](https://img.shields.io/badge/语言-中文-yellow.svg)](../cn/README.md)
[![fr](https://img.shields.io/badge/langue-Français-blue.svg)](../fr/README.md)
[![sp](https://img.shields.io/badge/Idioma-Español-green.svg)](README.md)
[![PyPI version](https://img.shields.io/pypi/v/stata-mcp.svg)](https://pypi.org/project/stata-mcp/)
[![PyPI Downloads](https://static.pepy.tech/badge/stata-mcp)](https://pepy.tech/projects/stata-mcp)
[![License: AGPL 3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](../../../../LICENSE)
[![Issue](https://img.shields.io/badge/Issue-report-green.svg)](https://github.com/sepinetam/stata-mcp/issues/new)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/SepineTam/stata-mcp)

---
**Notes**: While we strive to make open source accessible to everyone, we regret that we can no longer maintain the Apache-2.0 License. Due to individuals directly copying this project and claiming to be its maintainers, we have decided to change the license to AGPL-3.0 to prevent misuse of the project in ways that go against our original vision.

**Notes**: 尽管我们希望尽可能让所有人都能从开源中获益，但我们很遗憾地宣布无法继续保持 Apache-2.0 License。由于有人直接抄袭本项目并标榜其为项目维护者，我们不得不将 License 更改为 AGPL-3.0，以防止有人滥用本项目进行违背项目初心的事情。

<details>
<summary>Reason</summary>

**Background**: @jackdark425's [repository](https://github.com/jackdark425/aigroup-stata-mcp) directly copied this project and claimed to be the sole maintainer. We welcome open source collaboration based on forks, including but not limited to adding new features, fixing existing bugs, or providing valuable suggestions for the project, but we firmly oppose plagiarism and false attribution.

**Update**: The infringing project has been taken down via GitHub DMCA. Click [here](https://github.com/github/dmca/blob/master/2025/12/2025-12-30-stata-mcp.md) to learn about.

**背景**: @jackdark425 的[仓库](https://github.com/jackdark425/aigroup-stata-mcp)直接抄袭了本项目并标榜为项目唯一维护者。我们欢迎基于fork的开源协作，包括但不限于添加新的feature、修改已有bug或对项目提出您宝贵的意见，但坚决反对抄袭和虚假署名行为。

**更新**: 侵权项目已通过GitHub DMCA被takedown，点击[这里](https://github.com/github/dmca/blob/master/2025/12/2025-12-30-stata-mcp.md)查看详情。

</details>

---
**Novedades**:
- 🦞 **Soporte OpenClaw** : Herramientas CLI independientes para la integración OpenClaw (`stata-mcp tool`), vea [guía OpenClaw](https://docs.statamcp.com/agents/openclaw.md)
- ✨ **Soporte de Plugin Claude Code** : Paquete de plugin oficial con integración de servidor MCP y Stata LSP
- Use Stata-MCP en Claude Code, mire [aquí](#avanzado---claude-code)

> ¿Buscando nuestras **investigaciones más recientes** ? Haga clic [aquí](../../../reports/README.md) o visite el [sitio de informes](https://www.statamcp.com/reports).

<details>
<summary>¿Buscando otros?</summary>

> **MCP o IA sobre Stata**
> - Un servidor MCP basado en sesión para Stata, [mcp-stata](https://github.com/tmonk/mcp-stata)
> - Una integración VScode o Cursor [aquí](https://github.com/hanlulong/stata-mcp). ¿Confundido? 💡 [Comparación](#comparación)
>
> **Conjuntos de datos e Información**
> - [STOP Dataset](https://opendata.ai4cssci.com) : Proyecto Opendata StataMCP-Team 📊, hemos open-sourceado una colección completa de conjuntos de datos para la investigación en ciencias sociales, con el objetivo de permitir el futuro de los paradigmas de investigación impulsados por IA y basados en datos.
> - [Trace DID](https://github.com/asjadnaqvi/DiD) : Si quieres obtener la información más reciente sobre DID (Difference-in-Difference), haz clic [aquí](https://asjadnaqvi.github.io/DiD/). Ahora hay una traducción española por [Sepine Tam](https://github.com/sepine) y [StataMCP-Team](https://github.com/statamcp-team) 🎉
> - Uso en Jupyter Lab (Importante : Stata 17+) [aquí](../../JupyterStata.md) y [nbstata](https://github.com/hugetim/nbstata)
</details>

## 💡 Inicio Rápido
### Instalar para todos los agentes
Si no quieres pasar por una configuración complicada, simplemente ejecuta el siguiente comando :
```bash
uvx stata-mcp install --all
```

<details>
<summary>Agentes soportados 🤖</summary>
Basado en nuestra propia experiencia y pruebas, recomendamos usar Claude Code, Codex y OpenClaw.
Hemos encontrado que Claude y DeepSeek son los dos mejores modelos en cualquier framework.

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

Si no tienes `uv`, visita [aquí](https://docs.astral.sh/uv/getting-started/installation) para instalarlo.
O, usa nuestro script de instalación beta (instala automáticamente `uv` si falta) :

**macOS / Linux :**
```bash
curl -fsSL https://raw.githubusercontent.com/SepineTam/stata-mcp/master/scripts/install.sh | bash
```

**Windows (PowerShell) :**
```powershell
irm https://raw.githubusercontent.com/SepineTam/stata-mcp/master/scripts/install.ps1 | iex
```

### Avanzado - Claude Code
Como encontramos que Claude Code es el mejor agente para Stata-MCP gracias a sus perfectas capacidades agenticas, recomendamos usarlo, y hay muchos usos avanzados siguientes :

Antes de usarlo, asegúrate de haber instalado `Claude Code`, si no sabes cómo instalarlo, visita [GitHub](https://github.com/anthropics/claude-code)

Generalmente, puedes instalar Stata-MCP globalmente una vez, ejecuta :
```bash
claude mcp add stata-mcp --scope user -- uvx stata-mcp
```

Luego, no necesitarás ocuparte de ello nuevamente.

<details>
<summary>Local y compartir con tus socios</summary>

Si quieres instalarlo localmente solo para un cierto espacio de trabajo, puedes ir a tu directorio de trabajo, luego ejecuta :
```bash
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope local -- uvx --directory $(pwd) stata-mcp
```

No pasará nada, puedes escribir `claude` y teclear `/mcp` para encontrar el estado.

Además, la colaboración es una parte esencial de la investigación. Puedes compartir tu configuración MCP con tus coautores usando :
```bash
claude mcp add stata-mcp --scope project -- uvx stata-mcp
```

En tu directorio de trabajo, puedes encontrar un archivo llamado `.mcp.json`, tu configuración mcp se colocará aquí.

</details>

Luego, puedes usar Stata-MCP en Claude Code. Aquí hay algunos escenarios de uso :

- **Replicación de artículos** : Replicar estudios empíricos de artículos de economía
- **Prueba rápida de hipótesis** : Validar hipótesis económicas mediante análisis de regresión
- **Asistente de aprendizaje Stata** : Aprender econometría con explicaciones Stata paso a paso
- **Organización de código** : Revisar y optimizar do-files Stata existentes
- **Interpretación de resultados** : Comprender salidas estadísticas complejas y resultados de regresión

Si usas Claude Code dentro de IDEs (ya sea el terminal integrado o la Extensión Claude Code), instala nuestro plugin incluyendo [Stata-MCP](https://github.com/sepinetam/stata-mcp) y [Stata LSP](https://github.com/euglevi/stata-language-server) mantenido por @euglevi.

```bash
# Agregar el marketplace Stata-MCP
claude plugin marketplace add SepineTam/stata-mcp

# Instalar el plugin en el alcance local, project o user
claude plugin install stata-toolbox -s project
```

> El servidor de lenguaje da al código Stata generado por IA una mejor conciencia sintáctica y completado, lo que mejora la calidad de salida. Empaquetamos el LSP en cumplimiento con su licencia y damos atribución completa al autor original.

### Otros clientes
> Configuración estándar requerida : asegúrate de que Stata esté instalado en la ruta predeterminada y que la interfaz cli de Stata (para macOS y Linux) exista.

La configuración json estándar es la siguiente, puedes personalizar tu configuración mediante la adición de variables de entorno.
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

Para información de uso más detallada, visita la [guía de uso](https://docs.statamcp.com/usage).

### Requisitos previos
- [uv](https://github.com/astral-sh/uv) - Instalador de paquetes y gestor de entornos virtuales
- Claude Code, Codex, OpenClaw u otros Agents
- Licencia de Stata
- Tu API-KEY de LLM

Si quieres verificar si tu dispositivo es compatible, puedes ejecutar :
```bash
uvx stata-mcp doctor
```

Muestra información básica sobre tu dispositivo y verifica si tu configuración es compatible.

<details>
<summary>Ejemplo de salida</summary>

```
stata-mcp v1.16.3 — Doctor Report

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

> Notas :
> 1. Si te encuentras en China, puedes encontrar un breve documento de uso de uv [aquí](../../ChinaUsers/uv.md).
> 2. Claude es la mejor opción para Stata-MCP, para usuarios chinos, recomiendo usar DeepSeek como proveedor de modelos ya que es económico y potente, y su puntuación es la más alta entre los proveedores chinos, si estás interesado, visita el informe [How to use StataMCP improve your social science research](https://statamcp.com/reports/2025/09/21/stata_mcp_a_research_report_on_ai_assisted_empirical_research).

## Comparación

Existen varios proyectos MCP relacionados con Stata. La tabla siguiente fue generada por Claude Code después de analizar directamente cada codebase.

| Característica | Stata-MCP (este proyecto) | hanlulong/stata-mcp | tmonk/mcp-stata |
|---|---|---|---|
| **Agents** | Todos | Ventana VSCode debe permanecer activa | Todos |
| **Tipo** | Servidor MCP + caja de herramientas CLI | Extensión VSCode (servidor local, MCP no autónomo) | Servidor MCP basado en sesión |
| **Ejecución** | do-file vía subprocess | Ejecutor IDE integrado vía localhost :4000 | pystata (Stata 17+) |
| **Seguridad** | Guardia de comando + monitor RAM | — | — |
| **Análisis de datos** | Manejadores CSV, DTA, XLSX, SPSS | — | `describe` / `codebook` en sesión |
| **Logs** | Lectores texto + SMCL | — | Lector de logs integrado |
| **Gráficos** | — | — | Exportar, caché, SVG/PNG |
| **Soporte CLI** | Nativo (mismas herramientas que el servidor MCP) | — | — |
| **Sesiones** | — | — | Multi-sesión, tareas en segundo plano |
| **Plugin IDE** | — | VSCode / Cursor nativo | Stata Workbench (VS Code) |
| **Instalación** | `uvx stata-mcp install` | VS Code Marketplace | `uvx` o script de instalación |
| **Mejor para** | Análisis impulsado por agente (Claude Code, Codex, OpenClaw) | Usuarios que escriben y ejecutan código Stata en VSCode ellos mismos | Flujos de trabajo de investigación (replicación, robustez, QA publicación) |

## 📝 Documentación
> Documentos Stata-MCP visita https://docs.statamcp.com

### Documentación principal
- **[Documentación completa](https://docs.statamcp.com/)** : Sitio de documentación completo con todas las funcionalidades
- **[Guía de configuración](https://docs.statamcp.com/configuration)** : Sistema de configuración unificado basado en TOML
- **[Security Guard](https://docs.statamcp.com/security)** : Validación de seguridad para comandos peligrosos
- **[Sistema de monitoreo](https://docs.statamcp.com/monitoring)** : Monitoreo RAM y límites de recursos
- **[Visión general de la arquitectura](https://docs.statamcp.com/overview)** : Diseño de sistema y patrones de integración

### Características clave
- **[Security Guard](https://docs.statamcp.com/security)** : Bloquea comandos peligrosos (`!`, `shell`, `erase`, etc.)
- **[Monitoreo RAM](https://docs.statamcp.com/monitoring)** : Previene el agotamiento de memoria con límites configurables
- **[Configuración unificada](https://docs.statamcp.com/configuration)** : Configuración TOML + variables de entorno
- Soporte multiplataforma (macOS, Windows, Linux)
- Captura automática de logs y reporte de errores

## 🐛 Reportar problemas
Si encuentras algún error o tienes solicitudes de funcionalidades, por favor [abre un issue](https://github.com/sepinetam/stata-mcp/issues/new).

## 📄 Licencia
[GNU Affero General Public License v3.0](../../../../LICENSE)

## 📚 Cita
Si utilizas Stata-MCP en tu investigación, por favor cita este repositorio utilizando uno de los siguientes formatos:

### BibTeX
```bibtex
@software{sepinetam2025stata,
  author = {Song Tan},
  title = {Stata-MCP: Let LLM help you achieve your regression analysis with Stata},
  year = {2025},
  url = {https://github.com/sepinetam/stata-mcp},
  version = {1.13.0}
}
```

### APA
```
Song Tan. (2025). Stata-MCP: Let LLM help you achieve your regression analysis with Stata (Version 1.13.0) [Computer software]. https://github.com/sepinetam/stata-mcp
```

### Chicago
```
Song Tan. 2025. "Stata-MCP: Let LLM help you achieve your regression analysis with Stata." Version 1.13.0. https://github.com/sepinetam/stata-mcp.
```

## 📬 Contacto
Correo electrónico : [sepinetam@gmail.com](mailto:sepinetam@gmail.com)

¡O contribuye directamente enviando un [Pull Request](https://github.com/sepinetam/stata-mcp/pulls)! Damos la bienvenida a contribuciones de todo tipo, desde correcciones de errores hasta nuevas funcionalidades.

## ❤️ Agradecimientos
El autor agradece sinceramente al equipo oficial de Stata por su apoyo y a la Licencia Stata por autorizar el desarrollo de la prueba.

## 📃 Declaración
El Stata mencionado en este proyecto es el software comercial Stata desarrollado por [StataCorp LLC](https://www.stata.com/company/). Este proyecto no está afiliado, asociado ni patrocinado por StataCorp LLC. Este proyecto no incluye el software Stata ni sus paquetes de instalación ; los usuarios deben obtener e instalar una copia de Stata con licencia válida de StataCorp. Este proyecto está bajo licencia [AGPL-3.0](../../../../LICENSE). Los mantenedores del proyecto no aceptan ninguna responsabilidad por cualquier pérdida o daño resultante del uso de este proyecto o de acciones relacionadas con Stata.

## ✨ Historial de Estrellas

[![Star History Chart](https://api.star-history.com/svg?repos=sepinetam/stata-mcp&type=Date)](https://www.star-history.com/#sepinetam/stata-mcp&Date)
