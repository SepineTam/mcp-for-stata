<h1 align="center">
  <a href="https://www.statamcp.com">
    <img src="https://example-data.statamcp.com/logo_with_name.jpg" alt="logo" width="300"/>
  </a>
</h1>

<h1 align="center">Stata-MCP</h1>

<p align="center"> 
    Let LLM help you achieve your regression analysis with Stata ✨ <br>
    Evolve from reg monkey to causal thinker 🐒 -> 🧐
</p>

[![en](https://img.shields.io/badge/lang-English-red.svg)](README.md)
[![cn](https://img.shields.io/badge/语言-中文-yellow.svg)](source/docs/README/cn/README.md)
[![Publish to PyPI](https://github.com/SepineTam/stata-mcp/actions/workflows/python-package.yml/badge.svg)](https://github.com/SepineTam/stata-mcp/actions/workflows/python-package.yml)
[![Build and Push Docker Images](https://github.com/SepineTam/stata-mcp/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/SepineTam/stata-mcp/actions/workflows/docker-publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/stata-mcp.svg)](https://pypi.org/project/stata-mcp/)
[![PyPI Downloads](https://static.pepy.tech/badge/stata-mcp)](https://pepy.tech/projects/stata-mcp)
[![License: AGPL 3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](LICENSE)
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
**News**:
- ✨ **Claude Code Plugin Support**: Official plugin package with MCP server and Stata LSP integration
- ✨ **Security Guard System**: Automatic validation against dangerous commands (shell execution, file deletion, etc.)
- ✨ **RAM Monitoring System**: Real-time monitoring with automatic process termination when memory limits exceeded
- ✨ **Unified Configuration**: TOML-based config file with environment variable overrides
- 📚 **Complete Documentation**: New [Configuration](docs/configuration.md), [Security](docs/security.md), and [Monitoring](docs/monitoring.md) guides
- Use Stata-MCP in Claude Code, look [here](#use-stata-mcp-in-claude-code)
- Try to use agent mode as tool? Now it is supported more easily [here](source/docs/Usages/agent_as/agent_as_tool.md).
- Want to evaluate your LLM? Look [here](source/docs/Usages/Evaluation.md).
- Update `StataFinder`, it could locate your Stata executable file automatically. 

> Finding our **newest research**? Click [here](source/reports/README.md) or visit [reports website](https://www.statamcp.com/reports).

<details>
<summary>Looking for others?</summary>

> **MCP or AI about Stata**
> - A session based MCP server for Stata, [mcp-stata](https://github.com/tmonk/mcp-stata)
> - A VScode or Cursor integrated [here](https://github.com/hanlulong/stata-mcp). Confused it? 💡 [Difference](source/docs/Difference.md)
> 
> **Datasets and Informations**  
> - [STOP Dataset](https://opendata.ai4cssci.com): StataMCP-Team Opendata Project 📊, we have open-sourced a comprehensive dataset collection for social science research, aiming to enable the future of AI-driven and data-powered research paradigms.  
> - [Trace DID](https://github.com/asjadnaqvi/DiD): If you want to fetch the newest information about DID (Difference-in-Difference), click [here](https://asjadnaqvi.github.io/DiD/). Now there is a Chinese translation by [Sepine Tam](https://github.com/sepine) and [StataMCP-Team](https://github.com/statamcp-team) 🎉
> - Jupyter Lab Usage (Important: Stata 17+) [here](source/docs/JupyterStata.md) and [nbstata](https://github.com/hugetim/nbstata)
</details>

## 💡 Quickly Start
### Use Stata-MCP in Claude Code
We can use Stata-MCP in Claude Code as its prefect agentic ability. 

Before using it, please make sure you have ever install `Claude Code`, if you don't know how to install it, visit on [GitHub](https://github.com/anthropics/claude-code)

You can open your terminal and `cd` to your working directory, and run:
```bash
claude mcp add stata-mcp --env STATA_MCP_CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp
```

In your working directory, you can find a file named `.mcp.json`, your mcp config will be placed here. 

If you want to install Stata-MCP globally, you can run:
```bash
claude mcp add stata-mcp --scope user -- uvx stata-mcp
```

Then, you can use Stata-MCP in Claude Code. Here are some scenarios for using it:

- **Paper Replication**: Replicate empirical studies from economics papers
- **Quick Hypothesis Testing**: Validate economic hypotheses through regression analysis
- **Stata Learning Assistant**: Learn econometrics with step-by-step Stata explanations
- **Code Organization**: Review and optimize existing Stata do-files
- **Result Interpretation**: Understand complex statistical outputs and regression results

### Install Claude Code Plugin
We provide official native plugin, integrating [Stata-MCP](https://github.com/sepinetam/stata-mcp) maintained by @sepinetam and [Stata LSP](https://github.com/euglevi/stata-language-server) maintained by @euglevi. Installation commands:
```bash
# Install stata-mcp marketplace first
claude plugin marketplace add sepinetam/stata-mcp

# Install plugin to local, project or user scope
claude plugin install stata-toolbox -s local
```

### Agent Mode
The details of agent mode find [here](source/agent_examples/README.md).

```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

uv sync
uv pip install -e .

stata-mcp --version  # for test whether stata-mcp is installed successfully.
stata-mcp agent run  # now you can enjoy your stata-mcp agent mode.
```

or you can directly use it with `uvx`:
```bash
uvx stata-mcp --version  # for test whether it could be used on your computer.
uvx stata-mcp agent run
```

You can edit the task in `agent_examples/openai/main.py` for variable `[model_instructions](source/agent_examples/openai/main.py#L37)` and `[task_message](source/agent_examples/openai/main.py#L68)`

### Agent as Tool
If you want to use a Stata-Agent in another agent, [here](source/docs/Usages/agent_as/agent_as_tool.md) is a simple example:

```python
import asyncio

from agents import Agent, Runner
from stata_mcp.agent_as.agent_as_tool import StataAgent

# init stata agent and set as tool
stata_agent = StataAgent()
sa_tool = stata_agent.as_tool()

# Create main Agent
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant",
    tools=[sa_tool],
)


# Then run the agent as usual.
async def main(task: str, max_turns: int = 30):
    result = await Runner.run(agent, input=task, max_turns=max_turns)
    return result


if __name__ == "__main__":
    econ_task = "Use Stata default data to find out the relationship between mpg and price."
    asyncio.run(main(econ_task))

```


### AI Chat-Bot Client Mode
> Standard config requires: please make sure the stata is installed at the default path, and the stata cli (for macOS and Linux) exists.

The standard config json as follows, you can DIY your config via add envs.
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

For more detailed usage information, visit the [Usage guide](source/docs/Usages/Usage.md). 

And some advanced usage, visit the [Advanced guide](source/docs/Usages/Advanced.md)

### Prerequisites
- [uv](https://github.com/astral-sh/uv) - Package installer and virtual environment manager
- Claude, Cline, ChatWise, or other LLM service
- Stata License
- Your API-KEY from LLM

> Notes:
> 1. If you are located in China, a short uv usage document you can find [here](source/docs/ChinaUsers/uv.md).
> 2. Claude is the best choice for Stata-MCP, for Chinese, I recommend to use DeepSeek as your model provider as it is cheap and powerful, also the score is highest in China provider, if you are increased in it, visit the report [How to use StataMCP improve your social science research](https://statamcp.com/reports/2025/09/21/stata_mcp_a_research_report_on_ai_assisted_empirical_research).

### Installation
For the new version, you don't need to install the `stata-mcp` package again, you can just use the following command to check whether your computer can use stata-mcp.
```bash
uvx stata-mcp --usable
uvx stata-mcp --version
```

If you want to use it locally, you can install it via pip or download the source code.

**Download via pip**
```bash
pip install stata-mcp
```

**Download source code and compile**
```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

uv build
```
Then you can find the compiled `stata-mcp` binary in the `dist` directory. You can use it directly or add it to your PATH.

For example:
```bash
uvx /path/to/your/whl/stata_mcp-1.13.0-py3-non-any.whl  # here is the wheel file name, you can change it to your version
```

## 📝 Documentation

### Core Documentation
- **[Complete Documentation](https://docs.statamcp.com/)**: Full documentation site with all features
- **[Configuration Guide](https://docs.statamcp.com/configuration)**: Unified TOML-based configuration system
- **[Security Guard](https://docs.statamcp.com/security)**: Security validation for dangerous commands
- **[Monitoring System](https://docs.statamcp.com/monitoring)**: RAM monitoring and resource limits
- **[Architecture Overview](https://docs.statamcp.com/overview)**: System design and integration patterns

### Usage Guides
- For more detailed usage information, visit the [Usage guide](source/docs/Usages/Usage.md)
- Advanced Usage, visit the [Advanced](source/docs/Usages/Advanced.md)
- Some questions, visit the [Questions](source/docs/Usages/Questions.md)
- Difference with [Stata-MCP@hanlulong](https://github.com/hanlulong/stata-mcp), visit the [Difference](source/docs/Difference.md)

### Key Features
- **[Security Guard](https://docs.statamcp.com/security)**: Blocks dangerous commands (`!`, `shell`, `erase`, etc.)
- **[RAM Monitoring](https://docs.statamcp.com/monitoring)**: Prevents memory exhaustion with configurable limits
- **[Unified Configuration](https://docs.statamcp.com/configuration)**: TOML config + environment variables
- Cross-platform support (macOS, Windows, Linux)
- Automatic log capture and error reporting

## 💡 Questions
- [Cherry Studio 32000 wrong](source/docs/Usages/Questions.md#cherry-studio-32000-wrong)
- [Cherry Studio 32000 error](source/docs/Usages/Questions.md#cherry-studio-32000-error)
- [Windows Support](source/docs/Usages/Questions.md#windows-supports)
- [Network Errors When Running Stata-MCP](source/docs/Usages/Questions.md#network-errors-when-running-stata-mcp)

## 🚀 Roadmap
- [x] macOS support
- [x] Windows support
- [ ] Additional LLM integrations (With a new webUI)
- [ ] Performance optimizations (Via prompt and context engineering)

For more information, refer to the [Statement](source/docs/Rights/Statement.md).

## 🐛 Report Issues
If you encounter any bugs or have feature requests, please [open an issue](https://github.com/sepinetam/stata-mcp/issues/new).

## 📄 License
[GNU Affero General Public License v3.0](LICENSE)

## 📚 Citation
If you use Stata-MCP in your research, please cite this repository using one of the following formats:

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
Email: [sepinetam@gmail.com](mailto:sepinetam@gmail.com)

Or contribute directly by submitting a [Pull Request](https://github.com/sepinetam/stata-mcp/pulls)! We welcome contributions of all kinds, from bug fixes to new features.

## ❤️ Acknowledgements
The author sincerely thanks the Stata official team for their support and the Stata License for authorizing the test development.

## 📃 Statement
The Stata referred to in this project is the commercial software Stata developed by [StataCorp LLC](https://www.stata.com/company/). This project is not affiliated with, endorsed by, or sponsored by StataCorp LLC. This project does not include the Stata software or any installation packages; users must obtain and install a validly licensed copy of Stata from StataCorp. This project is licensed under [AGPL-3.0](LICENSE). The project maintainers accept no liability for any loss or damage arising from the use of this project or from actions related to Stata.

More information: refer to the Chinese version at [source/docs/README/cn/README.md]; in case of any conflict, the Chinese version shall prevail.

## ✨ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=sepinetam/stata-mcp&type=Date)](https://www.star-history.com/#sepinetam/stata-mcp&Date)

