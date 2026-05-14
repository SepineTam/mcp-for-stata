<h1 align="center">
  <a href="https://www.statamcp.com">
    <img src="https://example-data.statamcp.com/logo_with_name.jpg" alt="logo" width="300"/>
  </a>
</h1>

<h1 align="center">Stata-MCP</h1>

<p align="center"> Laissez les modèles de langage (LLM) vous aider à réaliser vos analyses de régression avec Stata. ✨</p>

[![en](https://img.shields.io/badge/lang-English-red.svg)](../../../../README.md)
[![cn](https://img.shields.io/badge/语言-中文-yellow.svg)](../cn/README.md)
[![fr](https://img.shields.io/badge/langue-Français-blue.svg)](README.md)
[![sp](https://img.shields.io/badge/Idioma-Español-green.svg)](../sp/README.md)
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
**Nouvelles**:
- 🦞 **Support OpenClaw** : Outils CLI autonomes pour l'intégration OpenClaw (`stata-mcp tool`), voir [guide OpenClaw](https://docs.statamcp.com/agents/openclaw.md)
- ✨ **Support Plugin Claude Code** : Package plugin officiel avec intégration serveur MCP et Stata LSP
- Utilisez Stata-MCP dans Claude Code, regardez [ici](#avancé---claude-code)

> Vous cherchez nos **dernières recherches** ? Cliquez [ici](../../../reports/README.md) ou visitez le [site de rapports](https://www.statamcp.com/reports).

<details>
<summary>Vous cherchez d'autres ?</summary>

> **MCP ou IA sur Stata**
> - Un serveur MCP basé sur session pour Stata, [mcp-stata](https://github.com/tmonk/mcp-stata)
> - Une intégration VScode ou Cursor [ici](https://github.com/hanlulong/stata-mcp). Confus ? 💡 [Comparaison](#comparaison)
>
> **Jeux de données et Informations**
> - [STOP Dataset](https://opendata.ai4cssci.com) : Projet Opendata StataMCP-Team 📊, nous avons open-sourcé une collection complète de jeux de données pour la recherche en sciences sociales, visant à permettre l'avenir des paradigmes de recherche pilotés par l'IA et alimentés par les données.
> - [Trace DID](https://github.com/asjadnaqvi/DiD) : Si vous voulez récupérer les informations les plus récentes sur DID (Difference-in-Difference), cliquez [ici](https://asjadnaqvi.github.io/DiD/). Il y a maintenant une traduction française par [Sepine Tam](https://github.com/sepine) et [StataMCP-Team](https://github.com/statamcp-team) 🎉
> - Utilisation de Jupyter Lab (Important : Stata 17+) [ici](../../JupyterStata.md) et [nbstata](https://github.com/hugetim/nbstata)
</details>

## 💡 Démarrage Rapide
### Installer pour tous les agents
Si vous ne voulez pas passer par une configuration compliquée, exécutez simplement la commande suivante :
```bash
uvx stata-mcp install --all
```

<details>
<summary>Agents supportés 🤖</summary>
Basé sur notre propre expérience et nos tests, nous recommandons d'utiliser Claude Code, Codex et OpenClaw.
Nous avons constaté que Claude et DeepSeek sont les deux meilleurs modèles quel que soit le framework.

| Agent                     | Tag      | Commande                          |
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

Si vous n'avez pas `uv`, visitez [ici](https://docs.astral.sh/uv/getting-started/installation) pour l'installer.
Ou, utilisez notre script d'installation bêta (installe automatiquement `uv` s'il manque) :

**macOS / Linux :**
```bash
curl -fsSL https://raw.githubusercontent.com/SepineTam/stata-mcp/master/scripts/install.sh | bash
```

**Windows (PowerShell) :**
```powershell
irm https://raw.githubusercontent.com/SepineTam/stata-mcp/master/scripts/install.ps1 | iex
```

### Avancé - Claude Code
Comme nous trouvons que Claude Code est le meilleur agent pour Stata-MCP grâce à ses capacités agentiques parfaites, nous recommandons de l'utiliser, et il y a beaucoup d'utilisations avancées suivantes :

Avant de l'utiliser, assurez-vous d'avoir installé `Claude Code`, si vous ne savez pas comment l'installer, visitez [GitHub](https://github.com/anthropics/claude-code)

Généralement, vous pouvez installer Stata-MCP globalement une fois, exécutez :
```bash
claude mcp add stata-mcp --scope user -- uvx stata-mcp
```

Ensuite, vous n'aurez plus besoin de vous en occuper.

<details>
<summary>Local et partager avec vos partenaires</summary>

Si vous voulez l'installer localement uniquement pour un certain espace de travail, vous pouvez vous rendre dans votre répertoire de travail, puis exécutez :
```bash
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope local -- uvx --directory $(pwd) stata-mcp
```

Il ne se passera rien, vous pouvez taper `claude` et saisir `/mcp` pour trouver le statut.

De plus, la collaboration est une partie essentielle de la recherche. Vous pouvez partager votre configuration MCP avec vos co-auteurs en utilisant :
```bash
claude mcp add stata-mcp --scope project -- uvx stata-mcp
```

Dans votre répertoire de travail, vous pouvez trouver un fichier nommé `.mcp.json`, votre configuration mcp sera placée ici.

</details>

Ensuite, vous pouvez utiliser Stata-MCP dans Claude Code. Voici quelques scénarios d'utilisation :

- **Réplication d'article** : Répliquer des études empiriques à partir d'articles d'économie
- **Test rapide d'hypothèse** : Valider des hypothèses économiques par analyse de régression
- **Assistant d'apprentissage Stata** : Apprendre l'économétrie avec des explications Stata étape par étape
- **Organisation de code** : Réviser et optimiser les do-files Stata existants
- **Interprétation de résultats** : Comprendre les sorties statistiques complexes et les résultats de régression

Si vous utilisez Claude Code dans des IDEs (que ce soit le terminal intégré ou l'Extension Claude Code), installez notre plugin incluant [Stata-MCP](https://github.com/sepinetam/stata-mcp) et [Stata LSP](https://github.com/euglevi/stata-language-server) maintenu par @euglevi.

```bash
# Ajouter le marketplace Stata-MCP
claude plugin marketplace add SepineTam/stata-mcp

# Installer le plugin dans la portée local, project ou user
claude plugin install stata-toolbox -s project
```

> Le serveur de langage donne au code Stata généré par l'IA une meilleure conscience syntaxique et complétion, ce qui améliore la qualité de sortie. Nous empaquetons le LSP en conformité avec sa licence et donnons une attribution complète à l'auteur original.

### Autres clients
> Configuration standard requise : assurez-vous que Stata est installé sur le chemin par défaut et que l'interface cli de Stata (pour macOS et Linux) existe.

La configuration json standard est la suivante, vous pouvez personnaliser votre configuration via l'ajout de variables d'environnement.
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

Pour plus d'informations d'utilisation détaillées, visitez le [guide d'utilisation](https://docs.statamcp.com/usage).

### Prérequis
- [uv](https://github.com/astral-sh/uv) - Installateur de paquets et gestionnaire d'environnements virtuels
- Claude Code, Codex, OpenClaw ou autres Agents
- Licence Stata
- Votre API-KEY de LLM

Si vous voulez vérifier si votre appareil est pris en charge, vous pouvez exécuter :
```bash
uvx stata-mcp doctor
```

Il affiche des informations de base sur votre appareil et vérifie si votre configuration est prise en charge.

<details>
<summary>Exemple de sortie</summary>

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

> Notes :
> 1. Si vous êtes situé en Chine, un court document d'utilisation d'uv est disponible [ici](../../ChinaUsers/uv.md).
> 2. Claude est le meilleur choix pour Stata-MCP, pour les utilisateurs chinois, je recommande d'utiliser DeepSeek comme fournisseur de modèle car il est peu coûteux et puissant, et son score est le plus élevé parmi les fournisseurs chinois, si vous êtes intéressé, visitez le rapport [How to use StataMCP improve your social science research](https://statamcp.com/reports/2025/09/21/stata_mcp_a_research_report_on_ai_assisted_empirical_research).

## Comparaison

Il existe plusieurs projets MCP liés à Stata. Le tableau ci-dessous a été généré par Claude Code après analyse directe de chaque codebase.

| Fonctionnalité | Stata-MCP (ce projet) | hanlulong/stata-mcp | tmonk/mcp-stata |
|---|---|---|---|
| **Agents** | Tous | Fenêtre VSCode doit rester active | Tous |
| **Type** | Serveur MCP + boîte à outils CLI | Extension VSCode (serveur local, MCP non autonome) | Serveur MCP basé sur session |
| **Exécution** | do-file via subprocess | Exécuteur IDE intégré via localhost :4000 | pystata (Stata 17+) |
| **Sécurité** | Garde de commande + surveillance RAM | — | — |
| **Analyse de données** | Gestionnaires CSV, DTA, XLSX, SPSS | — | `describe` / `codebook` en session |
| **Logs** | Lecteurs texte + SMCL | — | Lecteur de logs intégré |
| **Graphiques** | — | — | Export, cache, SVG/PNG |
| **Support CLI** | Natif (mêmes outils que le serveur MCP) | — | — |
| **Sessions** | — | — | Multi-session, tâches en arrière-plan |
| **Plugin IDE** | — | VSCode / Cursor natif | Stata Workbench (VS Code) |
| **Installation** | `uvx stata-mcp install` | VS Code Marketplace | `uvx` ou script d'installation |
| **Idéal pour** | Analyse pilotée par agent (Claude Code, Codex, OpenClaw) | Utilisateurs qui écrivent et exécutent du code Stata dans VSCode eux-mêmes | Flux de travail de recherche (réplication, robustesse, QA publication) |

## 📝 Documentation
> Documents Stata-MCP visitez https://docs.statamcp.com

### Documentation principale
- **[Documentation complète](https://docs.statamcp.com/)** : Site de documentation complet avec toutes les fonctionnalités
- **[Guide de configuration](https://docs.statamcp.com/configuration)** : Système de configuration unifié basé sur TOML
- **[Security Guard](https://docs.statamcp.com/security)** : Validation de sécurité pour les commandes dangereuses
- **[Système de surveillance](https://docs.statamcp.com/monitoring)** : Surveillance RAM et limites de ressources
- **[Aperçu de l'architecture](https://docs.statamcp.com/overview)** : Conception système et modèles d'intégration

### Fonctionnalités clés
- **[Security Guard](https://docs.statamcp.com/security)** : Bloque les commandes dangereuses (`!`, `shell`, `erase`, etc.)
- **[Surveillance RAM](https://docs.statamcp.com/monitoring)** : Prévient l'épuisement de mémoire avec des limites configurables
- **[Configuration unifiée](https://docs.statamcp.com/configuration)** : Configuration TOML + variables d'environnement
- Support multiplateforme (macOS, Windows, Linux)
- Capture automatique de logs et rapport d'erreurs

## 🐛 Signaler des Problèmes
Si vous rencontrez des bugs ou avez des demandes de fonctionnalités, veuillez [ouvrir un ticket](https://github.com/sepinetam/stata-mcp/issues/new).

## 📄 Licence
[GNU Affero General Public License v3.0](../../../../LICENSE)

## 📚 Citation
Si vous utilisez Stata-MCP dans vos recherches, veuillez citer ce référentiel en utilisant l'un des formats suivants:

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

## 📬 Contact
Email : [sepinetam@gmail.com](mailto:sepinetam@gmail.com)

Ou contribuez directement en soumettant une [Pull Request](https://github.com/sepinetam/stata-mcp/pulls) ! Nous accueillons les contributions de toutes sortes, des corrections de bugs aux nouvelles fonctionnalités.

## ❤️ Remerciements
L'auteur remercie sincèrement l'équipe officielle de Stata pour son soutien et la licence Stata pour avoir autorisé le développement du test.

## 📃 Déclaration
Le Stata mentionné dans ce projet est le logiciel commercial Stata développé par [StataCorp LLC](https://www.stata.com/company/). Ce projet n'est pas affilié, associé ou parrainé par StataCorp LLC. Ce projet n'inclut pas le logiciel Stata ou ses packages d'installation ; les utilisateurs doivent obtenir et installer une copie Stata sous licence valide auprès de StataCorp. Ce projet est sous licence [AGPL-3.0](../../../../LICENSE). Les mainteneurs du projet n'acceptent aucune responsabilité pour toute perte ou dommage résultant de l'utilisation de ce projet ou d'actions liées à Stata.

## ✨ Histoire des étoiles

[![Star History Chart](https://api.star-history.com/svg?repos=sepinetam/stata-mcp&type=Date)](https://www.star-history.com/#sepinetam/stata-mcp&Date)
