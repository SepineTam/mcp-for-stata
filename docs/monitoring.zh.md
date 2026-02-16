# 监控系统

监控系统在执行期间提供 Stata 进程的实时监控。此功能旨在防止资源耗尽并提高系统稳定性。

## 概述

监控系统**默认禁用**以保持 100% 的向后兼容性。启用时，它监控 Stata 子进程执行，并可自动终止超过配置资源限制的进程。

### 当前功能

- **RAM 监控**：跟踪内存使用并终止超过 RAM 限制的进程
- **跨平台**：使用 `psutil` 在 macOS、Linux 和 Windows 上工作
- **非侵入式**：禁用时开销极小，启用时为守护线程
- **可扩展**：抽象基类用于添加新的监控类型（例如超时监控）

## 架构

### MonitorBase

所有监控器实现的抽象基类：

```python
class MonitorBase(ABC):
    @abstractmethod
    def start(self, process: Any) -> None:
        """开始监控给定进程。"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """停止监控。"""
        pass
```

### RAMMonitor

监控 Stata 进程的 RAM 使用：

- **检查间隔**：0.5 秒
- **指标**：RSS（驻留集大小），单位 MB
- **动作**：超过限制时杀死进程
- **错误**：抛出带详情的 `RAMLimitExceededError`

## 配置

### 启用监控

监控由两个配置选项控制：

#### 选项 1：配置文件

编辑 `~/.statamcp/config.toml`：

```toml
[MONITOR]
IS_MONITOR = true
MAX_RAM_MB = 8192  # 8 GB 限制
```

#### 选项 2：环境变量

```bash
export STATA_MCP__IS_MONITOR=true
export STATA_MCP__RAM_LIMIT=8192
```

### 配置优先级

1. 环境变量（最高）
2. 配置文件（`~/.statamcp/config.toml`）
3. 默认值（最低）

### RAM 限制值

- `-1` 或 `None`：无限制（默认）
- `0`：不推荐（将立即杀死）
- 正值：以 MB 为单位的 RAM 限制

示例：
```bash
# 无限制（默认）
export STATA_MCP__RAM_LIMIT=-1

# 4 GB 限制
export STATA_MCP__RAM_LIMIT=4096

# 8 GB 限制
export STATA_MCP__RAM_LIMIT=8192

# 16 GB 限制
export STATA_MCP__RAM_LIMIT=16384
```

## 使用

### 基本设置

1. **在配置中启用监控**：
   ```bash
   export STATA_MCP__IS_MONITOR=true
   export STATA_MCP__RAM_LIMIT=8192
   ```

2. **正常运行 Stata-MCP**：
   ```bash
   stata-mcp
   # 或
   stata-mcp agent run
   ```

3. **启用时监控自动进行**：
   - 无需代码更改
   - 适用于所有 MCP 工具
   - 与现有工作流程无缝集成

### 编程使用

如果您将 Stata-MCP 作为库使用：

```python
from stata_mcp.monitor import RAMMonitor
from stata_mcp.core.stata import StataDo

# 创建带 8GB 限制的监控器
monitor = RAMMonitor(max_ram_mb=8192)

# 传递给 StataDo
stata = StataDo(
    dofile_path="analysis.do",
    monitors=[monitor]  # 可选：监控器列表
)

# 执行自动被监控
result = stata.execute()
```

## 行为

### 当超过 RAM 限制时

1. **检测**：监控器检测到 RAM 使用 > 限制
2. **日志记录**：记录带详情的警告
3. **终止**：立即杀死进程
4. **错误**：抛出 `RAMLimitExceededError`

### 示例输出

```
WARNING: RAM limit exceeded: 8256MB > 8192MB. Killing Stata process (PID: 12345)
ERROR: RAM limit exceeded: Used 8256MB, Limit 8192MB
```

### 正常完成

如果进程在超过限制前完成：
- 监控器优雅停止
- 不抛出错误
- 正常执行流程继续

## 性能考虑

### 开销

- **禁用**：零开销（默认）
- **启用**：守护线程带来的极小开销
  - 每 0.5 秒进行一次 RAM 检查
  - 使用 `psutil` 实现跨平台兼容性

### 建议

对于**生产环境**：
```toml
[MONITOR]
IS_MONITOR = true
MAX_RAM_MB = 16384  # 根据您的硬件设置合理限制
```

对于**开发环境**：
```toml
[MONITOR]
IS_MONITOR = false  # 禁用以避免意外终止
```

对于**高性能计算**：
```toml
[MONITOR]
IS_MONITOR = true
MAX_RAM_MB = 65536  # 64 GB 用于大数据集
```

