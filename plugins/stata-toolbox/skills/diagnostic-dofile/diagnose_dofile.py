#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# 诊断 Stata do-file，生成 JSON 报告。
# 只读取文件内容，不修改原文件。
# 复用项目已有的 Stata 解析与安全规则，降低误判。

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from stata_mcp.guard.blacklist import (
    DANGEROUS_COMMANDS,
    PACKAGE_MANAGEMENT_COMMANDS,
)
from stata_mcp.utils.parse_dofile import expand_dofile_for_security


# 常见外部命令，建议用 Stata help 确认是否已安装
EXTERNAL_COMMANDS: frozenset[str] = frozenset({
    "reghdfe",
    "estout",
    "esttab",
    "outreg2",
    "coefplot",
    "ivreg2",
    "rdrobust",
    "rdplot",
    "ivreghdfe",
    "ppmlhdfe",
    "ftools",
    "binsreg",
    "did_multiplegt",
    "csdid",
    "drdid",
    "jwdid",
    "eventstudyinteract",
    "did_imputation",
    "twowayfeweights",
    "stackedev",
    "xthdidreg",
    "honestdid",
    "synth",
    "synth_runner",
    "sdid",
    "psmatch2",
    "cem",
    "matchit",
    "grstyle",
    "plottig",
    "tabout",
    "asdoc",
    "logout",
    "texdoc",
    "markdoc",
    "dyndoc",
})

# 可能覆盖输出文件的命令
OUTPUT_OVERWRITE_COMMANDS: frozenset[str] = frozenset({
    "graph",
    "export",
    "outreg2",
    "esttab",
    "estout",
    "putexcel",
    "putdocx",
    "putpdf",
    "logout",
    "texdoc",
    "saveold",
    "outsheet",
    "outfile",
})

# 上下文变更命令
CONTEXT_MUTATION_COMMANDS: frozenset[str] = frozenset({"cd", "chdir"})

# 路径相关命令
PATH_COMMANDS: frozenset[str] = frozenset({
    "use",
    "save",
    "saveold",
    "import",
    "export",
    "webuse",
    "sysuse",
    "infile",
    "infix",
    "insheet",
    "outsheet",
    "outfile",
    "do",
    "run",
    "include",
    "type",
    "erase",
    "rmdir",
    "mkdir",
    "copy",
    "cd",
    "chdir",
})

# 日志命令单独处理
LOG_COMMANDS: frozenset[str] = frozenset({"log"})


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="Diagnose a Stata do-file and emit a JSON report."
    )
    parser.add_argument("dofile", help="Path to the .do file to check")
    parser.add_argument(
        "--output",
        "-o",
        help="Path to write the report; defaults to stdout",
        default=None,
    )
    return parser.parse_args()


def detect_line_ending(content: str) -> str:
    """判断主要行尾符类型。"""
    crlf = content.count("\r\n")
    lf = content.count("\n") - crlf
    if crlf > 0 and lf == 0:
        return "crlf"
    if crlf > 0 and lf > 0:
        return "mixed"
    return "lf"


def has_replace_option(text: str) -> bool:
    """检查命令选项中是否包含 replace。"""
    # 只匹配顶层逗号后的 replace，避免括号内误报
    comma = _find_top_level_comma(text)
    options = text[comma:] if comma != -1 else ""
    return re.search(r",\s*replace\b", options, re.IGNORECASE) is not None


def _find_top_level_comma(text: str) -> int:
    """找到字符串和括号外的第一个逗号位置。"""
    index = 0
    length = len(text)
    paren_depth = 0
    while index < length:
        if text[index] == '"':
            end = text.find('"', index + 1)
            index = end + 1 if end != -1 else length
        elif text.startswith("'", index):
            end = text.find("'", index + 1)
            index = end + 1 if end != -1 else length
        elif text[index] == "(":
            paren_depth += 1
            index += 1
        elif text[index] == ")":
            paren_depth = max(paren_depth - 1, 0)
            index += 1
        elif text[index] == "," and paren_depth == 0:
            return index
        else:
            index += 1
    return -1


def normalize_path_token(token: str) -> str:
    """对路径做简单归一化，用于比较 use/save 是否指向同一文件。"""
    cleaned = token.strip().strip('"').strip("'")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.lower()


def is_absolute_path(token: str) -> bool:
    """判断路径是否为绝对路径。"""
    stripped = token.strip().strip('"').strip("'")
    return bool(
        stripped.startswith(("/", "~", "\\"))
        or re.match(r"^[A-Za-z]:\\", stripped)
    )


def extract_urls(text: str) -> list[str]:
    """提取文本中的 URL。"""
    return re.findall(r"https?://[^\s\"'`,;)]+", text)


