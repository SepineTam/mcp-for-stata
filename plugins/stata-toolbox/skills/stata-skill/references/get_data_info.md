# `get_data_info`

Get descriptive statistics and a data preview for a supported data file.

## Parameters

| Parameter | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `data_path` | `str` | Yes | — | Absolute path to the data file |
| `vars_list` | `List[str] \| None` | No | `None` | Subset of variables to analyze (default: all) |
| `encoding` | `str` | No | `"utf-8"` | File encoding (ignored for `.dta`) |
| `head` | `int` | No | `0` | Number of preview rows (`0` = disabled) |

## Supported Formats

| Extension | Format | Handler |
|:---|:---|:---|
| `.dta` | Stata | `DtaDataInfo` |
| `.csv`, `.tsv`, `.psv` | CSV/Text | `CsvDataInfo` |
| `.xlsx`, `.xls` | Excel | `ExcelDataInfo` |
| `.sav`, `.zsav` | SPSS | `SpssDataInfo` |

## Returns

JSON string containing:

```json
{
  "overview": {
    "source": "data.dta",
    "obs": 1000,
    "var_numbers": 15,
    "var_list": ["id", "year", "income", ...]
  },
  "info_config": {
    "metrics": ["obs", "mean", "stderr", "min", "max"],
    "max_display": 10,
    "decimal_places": 3
  },
  "vars_detail": {
    "income": {
      "type": "numeric",
      "obs": 998,
      "mean": 45000.123,
      "stderr": 1200.456,
      "min": 10000.0,
      "max": 120000.0
    },
    "gender": {
      "type": "string",
      "top_values": ["Male", "Female"]
    }
  },
  "saved_path": "/path/to/cache/file.json"
}
```

## When to Use

- First encounter with a data file before writing any analysis code
- Understanding variable types, distributions, and missing values
- Checking data quality before regression

## Caching

Results are cached using content-addressable storage (MD5 hash of file content). Repeated queries on the same file return instantly from cache. The cache file path is returned in `saved_path`.

## Configurable Metrics

The following metrics can be configured via `~/.statamcp/config.toml` under `[data_info]`:

- `obs`: number of observations
- `mean`: arithmetic mean
- `stderr`: standard error
- `min` / `max`: minimum and maximum
- `q1` / `q3`: first and third quartile
- `skewness`: skewness
- `kurtosis`: kurtosis

Default metrics: `obs`, `mean`, `stderr`, `min`, `max`.

## Environment Variables

| Variable | Default | Description |
|:---|:---|:---|
| `STATA_MCP_DATA_INFO_DECIMAL_PLACES` | `3` | Decimal places for numeric output |
| `STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER` | `10` | Max string values to display |
| `STATA_MCP_DATA_INFO_HASH_LENGTH` | `12` | Hash length for cache filename |

## Example

```python
# Analyze all variables in a Stata file
get_data_info(data_path="/path/to/project/data.dta")

# Analyze a specific subset with 5 preview rows
get_data_info(
    data_path="/path/to/project/data.csv",
    vars_list=["income", "education", "age"],
    head=5
)
```
