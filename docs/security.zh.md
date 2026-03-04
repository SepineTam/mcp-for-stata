# 安全守卫系统

安全守卫系统提供针对 Stata dofile 中危险命令和操作的保护。它充当 LLM 生成代码与实际执行之间的安全层。

## 概述

安全守卫**默认启用**，以防止意外执行破坏性操作。它在执行前针对危险命令和模式黑名单验证所有 dofile 代码。

### 关键功能

- **基于黑名单的验证**：阻止已知的危险命令
- **模式匹配**：使用正则表达式检测潜在危险操作
- **逐行分析**：提供带行号的详细风险报告
- **可配置**：可根据需要禁用（不推荐）
- **安全代码零误报**：仅标记真正危险的操作

## 危险命令

安全守卫阻止以下危险命令：

### Shell 执行命令

| 命令 | 描述 | 示例 |
|---------|-------------|---------|
| `!` | Unix 风格 shell 转义 | `! ls -la` |
| `!!` | 扩展 shell 命令 | `!! vi file.do` |
| `shell` | Shell 命令执行 | `shell dir` |
| `xshell` | Mac/Unix(GUI) 扩展 shell | `xshell vi file.do` |
| `winexec` | Windows 程序执行 | `winexec notepad.exe` |
| `unixcmd` | Unix 命令执行 | `unixcmd ls` |

### 文件操作

| 命令 | 描述 | 风险 |
|---------|-------------|------|
| `erase` | 文件删除 | 数据丢失 |
| `rm` | 文件删除（别名） | 数据丢失 |
| `rmdir` | 目录删除 | 数据丢失 |
| `copy` | 文件复制 | 可能覆盖文件 |

### 代码执行

| 命令 | 描述 | 风险 |
|---------|-------------|------|
| `run` | 运行另一个 do 文件 | 不受信任的代码执行 |
| `do` | 执行 do 文件 | 不受信任的代码执行 |
| `include` | 包含另一个 do 文件 | 不受信任的代码执行 |

## 配置

### 启用/禁用安全守卫

#### 选项 1：配置文件

编辑 `~/.statamcp/config.toml`：

```toml
[SECURITY]
IS_GUARD = true  # 默认：true
```

#### 选项 2：环境变量

```bash
# 启用（默认）
export STATA_MCP__IS_GUARD=true

# 禁用（不推荐）
export STATA_MCP__IS_GUARD=false
```

### 默认行为

- **默认**：启用（`IS_GUARD = true`）
- **推荐**：生产使用时保持启用
- **开发**：可禁用以进行测试（谨慎使用）

## 使用

### 基本使用

使用 `stata_do` 工具时自动应用安全守卫：

```python
# 当 IS_GUARD 启用时（默认）
result = stata_mcp.stata_do(code="""
    sysuse auto
    regress price mpg weight
""")

# 安全代码正常执行
```

### 安全验证示例

当检测到危险代码时：

```python
result = stata_mcp.stata_do(code="""
    sysuse auto
    ! rm -rf /  # 危险命令
""")

# Error: Security validation failed
# ❌ Security validation failed. Found dangerous items:
#   - Line 3: command '!'
```

### 编程使用

如果您将 Stata-MCP 作为库使用：

```python
from stata_mcp.guard import GuardValidator

# 创建验证器
validator = GuardValidator()

# 验证代码
code = """
sysuse auto
regress price mpg weight
"""

report = validator.validate(code)

if report.is_safe:
    print("✅ Code is safe to execute")
else:
    print(f"❌ Found {len(report.dangerous_items)} dangerous items:")
    for item in report.dangerous_items:
        print(f"  {item}")
```

## 安全报告

### SecurityReport 对象

```python
@dataclass
class SecurityReport:
    is_safe: bool                              # True 表示未发现危险项
    dangerous_items: List[RiskItem]            # 检测到的风险列表
```

### RiskItem 对象

```python
@dataclass
class RiskItem:
    type: str                                  # "command" 或 "pattern"
    content: str                               # 危险内容
    line: int                                  # 行号（从 1 开始）
```

