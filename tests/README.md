# Tests

这个目录包含 `stata_mcp` 的测试代码。

## 目录结构

```
tests/
├── conftest.py              # 全局 pytest fixtures
├── download_data.py         # 下载 Stata 示例数据的辅助脚本
├── fixtures/                # 测试数据/fixture 文件
│   └── dataset/
│       ├── auto.csv
│       ├── auto.dta
│       ├── auto.xlsx
│       └── auto.sav
├── data_info/               # data_info 模块测试
│   ├── test_base.py
│   ├── test_csv.py
│   ├── test_dta.py
│   ├── test_spss.py
│   ├── test_xlsx.py
│   └── test_security.py
├── guard/                   # guard 安全校验模块测试
│   ├── test_validator.py
│   ├── test_validator_data_commands.py
│   ├── test_data_path_auditor.py
│   └── test_input_validation.py
├── cli/                     # CLI 模块测试
│   ├── test_server_parser.py
│   ├── test_server_registration.py
│   ├── test_ado_install.py
│   ├── test_install.py
│   └── test_verify.py
├── stata/                   # Stata 集成模块测试
│   ├── test_controller.py
│   ├── test_do_boundary.py
│   ├── test_do_timeout.py
│   ├── test_async_do.py
│   ├── test_help_interfaces.py
│   ├── test_help_security.py
│   └── test_log_smcl.py
├── api/                     # API 层测试
│   └── test_read_log_security.py
├── utils/                   # 工具模块测试
│   ├── test_parse_dofile.py
│   ├── test_color_stream.py
│   └── test_installer_backup.py
├── test_config_security.py  # config 模块安全测试
└── test_mcp_servers_security_log.py  # mcp_servers 安全日志测试
```

## 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行某个模块的测试
pytest tests/data_info/
pytest tests/guard/
pytest tests/cli/
pytest tests/stata/
pytest tests/api/
pytest tests/utils/

# 运行特定测试文件
pytest tests/data_info/test_csv.py

# 运行特定测试类
pytest tests/data_info/test_csv.py::TestCsvReading

# 运行特定测试方法
pytest tests/data_info/test_csv.py::TestCsvReading::test_df_shape

# 显示详细输出
pytest tests/ -v

# 显示 print 输出
pytest tests/ -s
```

## 编写测试

### 测试文件命名规范

- 测试文件以 `test_` 开头
- 测试类以 `Test` 开头
- 测试方法以 `test_` 开头

### 使用 Fixtures

`conftest.py` 中定义了共享的 fixtures：

```python
# 在测试中使用 fixture
def test_csv_read(sample_csv_path):
    # sample_csv_path 是一个 fixture
    data_info = CsvDataInfo(sample_csv_path)
    assert data_info is not None
```

### 跳过测试

```python
@pytest.mark.skip(reason="需要网络连接")
def test_url_fetch():
    ...

# 或者条件跳过
@pytest.mark.skipif(not has_network(), reason="无网络连接")
def test_url_fetch():
    ...
```

## 测试数据

### 目录内容

`fixtures/dataset/` 目录包含测试用的数据文件，默认提供同一组数据的四种格式：

```
fixtures/dataset/
├── auto.csv    # CSV 格式
├── auto.dta    # Stata 格式
├── auto.xlsx   # Excel 格式
└── auto.sav    # SPSS 格式
```

这些数据来自 Stata 自带的 `auto` 数据集，用于覆盖 `data_info` 模块对不同文件格式的解析场景。

### 数据生成方式

运行测试时，`conftest.py` 会自动检查 `fixtures/dataset/` 中的文件：

1. 如果 `auto.dta` 不存在，会从 Stata Press 官方数据仓库下载
2. 如果 `auto.csv` / `auto.xlsx` / `auto.sav` 不存在，会用 pandas 从 `auto.dta` 生成

因此第一次运行测试时可能需要联网下载数据，之后会自动复用本地缓存。

### 添加新的测试数据

如果需要更多 Stata 示例数据集，可以使用 `download_data.py` 脚本：

```bash
# 下载单个数据集
uv run tests/download_data.py auto

# 下载多个数据集
uv run tests/download_data.py auto nlswork

# 查看支持的数据集列表
uv run tests/download_data.py --list
```

下载的数据会保存到 `fixtures/dataset/`。

### 注意事项

- `fixtures/dataset/` 下的文件已被 `.gitignore` 忽略，不会进入版本控制
- 如果测试中出现 fixture 下载失败，会自动跳过依赖该 fixture 的测试
