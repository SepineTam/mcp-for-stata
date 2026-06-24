# 故障排查

本页面汇总了常见问题及其解决方法。

## 网络问题

### 包下载缓慢或失败

如果在安装或运行 `uvx stata-mcp` 时速度很慢，或者因为无法访问 PyPI 而失败，可以将 uv 配置为使用国内镜像。

以下配置使用[清华大学 PyPI 镜像](https://mirror.tuna.tsinghua.edu.cn/help/pypi/)：

编辑 `~/.config/uv/uv.toml`（用户级）或 `/etc/uv/uv.toml`（系统级），添加以下内容：

```toml
[[index]]
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"
default = true
```

如果编辑系统级文件，可能需要 `sudo`。在 macOS 或 Linux 上可以使用 `nano`：

```bash
sudo nano /etc/uv/uv.toml
# 输入密码
# 编辑完成后按 Ctrl+X 退出
# 按提示保存文件
cat /etc/uv/uv.toml  # 验证内容是否已保存
```

保存后，重新运行之前失败的安装或命令即可。
