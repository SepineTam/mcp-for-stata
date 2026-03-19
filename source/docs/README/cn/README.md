<h1 align="center">
  <a href="https://www.statamcp.com">
    <img src="https://example-data.statamcp.com/logo_with_name.jpg" alt="logo" width="300"/>
  </a>
</h1>

<h1 align="center">Stata-MCP</h1>

<p align="center"> 
    让大语言模型（LLM）帮助您使用Stata完成回归分析 ✨<br>
    让 reg monkey 进化为 causal thinker 🐒 -> 🧐
</p>

[![en](https://img.shields.io/badge/lang-English-red.svg)](../../../../README.md)
[![cn](https://img.shields.io/badge/语言-中文-yellow.svg)](README.md)
[![fr](https://img.shields.io/badge/langue-Français-blue.svg)](../fr/README.md)
[![sp](https://img.shields.io/badge/Idioma-Español-green.svg)](../sp/README.md)
[![PyPI version](https://img.shields.io/pypi/v/stata-mcp.svg)](https://pypi.org/project/stata-mcp/)
[![PyPI Downloads](https://static.pepy.tech/badge/stata-mcp)](https://pepy.tech/projects/stata-mcp)
[![License: AGPL 3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](../../../../LICENSE)
[![Issue](https://img.shields.io/badge/Issue-report-green.svg)](https://github.com/sepinetam/stata-mcp/issues/new)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/SepineTam/stata-mcp)

---
**Notes**：尽管我们希望尽可能让所有人都能从开源中获益，但我们很遗憾地宣布无法继续保持 Apache-2.0 License。由于有人直接抄袭本项目并标榜其为项目维护者，我们不得不将 License 更改为 AGPL-3.0，以防止有人滥用本项目进行违背项目初心的事情。

**背景**：@jackdark425 的[仓库](https://github.com/jackdark425/aigroup-stata-mcp)直接抄袭了本项目并标榜为项目唯一维护者。我们欢迎基于fork的开源协作，包括但不限于添加新的feature、修改已有bug或对项目提出您宝贵的意见，但坚决反对抄袭和虚假署名行为。

**更新**: 侵权项目已通过GitHub DMCA被takedown，点击[这里](https://github.com/github/dmca/blob/master/2025/12/2025-12-30-stata-mcp.md)查看详情。

---
**新闻**：
- 🦞 **OpenClaw 支持**：独立 CLI 工具用于 OpenClaw 集成（`stata-mcp tool`），详见 [OpenClaw 指南](https://docs.statamcp.com/agents/openclaw.md)
- ✨ **Claude Code 插件支持**：官方插件包，集成 MCP 服务器和 Stata LSP
- 在Claude Code中使用Stata-MCP，请查看[此处](#在claude-code中使用stata-mcp)

> 寻找我们的**最新研究**？点击[此处](../../../reports/README.md)或访问[报告网站](https://www.statamcp.com/reports)。

<details>
<summary>正在寻找其他？</summary>

> - [STOP](https://opendata.ai4cssci.com)：StataMCP-Team 开放数据项目 📊，我们开源了全面的数据集集合用于社会科学研究，旨在实现 AI 驱动和数据赋能的研究范式未来。
> - [追踪 DID](https://github.com/asjadnaqvi/DiD)：如果您想获取关于DID（双重差分法）的最新信息，请点击[此处](https://asjadnaqvi.github.io/DiD/)。现在有[Sepine Tam](https://github.com/sepine)和[StataMCP-Team](https://github.com/statamcp-team)的中文翻译 🎉
> - Jupyter Lab 使用方法（重要提示：Stata 17+）[此处](../../JupyterStata.md)
> - [NBER-MCP](https://github.com/sepinetam/NBER-MCP) & [AER-MCP](https://github.com/sepinetam/AER-MCP) 🔧 建造之下
> - [Econometrics-Agent](https://github.com/FromCSUZhou/Econometrics-Agent)
> - [TexIV](https://github.com/sepinetam/TexIV)：一个基于机器学习的框架，利用先进的NLP和机器学习技术将文本数据转化为可用于实证研究的变量
> - VScode 或 Cursor 集成 [此处](https://github.com/hanlulong/stata-mcp)。搞不清楚？️💡 [区别](../../Difference.md)

</details>

## 💡 快速开始
### 在Claude Code中使用Stata-MCP
我们可以利用Stata-MCP在Claude Code中作为其完美的代理能力。

在使用之前，请确保您已经安装了`Claude Code`，如果您不知道如何安装，请访问[GitHub](https://github.com/anthropics/claude-code)

您可以打开终端并`cd`到您的工作目录，然后运行：
```bash
claude mcp add stata-mcp --env STATA_MCP_CWD=$(pwd) -- uvx stata-mcp
```
我不确定这是否在Windows的电脑上也工作，因为我并没有真的拥有一台Windows电脑用于测试。

然后，您就可以在Claude Code中使用Stata-MCP了。以下是一些使用场景：

- **论文复刻**：通过复刻经济学论文中的实证研究
- **快速验证假设**：通过回归分析验证经济学假设
- **Stata陪伴教学**：通过逐步Stata解释学习计量经济学
- **整理代码**：审查和优化现有Stata do-files
- **解释结果**：理解复杂的统计输出和回归结果

### 安装 Claude Code 插件
我们提供官方原生插件，集成 [Stata-MCP](https://github.com/sepinetam/stata-mcp) 由 @sepinetam 维护 和 [Stata LSP](https://github.com/euglevi/stata-language-server) 由 @euglevi 维护。安装命令：
```bash
# Install stata-mcp marketplace first
claude plugin marketplace add sepinetam/stata-mcp

# Install plugin to local, project or user scope
claude plugin install stata-toolbox -s local
```

详细的安装指南和故障排除，请查看[插件安装文档](https://docs.statamcp.com/claude-plugin)。

### 代理模式
代理模式的详细信息请查看[此处](../../../agent_examples/README.md)。

```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

uv sync
uv pip install -e .

stata-mcp --version  # 测试stata-mcp是否安装成功。
stata-mcp agent run  # 现在您可以享受stata-mcp代理模式。
```

或者您可以直接使用 `uvx`：
```bash
uvx stata-mcp --version  # 测试它是否可以在您的计算机上使用。
uvx stata-mcp agent run
```

您可以编辑 `agent_examples/openai/main.py` 中的 `[model_instructions](../../../agent_examples/openai/main.py#L37)` 和 `[task_message](../../../agent_examples/openai/main.py#L68)` 变量

### 代理作为工具
如果您想在另一个代理中使用Stata代理，[此处](../../Usages/agent_as/agent_as_tool.md)有一个简单的示例：

```python
import asyncio

from agents import Agent, Runner
from stata_mcp.agent_as.agent_as_tool import StataAgent

# 初始化stata代理并设置为工具
stata_agent = StataAgent()
sa_tool = stata_agent.as_tool()

# 创建主代理
agent = Agent(
    name="Assistant",
    instructions="您是一个有用的助手",
    tools=[sa_tool],
)


# 然后像往常一样运行代理。
async def main(task: str, max_turns: int = 30):
    result = await Runner.run(agent, input=task, max_turns=max_turns)
    return result


if __name__ == "__main__":
    econ_task = "使用Stata默认数据找出mpg和price之间的关系。"
    asyncio.run(main(econ_task))

```

### AI 聊天机器人客户端模式
> 标准配置要求：请确保 Stata 安装在默认路径，并且在 macOS 或 Linux 上存在 Stata CLI。

标准配置 json 如下，您可以通过添加环境变量来自定义配置。
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

有关更详细的使用信息，请访问[使用指南](../../Usages/Usage.md)。

一些高级的功能，访问[高级指南](../../Usages/Advanced.md)

### 前提条件
- [uv](https://github.com/astral-sh/uv) - 包安装器和虚拟环境管理器
- Claude、Cline、ChatWise或其他LLM服务
- Stata许可证
- 您的LLM API密钥

> 注：
> 1. 如果您位于中国，可以在此处找到简短的uv使用文档[此处](../../ChinaUsers/uv.md)。
> 2. Claude是Stata-MCP的最佳选择，对于中文用户，我推荐使用DeepSeek作为您的模型提供商，因为它价格便宜且功能强大，在中国提供商中得分最高，如果您对此感兴趣，请访问报告[How to use StataMCP improve your social science research](https://statamcp.com/reports/2025/09/21/stata_mcp_a_research_report_on_ai_assisted_empirical_research)。

### 安装
对于新版本，您无需再次安装 `stata-mcp` 包，只需使用以下命令检查您的计算机是否可以使用 stata-mcp。
```bash
uvx stata-mcp --usable
uvx stata-mcp --version
```

如果您希望在本地使用，也可以通过 pip 安装或下载源代码并编译。

**通过 pip 安装**
```bash
pip install stata-mcp
```

**下载源代码并编译**
```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

uv build
```
然后您可以在 `dist` 目录中找到编译好的 `stata-mcp` 可执行文件，可直接使用或加入 PATH。

例如：
```bash
uvx /path/to/your/whl/stata_mcp-1.13.0-py3-non-any.whl  # 这里的文件名可根据版本修改
```

## 📝 文档
- 有关更详细的使用信息，请访问[使用指南](../../Usages/Usage.md)。
- 高级用法，请访问[高级指南](../../Usages/Advanced.md)
- 一些问题，请访问[问题](../../Usages/Questions.md)
- 与[Stata-MCP@hanlulong](https://github.com/hanlulong/stata-mcp)的区别，请访问[区别](../../Difference.md)

## 💡 常见问题
- [Cherry Studio 32000 wrong](../../Usages/Questions.md#cherry-studio-32000-wrong)
- [Cherry Studio 32000 error](../../Usages/Questions.md#cherry-studio-32000-error)
- [Windows 支持](../../Usages/Questions.md#windows-supports)
- [网络问题](../../Usages/Questions.md#network-errors-when-running-stata-mcp)

## 🚀 路线图
- [x] macOS支持
- [x] Windows支持
- [ ] 更多LLM集成
- [ ] 性能优化

更多信息，请参阅[声明](../../Rights/Statement.md)。

## 🐛 报告问题
如果您遇到任何错误或有功能请求，请[提交问题](https://github.com/sepinetam/stata-mcp/issues/new)。

## 📄 许可证
[GNU Affero General Public License v3.0](../../../../LICENSE)

## 📚 引用
如果您在研究中使用 Stata-MCP，请使用以下格式之一引用此存储库：

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

## 📬 联系方式
电子邮件：[sepinetam@gmail.com](mailto:sepinetam@gmail.com)

或通过提交[拉取请求](https://github.com/sepinetam/stata-mcp/pulls)直接贡献！我们欢迎各种形式的贡献，从错误修复到新功能。

## ❤️ 致谢
作者诚挚感谢Stata官方团队给予的支持和授权测试开发使用的Stata License

## 📃 声明
项目里面涉及到的Stata指的是由[StataCorp LLC](https://www.stata.com/company/)开发的商业软件Stata。本项目与 StataCorp LLC 无隶属、关联或背书关系。本项目不包含 Stata 软件或其安装包，用户须自行从 StataCorp 获取并安装有效授权的 Stata 版本。本项目按 [Apache-2.0](../../../../LICENSE) 许可发布，不对因使用本项目或与 Stata 相关操作产生的任何损失承担责任。


## ✨ 历史Star

[![Star History Chart](https://api.star-history.com/svg?repos=sepinetam/stata-mcp&type=Date)](https://www.star-history.com/#sepinetam/stata-mcp&Date)