def compute_sha256(path: Path) -> str:
    """计算文件 SHA256。"""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def detect_encoding(path: Path) -> tuple[str, bool]:
    """检测文件编码，返回 (编码名, 是否有 BOM)。"""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig", True
    for enc in ("utf-8", "gbk", "gb2312"):
        try:
            raw.decode(enc)
            return enc, False
        except UnicodeDecodeError:
            pass
    return "latin-1", False


def _command_origin_line(command) -> int:
    """返回命令对应的原始代码行号。"""
    return command.origins[0] if command.origins else command.line


def check_dangerous_and_external_commands(commands) -> list[dict]:
    """检查危险命令、包管理命令、外部命令。"""
    findings = []
    seen_external: set[str] = set()

    for command in commands:
        line = _command_origin_line(command)
        name = command.name
        text = command.text

        # 特殊处理 shell 转义前缀 ! / !!
        if text.startswith("!!"):
            findings.append({
                "level": "error",
                "line": line,
                "category": "dangerous_command",
                "message": "Detected shell escape command '!!'",
            })
            continue
        if text.startswith("!"):
            findings.append({
                "level": "error",
                "line": line,
                "category": "dangerous_command",
                "message": "Detected shell escape command '!'",
            })
            continue

        if name in DANGEROUS_COMMANDS:
            if name in CONTEXT_MUTATION_COMMANDS:
                msg = f"Detected working-directory change command '{name}'"
            else:
                msg = f"Detected dangerous command '{name}'"
            findings.append({
                "level": "error",
                "line": line,
                "category": "dangerous_command",
                "message": msg,
            })
            continue

        if name in PACKAGE_MANAGEMENT_COMMANDS:
            findings.append({
                "level": "error",
                "line": line,
                "category": "package_management",
                "message": f"Detected package-management command '{name}'; use the controlled installation path",
            })
            continue

        if name in EXTERNAL_COMMANDS and name not in seen_external:
            seen_external.add(name)
            findings.append({
                "level": "info",
                "line": line,
                "category": "external_command",
                "message": (
                    f"Detected external command '{name}'; run Stata 'help {name}' "
                    f"to verify it is installed"
                ),
            })

    return findings


def check_data_overwrite(commands) -> list[dict]:
    """检查 use 后 save 同一个文件的情况。"""
    findings = []
    used_files: dict[str, int] = {}

    # 第一次遍历收集 use 命令加载的文件
    for command in commands:
        if command.name != "use":
            continue
        for path in command.data_paths:
            normalized = normalize_path_token(path)
            if normalized:
                used_files[normalized] = _command_origin_line(command)

    # 第二次遍历检查 save 是否覆盖同名文件
    for command in commands:
        if command.name not in {"save", "saveold"}:
            continue
        if not has_replace_option(command.text):
            continue
        for path in command.data_paths:
            normalized = normalize_path_token(path)
            if normalized and normalized in used_files:
                findings.append({
                    "level": "warning",
                    "line": _command_origin_line(command),
                    "category": "data_overwrite",
                    "message": (
                        f"save replaces '{path}', which was loaded by use on line {used_files[normalized]}"
                    ),
                })

    return findings


def check_output_overwrite(commands) -> list[dict]:
    """检查输出文件是否被 replace 覆盖。"""
    findings = []

    for command in commands:
        line = _command_origin_line(command)
        name = command.name
        text = command.text

        if name in OUTPUT_OVERWRITE_COMMANDS and has_replace_option(text):
            display_name = name
            if name == "graph" and re.search(r"\bexport\b", text, re.IGNORECASE):
                display_name = "graph export"
            findings.append({
                "level": "warning",
                "line": line,
                "category": "output_overwrite",
                "message": f"Command '{display_name}' uses the replace option and may overwrite an existing output file",
            })
            continue

        if name in LOG_COMMANDS and re.search(r"\blog\s+using\b", text, re.IGNORECASE):
            if has_replace_option(text):
                findings.append({
                    "level": "warning",
                    "line": line,
                    "category": "output_overwrite",
                    "message": "log using uses the replace option and may overwrite an existing log",
                })

    return findings


def check_destructive_commands(commands) -> list[dict]:
    """检查可能清空内存或数据的命令。"""
    findings = []
    for command in commands:
        name = command.name
        text = command.text.lower()
        line = _command_origin_line(command)

        if name == "clear" and re.search(r"\bclear\s+all\b", text):
            findings.append({
                "level": "warning",
                "line": line,
                "category": "destructive_command",
                "message": "'clear all' clears all data from memory",
            })
        elif name == "drop" and re.search(r"\bdrop\s+_all\b", text):
            findings.append({
                "level": "warning",
                "line": line,
                "category": "destructive_command",
                "message": "'drop _all' drops all variables from memory",
            })

    return findings


