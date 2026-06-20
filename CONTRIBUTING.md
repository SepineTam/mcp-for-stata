# CONTRIBUTING
Thank you for your interest in contributing to this project! We welcome contributions from everyone. Please follow the guidelines below to ensure a smooth process.

## Branch Protection Policy

**All changes MUST be submitted via Pull Request.** Direct commits to `master` branch are NOT allowed.

### Branch Naming Convention

Create a feature branch before making changes:
- **Feature branches**: `feat/feature-name` or `dev/1.2.3`
- **Bug fix branches**: `fix/bug-name`
- **Docs branches**: `docs/doc-name`

### PR Workflow

1. Create a new branch from the target development branch (e.g., `dev/1.x.y`)
2. Make your changes and commit
3. Push the branch to remote
4. Create a Pull Request targeting the development branch
5. Wait for review (if applicable)
6. Merge PR when approved

### Syncing Development Branches

When `master` receives updates (e.g., documentation fixes, hotfixes), development branches should be kept in sync to reduce future merge conflicts:

```bash
# On the development branch
git checkout dev/1.x.y
git merge origin/master
```

This ensures the development branch incorporates the latest changes from `master` before it is eventually merged back.

### Example

```bash
# Create and switch to new branch
git checkout -b dev/1.13.42

# Make changes, stage and commit
git add .
git commit -m "feat: add new feature"

# Push branch to remote
git push -u origin dev/1.13.42

# Create PR via GitHub CLI or web interface
gh pr create --title "feat: add new feature" --body "Description here"
```

## Git Commit Standards

We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for all commit messages. This creates a structured commit history that is both human and machine readable.

### Basic Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type | Description | SemVer Impact |
|------|-------------|---------------|
| `feat` | New feature | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentation changes | NONE |
| `style` | Code formatting (no functional changes) | NONE |
| `refactor` | Code refactoring | NONE |
| `perf` | Performance improvements | NONE |
| `test` | Testing related | NONE |
| `chore` | Build tools, auxiliary tools | NONE |
| `ci` | CI/CD configuration | NONE |
| `build` | Build system changes | NONE |
| `revert` | Revert a commit | NONE |

### Breaking Changes

Breaking changes MUST be indicated in one of two ways:

1. **Using `!` before the colon:**
   ```
   feat!: send an email to customer when product is shipped
   feat(api)!: remove deprecated endpoints
   ```

2. **Using BREAKING CHANGE footer:**
   ```
   feat: allow provided config object to extend other configs

   BREAKING CHANGE: `extends` key in config file is now used for extending other config files
   ```

Any commit with a breaking change correlates with a **MAJOR** version bump.

### Examples

**Simple commit:**
```bash
feat: add user avatar upload functionality
```

**With scope:**
```bash
feat(auth): add two-factor authentication
```

**With body and footer:**
```bash
fix: prevent racing of requests

Introduce a request id and a reference to latest request. Dismiss
incoming responses other than from latest request.

Fixes #123
```

**Breaking change:**
```bash
feat(api): update user API response format

BREAKING CHANGE:
User API response format has been updated:
- Removed `user_name` field
- Added `username` and `display_name` fields
```

### Using Claude Code for Commits

If you are not comfortable with git, you can ask Claude Code to help you commit changes. For example:
```bash
# In Claude Code, you can say:
> help me commit my change to github

# Or manually stage files and let Claude generate the message:
!git add <the_files_you_want_to_commit>
> help me commit the message to github

# Always review the commit before pushing
git push
```

**Important:** Always review the generated commit message for accuracy before pushing, as AI tools may sometimes make mistakes.

## Legal Notice

By contributing to this project, you agree to the terms of the [Contributor License Agreement](source/docs/Rights/CLA.md). If you do not have the rights to submit the code, please do not contribute.

## Development Guidelines

### Code Style

- All Python functions must have **type annotations**
- All Python functions must have **English docstrings**
- Script comments should be in **Chinese** (for one-time scripts)
- Use descriptive variable names
- Maintain proper code indentation

### Project Structure

```
stata-mcp/
├── src/stata_mcp/
│   ├── __init__.py          # MCP server entry point
│   ├── config.py            # Configuration system
│   ├── core/                # Core functionality
│   │   ├── stata/          # Stata integration
│   │   └── data_info/      # Data processing
│   ├── guard/              # Security validation
│   ├── monitor/            # Performance monitoring
│   ├── cli/                # Command-line interface
│   └── agent_as/           # Agent mode implementation
├── docs/                   # Documentation
├── tests/                  # Test files (if applicable)
└── config.example.toml     # Example configuration
```

### Adding New Features

#### 1. Configuration Options

When adding new configuration options:

1. Add to `config.example.toml`
2. Implement in `src/stata_mcp/config.py`
3. Add documentation in `docs/configuration.md`
4. Update CLAUDE.md if needed

Example:
```python
@property
def MY_NEW_OPTION(self) -> bool:
    return self._get_config_value(
        config_keys=["SECTION", "MY_OPTION"],
        env_var="STATA_MCP__MY_OPTION",
        default=False,
        converter=self._to_bool,
        validator=lambda x: isinstance(x, bool)
    )
```

#### 2. Security Features

When adding security features:

1. Extend `src/stata_mcp/guard/` module for dofile content validation
2. Add to blacklist or create new validators
3. For execution boundary controls, update both `src/stata_mcp/mcp_servers.py` and `src/stata_mcp/api/stata_do.py`
4. Document in `docs/security.md`
5. Add tests if applicable

#### 3. Monitoring Features

When adding monitoring features:

1. Extend `src/stata_mcp/monitor/base.py`
2. Create new monitor class
3. Document in `docs/monitoring.md`
4. Ensure graceful degradation when disabled

### Testing Guidelines

Before submitting a PR:

1. **Test locally**: Use `uvx stata-mcp --usable` to verify installation
2. **Test configuration**: Verify config file parsing
3. **Test cross-platform**: Check macOS, Windows, Linux if possible
4. **Test security features**: Verify guard validation works
5. **Document changes**: Update relevant documentation

### Documentation Updates

When making changes, ensure you:

1. **Update CLAUDE.md** for architectural changes
2. **Update docs/** for user-facing features
3. **Update README.md** for major features
4. **Add examples** for new functionality
5. **Update CHANGELOG.md** for releases

### Getting Help

- **Documentation**: See [sepinetam.github.io/mcp-for-stata](https://sepinetam.github.io/mcp-for-stata/) for complete guides
- **Architecture**: Read [Architecture Overview](https://sepinetam.github.io/mcp-for-stata/overview) for system design
- **Configuration**: Refer to [Configuration Guide](https://sepinetam.github.io/mcp-for-stata/configuration)
- **Security**: Check [Security Guard](https://sepinetam.github.io/mcp-for-stata/security)
- **Monitoring**: See [Monitoring System](https://sepinetam.github.io/mcp-for-stata/monitoring)

## Issue Reporting

When reporting issues, please include:

1. **Stata-MCP version**: `stata-mcp --version`
2. **Operating system**: macOS/Windows/Linux with version
3. **Stata version**: Stata 17/18 with MP/SE/BE variant
4. **Error messages**: Complete error traceback
5. **Steps to reproduce**: Minimal reproducible example
6. **Configuration**: Relevant parts of `~/.statamcp/config.toml` (without sensitive data)

## Feature Requests

For feature requests:

1. Check [existing issues](https://github.com/sepinetam/stata-mcp/issues) first
2. Describe the use case clearly
3. Explain why it's important
4. Suggest a possible implementation (if you have ideas)
5. Consider if it fits the project's scope and philosophy
