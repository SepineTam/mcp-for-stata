# Troubleshooting

This page collects common issues and their solutions.

## Network Issues

### Package download is slow or fails

If installing or running `uvx stata-mcp` is slow or fails because the package index is unreachable, configure uv to use a domestic mirror.

The following configuration uses the [Tsinghua University PyPI mirror](https://mirror.tuna.tsinghua.edu.cn/help/pypi/):

Edit `~/.config/uv/uv.toml` (user-level) or `/etc/uv/uv.toml` (system-level) with the following content:

```toml
[[index]]
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"
default = true
```

If you edit the system-level file, you may need `sudo`. On macOS or Linux with `nano`:

```bash
sudo nano /etc/uv/uv.toml
# Enter your password
# After editing, press Ctrl+X to exit
# Save the file when prompted
cat /etc/uv/uv.toml  # verify the content
```

After saving, re-run the installation or command that failed.