def check_path_issues(commands) -> list[dict]:
    """检查路径相关问题。"""
    findings = []

    for command in commands:
        line = _command_origin_line(command)
        name = command.name
        text = command.text

        if name == "webuse":
            findings.append({
                "level": "warning",
                "line": line,
                "category": "network_data",
                "message": "Uses webuse to load remote data; verify the source is trusted",
            })

        # 检查 data_paths 中的绝对路径
        for path in command.data_paths:
            if is_absolute_path(path):
                findings.append({
                    "level": "info",
                    "line": line,
                    "category": "absolute_path",
                    "message": f"Uses absolute path '{path}', which hurts portability",
                })

        # 检查文本中的 URL
        urls = extract_urls(text)
        for url in urls:
            findings.append({
                "level": "warning",
                "line": line,
                "category": "network_url",
                "message": f"Detected network URL '{url}'; verify the domain is allowlisted",
            })

    return findings


def check_parse_diagnostics(commands, expansion_result) -> list[dict]:
    """处理解析器报告的诊断信息。"""
    findings = []

    # 全局诊断，影响整个文件的可靠性
    for diagnostic in expansion_result.diagnostics:
        if diagnostic.scope == "global" and diagnostic.security_relevant:
            findings.append({
                "level": "warning",
                "line": diagnostic.line,
                "category": "parse_issue",
                "message": f"Parse warning: {diagnostic.message}",
            })

    # 行级诊断，针对危险或路径相关命令时提升为警告
    sensitive_commands = DANGEROUS_COMMANDS | PACKAGE_MANAGEMENT_COMMANDS | PATH_COMMANDS
    for command in commands:
        if command.name not in sensitive_commands and not command.has_unresolved_macro:
            continue
        line_diagnostics = expansion_result.diagnostics_on(command)
        for diagnostic in line_diagnostics:
            if not diagnostic.security_relevant:
                continue
            level = "warning" if command.name in sensitive_commands else "info"
            findings.append({
                "level": level,
                "line": _command_origin_line(command),
                "category": "unresolved_macro" if diagnostic.code == "unresolved-macro" else "parse_issue",
                "message": f"{diagnostic.message} (command: {command.name})",
            })

    return findings


def count_line_types(content: str) -> dict[str, int]:
    """统计总行数、代码行、注释行、空行。"""
    lines = content.split("\n")
    total = len(lines)
    code = 0
    comment = 0
    blank = 0

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            blank += 1
        elif line.startswith("*") or line.startswith("//"):
            comment += 1
        else:
            code += 1

    return {
        "total_lines": total,
        "code_lines": code,
        "comment_lines": comment,
        "blank_lines": blank,
    }


def diagnose(path: Path) -> dict:
    """对指定 do-file 执行完整诊断。"""
    encoding, has_bom = detect_encoding(path)
    content = path.read_text(encoding=encoding)
    line_stats = count_line_types(content)

    expansion_result = expand_dofile_for_security(path)
    commands = expansion_result.commands

    findings: list[dict] = []
    findings.extend(check_dangerous_and_external_commands(commands))
    findings.extend(check_data_overwrite(commands))
    findings.extend(check_output_overwrite(commands))
    findings.extend(check_destructive_commands(commands))
    findings.extend(check_path_issues(commands))
    findings.extend(check_parse_diagnostics(commands, expansion_result))

    # 编码警告
    if encoding not in ("utf-8", "utf-8-sig"):
        findings.append({
            "level": "warning",
            "line": 0,
            "category": "encoding_issue",
            "message": f"File encoding is {encoding}; consider converting to UTF-8 to avoid garbled text",
        })

    # 空文件或只有注释
    if line_stats["code_lines"] == 0:
        findings.append({
            "level": "info",
            "line": 0,
            "category": "empty_or_comment_only",
            "message": "File is empty or contains only comments; no executable code found",
        })

    error_count = sum(1 for f in findings if f["level"] == "error")
    warning_count = sum(1 for f in findings if f["level"] == "warning")
    info_count = sum(1 for f in findings if f["level"] == "info")

    return {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "file": {
            "path": str(path.resolve()),
            "size_bytes": path.stat().st_size,
            "sha256": compute_sha256(path),
            "encoding": encoding,
            "has_bom": has_bom,
            "line_ending": detect_line_ending(content),
        },
        "summary": {
            **line_stats,
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
        },
        "findings": findings,
    }


def main() -> int:
    """脚本入口。"""
    args = parse_args()
    path = Path(args.dofile)
    if not path.exists():
        print(f"Error: file not found {path}", file=sys.stderr)
        return 1
    if not path.is_file():
        print(f"Error: path is not a file {path}", file=sys.stderr)
        return 1

    report = diagnose(path)
    output = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(output, encoding="utf-8")
        print(f"Report saved to {out_path.resolve()}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