### 示例输出

```python
# 安全代码
report = validator.validate("sysuse auto")
print(report)
# Output: ✅ Code passed security validation

# 危险代码
report = validator.validate("! rm file.txt")
print(report)
# Output:
# ❌ Security validation failed. Found dangerous items:
#   - Line 1: command '!'
```

## 危险模式

安全守卫使用正则表达式模式检测危险操作：

### Shell 命令模式

```python
r"!\s*\w+"           # 带命令的 Shell 转义：! ls
r"!!\s*\w+"          # 扩展 shell：!! vi file.do
r"shell\s+\w+"       # Shell 命令：shell dir
r"xshell\s+\w+"      # 扩展 shell：xshell vi file.do
r"winexec\s+\S+"     # Windows 执行：winexec program.exe
r"unixcmd\s+\w+"     # Unix 命令：unixcmd ls
```

### 文件操作模式

```python
r"erase\s+.*"        # 文件删除：erase file.dta
r"rm\s+.*"           # 文件删除：rm file.dta
r"rmdir\s+.*"        # 目录删除：rmdir mydir
r"copy\s+.*"         # 文件复制：copy file1.dta file2.dta
```

### 代码执行模式

```python
r"run\s+.*"          # 运行 do 文件：run script.do
r"\bdo\s+.*"         # 执行 do 文件：do script.do
r"include\s+.*"      # 包含 do 文件：include setup.do
```

## 验证流程

### 逐步验证

1. **代码输入**：接收 dofile 代码字符串
2. **行分割**：将代码分割成行以跟踪行号
3. **过滤**：跳过空行和注释（以 `*` 开头）
4. **命令检查**：针对危险命令检查每一行
5. **模式检查**：针对危险模式检查每一行
6. **报告生成**：创建包含所有发现的 SecurityReport

### 验证示例

```python
code = """
* This is a comment
sysuse auto
! rm dangerous.txt  # Line 3
regress price mpg
"""

report = validator.validate(code)
# Report:
# ❌ Security validation failed. Found dangerous items:
#   - Line 3: command '!'
```

## 最佳实践

### 1. 保持安全守卫启用

```toml
[SECURITY]
IS_GUARD = true  # 始终保持启用
```

### 2. 审查安全报告

始终审查安全验证报告：

```python
report = validator.validate(code)
if not report.is_safe:
    # 记录或通知危险项
    for item in report.dangerous_items:
        logger.warning(f"Dangerous item found: {item}")
```

### 3. 为允许的操作使用白名单

如果您需要执行某些危险操作：

1. 手动审查代码
2. 移除危险命令
3. 使用安全的替代方案

示例：
```stata
* 代替：! rm tempfile.dta
* 使用：erase tempfile.dta  （仍被阻止，但显示意图）

* 更好的方法：使用 Stata 内置的安全操作
capture erase tempfile.dta
```

### 4. 教育用户

记录哪些命令被阻止及其原因：

```markdown
## 被阻止的命令

以下命令因安全原因被阻止：
- Shell 命令（!、shell、xshell 等）
- 文件删除（erase、rm）
- 外部代码执行（run、do、include）

请使用安全的替代方案或联系管理员获取帮助。
```

## 故障排除

### 误报

如果您认为某个命令被错误标记：

1. **审查该命令**：它是否真的危险？
2. **检查模式**：它是否匹配危险模式？
3. **考虑替代方案**：是否有更安全的方法完成任务？

### 禁用安全守卫

**⚠️ 警告**：不推荐禁用安全守卫。

仅在以下情况下禁用：
- 您处于受信任的环境中
- 所有代码都经过人工审查
- 您了解风险

```bash
# 临时禁用（仅当前会话）
export STATA_MCP__IS_GUARD=false
stata-mcp

# 永久禁用（添加到配置）
# 编辑 ~/.statamcp/config.toml
[SECURITY]
IS_GUARD = false
```

### 自定义黑名单

您可以通过修改代码来扩展黑名单：

