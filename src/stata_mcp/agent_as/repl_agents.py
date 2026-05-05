#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : repl_agents.py

import asyncio
import os
import textwrap
import uuid
import warnings
from pathlib import Path

from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from agents.mcp import MCPServerStdio
from agents.memory.sqlite_session import SQLiteSession
from openai_api_polling.polling import APIPolling, ClientPolling

set_tracing_disabled(disabled=True)


def get_model_instructions(work_dir: str) -> str:
    """获取模型指令，包含当前工作目录信息"""
    return textwrap.dedent(f"""
    # 角色定义
    # [定义助手的核心身份和专业领域]

    # 核心能力
    # [列出主要技能和功能模块]

    # 工作原则
    # [指导性行为准则和优先级]
    # - 所有操作都在当前工作目录进行: {work_dir}
    # - 执行 Stata 命令前先确保切换到正确的目录: cd "{work_dir}"

    # 分析流程
    # [标准化的分析步骤和方法]

    # 输出标准
    # [结果呈现的格式和质量要求]

    # 代码规范
    # [生成代码的最佳实践]

    # 交互风格
    # [与用户沟通的方式和特点]
    """)


class REPLAgent:
    client_polling = ClientPolling(
        api_keys=[
            os.getenv("STATA_MCP_API_KEY", os.getenv("OPENAI_API_KEY", None))
        ],
        base_url=os.getenv("STATA_MCP_API_BASE_URL",
                           os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    )

    llm = os.getenv(
        "STATA_MCP_MODEL", os.getenv(
            "OPENAI_MODEL", "gpt-3.5-turbo"
        )
    )

    def __init__(self, work_dir: str = "./", session_id: str = None):
        warnings.warn(
            "Agent mode is deprecated and will be removed in a future version. "
            "Use MCP server mode (stata-mcp server) instead.",
            FutureWarning,
            stacklevel=2,
        )
        self.work_dir = Path(work_dir).expanduser().absolute()
        self.work_dir.mkdir(exist_ok=True)

        self.session_id = session_id or f"stata_session_{uuid.uuid4().hex[:8]}"

        session_db_path = self.work_dir / ".stata_sessions.db"

        self.session = SQLiteSession(
            session_id=self.session_id,
            db_path=session_db_path
        )

        self.stata_mcp_server = MCPServerStdio(
            name="Stata-MCP",
            params={
                "command": "uvx",
                "args": [
                    "stata-mcp"  # or you can use the local beta version with the git clone repo.
                ],
                "env": {
                    "STATA_MCP_CWD": self.work_dir.as_posix(),
                }
            },
            cache_tools_list=True,
            client_session_timeout_seconds=60,
            max_retry_attempts=3
        )

        async_client = self.client_polling.async_client
        self.agent = Agent(
            name="Stata Assistant",
            instructions=get_model_instructions(self.work_dir.as_posix()),
            mcp_servers=[self.stata_mcp_server],
            model=OpenAIChatCompletionsModel(
                model=self.llm,
                openai_client=async_client
            )
        )
        print("Current Agent Config: ")
        print(f">>> API KEY\t: {APIPolling.mask_api_key(async_client.api_key, mask_len=20)}")
        print(f">>> BASE URL\t: {async_client.base_url}")
        print(f">>> MODEL\t: {self.llm}")

    def __del__(self):
        async def clean_up():
            try:
                await self.stata_mcp_server.cleanup()
            except Exception:
                pass
        asyncio.run(clean_up())

    async def invoke(self, query: str):
        await self.stata_mcp_server.connect()
        try:
            result = await Runner.run(
                self.agent,
                query,
                session=self.session,
                max_turns=30
            )
        except Exception as e:
            print("Something went wrong")
            return str(e)
        finally:
            await self.stata_mcp_server.cleanup()
        return result.final_output

    def run(self):
        print("Welcome to Stata-MCP built-in Agent!")
        print("You can type what you want to do with Stata-MCP after sign `> `")
        print("Type `/exit` or `bye` to exit")
        while True:
            query = input("> ")
            if query.lower() == "/exit" or query.lower() == "bye":
                break
            result = asyncio.run(self.invoke(query))
            print(result)
        exit(0)