## 错误处理

### RAMLimitExceededError

当超过 RAM 限制时抛出：

```python
from stata_mcp.core.types import RAMLimitExceededError

try:
    result = stata.execute()
except RAMLimitExceededError as e:
    print(f"RAM exceeded: {e.ram_used_mb:.0f}MB > {e.ram_limit_mb}MB")
    # 处理错误：保存工作、通知用户等
```

错误属性：
- `ram_used_mb`：超过限制时实际使用的 RAM
- `ram_limit_mb`：配置的 RAM 限制

## 可扩展性

### 创建自定义监控器

您可以通过扩展 `MonitorBase` 创建自定义监控器：

```python
from stata_mcp.monitor.base import MonitorBase
import time
import threading

class TimeoutMonitor(MonitorBase):
    """监控并超时长时间运行的进程。"""

    def __init__(self, timeout_seconds: int):
        self.timeout = timeout_seconds
        self._start_time = None
        self._monitor_thread = None
        self._stop_event = threading.Event()

    def start(self, process):
        """开始超时监控。"""
        self._start_time = time.time()
        self.process = process

        def monitor_loop():
            while not self._stop_event.is_set():
                if time.time() - self._start_time > self.timeout:
                    self.process.kill()
                    break
                self._stop_event.wait(1)

        self._monitor_thread = threading.Thread(
            target=monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()

    def stop(self):
        """停止监控。"""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
```

### 使用多个监控器

您可以同时使用多个监控器：

```python
from stata_mcp.monitor import RAMMonitor, TimeoutMonitor

# 创建多个监控器
ram_monitor = RAMMonitor(max_ram_mb=8192)
timeout_monitor = TimeoutMonitor(timeout_seconds=3600)

# 传递给 StataDo
stata = StataDo(
    dofile_path="analysis.do",
    monitors=[ram_monitor, timeout_monitor]
)
```

## 故障排除

### 监控器不工作

1. **检查是否启用监控**：
   ```bash
   echo $STATA_MCP__IS_MONITOR
   ```

2. **验证配置文件语法**：
   ```bash
   cat ~/.statamcp/config.toml
   ```

3. **检查环境变量冲突**：
   ```bash
   env | grep STATA_MCP
   ```

### 进程意外被杀死

1. **检查 RAM 限制是否合理**：
   ```bash
   echo $STATA_MCP__RAM_LIMIT
   ```

2. **查看日志了解终止原因**：
   ```bash
   tail -f ~/.statamcp/stata_mcp_debug.log
   ```

3. **如需要增加限制**：
   ```bash
   export STATA_MCP__RAM_LIMIT=16384
   ```

### psutil 问题

如果遇到 `psutil` 错误：

1. **确保 psutil 已安装**：
   ```bash
   uv pip install psutil>=6.0.0
   ```

2. **检查 psutil 版本**：
   ```bash
   python3 -c "import psutil; print(psutil.__version__)"
   ```

3. **验证进程访问权限**（Linux/macOS）：
   ```bash
   # 监控器应该有访问子进程的权限
   # 子进程不需要特殊操作
   ```

## 最佳实践

### 1. 从无限制开始

对于初始测试：
```bash
export STATA_MCP__IS_MONITOR=true
export STATA_MCP__RAM_LIMIT=-1  # 最初无限制
```

### 2. 监控典型使用

运行典型工作负载并观察日志中的 RAM 使用。

### 3. 设置合理限制

将限制设置为典型使用量的 20-50% 以上：
```bash
# 如果典型使用量是 6GB
export STATA_MCP__RAM_LIMIT=8192  # 8GB 限制
```

### 4. 测试边缘情况

使用大数据集测试以确保限制适当。

### 5. 记录限制

在项目文档中为团队成员记录 RAM 限制。

## 安全考虑

- 监控器在守护线程中运行（主线程退出时终止）
- 不需要权限提升
- 使用标准 `psutil` 库实现跨平台兼容性
- 监控器只能访问它创建的子进程

## 未来增强

未来可能的监控类型：
- **超时监控器**：限制执行时间
- **CPU 监控器**：跟踪 CPU 使用百分比
- **磁盘 I/O 监控器**：监控磁盘读写操作
- **网络监控器**：跟踪网络活动（如适用）

## 注意事项

- 此功能是在 Claude Code 和 GLM-4.7 的协助下开发的
- 监控是通过配置**选择性加入**的
- 禁用时，行为与以前版本 100% 相同
- 监控系统设计为可扩展，以支持未来的用例
