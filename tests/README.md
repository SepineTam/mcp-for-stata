# Tests

这个目录包含 `stata_mcp` 的测试代码。

## 目录结构

```
tests/
├── conftest.py              # 全局 pytest fixtures
├── fixtures/                # 测试数据/fixture 文件
│   └── dataset/
│       ├── auto.csv
│       ├── auto.dta
│       ├── auto.xlsx
│       └── auto.sav
├── unit/                    # 单元测试
│   └── test_data_info/      # data_info 模块的单元测试
│       ├── test_base.py     # 测试基类
│       ├── test_csv.py      # 测试 CSV 读取
│       ├── test_dta.py      # 测试 DTA 读取
│       └── test_xlsx.py     # 测试 Excel 读取
├── integration/             # 集成测试
│   └── test_url_fetch.py   # 测试 URL 获取（默认跳过）
└── README.md               # 本文件
```

## 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行特定测试文件
pytest tests/unit/test_data_info/test_csv.py

# 运行特定测试类
pytest tests/unit/test_data_info/test_csv.py::TestCsvReading

# 运行特定测试方法
pytest tests/unit/test_data_info/test_csv.py::TestCsvReading::test_df_shape

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

`dataset/` 目录包含测试用的数据文件，这些文件是从 Stata 的 auto 数据集生成的。