```python
from stata_mcp.guard.blacklist import DANGEROUS_COMMANDS

# 添加自定义危险命令
DANGEROUS_COMMANDS.add("my_dangerous_command")

# 使用自定义验证器
from stata_mcp.guard import GuardValidator
validator = GuardValidator()
validator.dangerous_commands.add("another_command")
```

## 安全考虑

### 守卫防护的内容

✅ **防止**：
- Shell 命令执行
- 文件删除操作
- 不受信任的代码执行
- 系统级操作

❌ **不能防止**：
- Stata 内的数据修改
- 无限循环
- 内存耗尽
- Stata 崩溃

### 限制

安全守卫：
- 不分析数据流
- 不跟踪变量值
- 不防止资源耗尽
- 不能替代适当的代码审查

### 纵深防御

安全守卫是一层保护。结合以下措施：

1. **监控**：启用 RAM 监控（参见[监控文档](monitoring.md)）
2. **沙盒**：对不受信任的代码使用隔离环境
3. **代码审查**：人工审查生成的代码
4. **备份**：定期备份重要数据

## 与 MCP 工具的集成

### 自动集成

安全守卫自动与以下工具集成：

- `stata_do`：执行 Stata do 文件（默认验证）
- `write_dofile`：创建 do 文件（执行时验证）

### 验证流程

```
用户请求 → MCP 工具 → 安全守卫 → 验证
                                      ↓
                                 通过？ → 执行
                                      ↓
                                 失败？ → 返回错误
```

## 可扩展性

### 创建自定义验证器

您可以为特定用例创建自定义验证器：

```python
from stata_mcp.guard import GuardValidator, RiskItem, SecurityReport

class CustomValidator(GuardValidator):
    """带附加规则的自定义验证器。"""

    def validate(self, code: str) -> SecurityReport:
        # 获取基础验证结果
        report = super().validate(code)

        # 添加自定义验证逻辑
        if "custom_dangerous_thing" in code:
            report.dangerous_items.append(
                RiskItem(
                    type="custom",
                    content="custom_dangerous_thing",
                    line=code.find("custom_dangerous_thing")
                )
            )
            report.is_safe = False

        return report
```

### 组合多个验证器

```python
from stata_mcp.guard import GuardValidator

# 创建多个验证器
basic_validator = GuardValidator()
custom_validator = CustomValidator()

# 使用两者进行验证
code = "some stata code"
report1 = basic_validator.validate(code)
report2 = custom_validator.validate(code)

# 合并结果
if report1.is_safe and report2.is_safe:
    print("✅ All validations passed")
```

## 示例

### 示例 1：安全代码执行

```python
from stata_mcp.guard import GuardValidator

validator = GuardValidator()

safe_code = """
* Load sample data
sysuse auto

* Run regression
regress price mpg weight

* Display results
display "R-squared: " + string(e(r2))
"""

report = validator.validate(safe_code)
print(report)
# Output: ✅ Code passed security validation
```

### 示例 2：危险代码检测

```python
dangerous_code = """
sysuse auto

* This will be blocked
! rm -rf /important/data

regress price mpg
"""

report = validator.validate(dangerous_code)
print(report)
# Output:
# ❌ Security validation failed. Found dangerous items:
#   - Line 5: command '!'
```

### 示例 3：多项违规

```python
multiple_violations = """
sysuse auto
shell delete file.txt
run untrusted_script.do
"""

report = validator.validate(multiple_violations)
print(f"Found {len(report.dangerous_items)} violations:")
for item in report.dangerous_items:
    print(f"  {item}")
# Output:
# Found 2 violations:
#   Line 3: command 'shell'
#   Line 4: pattern 'run\s+.*'
```

## 总结

安全守卫系统为自动化 Stata 执行提供基本保护：

- ✅ **默认启用**以确保安全
- ✅ **阻止危险命令**（shell、文件删除等）
- ✅ **基于模式的检测**实现全面覆盖
- ✅ **详细报告**带行号
- ✅ **可配置**以适应不同用例
- ✅ **禁用时零开销**（不推荐）

对于生产使用，始终保持安全守卫启用并定期审查验证报告。
