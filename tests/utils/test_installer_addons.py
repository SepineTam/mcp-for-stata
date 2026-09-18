"""Isolated acceptance tests for GitHub payloads, ownership, and CLI integration."""

from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path
from unittest.mock import Mock

import pytest

from stata_mcp.cli._handlers import handle_install
from stata_mcp.cli._parsers import add_install_parser
from stata_mcp.utils.installer import Installer
from stata_mcp.utils.installer.addon_lsp import install_lsp
from stata_mcp.utils.installer.addon_source import AddonError, Bundle, GitHubSource, safe_relative_path
from stata_mcp.utils.installer.addon_store import ManagedStore
from stata_mcp.utils.installer.addons import AddonInstaller, convert_server, replace_toml_server

COMMIT = "a" * 40
SKILL = {
    "skills/stata-skill/SKILL.md": b"---\nname: stata-skill\ndescription: Stata\n---\nStata",
    "skills/stata-skill/references/example.md": b"reference",
    "skills/stata-skill/scripts/check.py": b"print(1)",
}
SERVERS = {
    "dip": {"type": "http", "url": "https://example.com/mcp"},
    "nber-mcp": {"type": "stdio", "command": "uvx", "args": ["nber-cli", "mcp-server"]},
}


@pytest.fixture(autouse=True)
def isolated_home(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.setattr(Installer, "STATA_CLI", property(lambda self: "/test/stata"))
    monkeypatch.setattr(Installer, "install_from_cli", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        "stata_mcp.utils.installer.addon_source.requests.get", Mock(side_effect=AssertionError("Unexpected network"))
    )


def parser():
    root = argparse.ArgumentParser()
    add_install_parser(root.add_subparsers(dest="command"))
    return root


def payload(group="addon", files=None):
    return Bundle(group, COMMIT, SKILL.copy() if files is None else files)


@pytest.mark.parametrize(
    "switches,addon,extra",
    [
        ([], True, False),
        (["--no-addon"], False, False),
        (["--with-extra"], True, True),
        (["--no-addon", "--with-extra"], False, True),
        (["--with-addon", "--no-extra"], True, False),
    ],
)
def test_cli_switches_drive_download_selection(switches, addon, extra, monkeypatch, tmp_path):
    fetch = Mock(side_effect=lambda group: payload(group))
    monkeypatch.setattr(GitHubSource, "fetch", fetch)
    assert handle_install(parser().parse_args(["install", "-c", "codex", *switches])) == 0
    assert [call.args[0] for call in fetch.call_args_list] == [
        name for name, enabled in (("addon", addon), ("extra", extra)) if enabled
    ]
    assert (tmp_path / ".codex/config.toml").exists()


@pytest.mark.parametrize("flags", [["--with-addon", "--no-addon"], ["--with-extra", "--no-extra"], ["--no-with-addon"]])
def test_cli_rejects_ambiguous_flags(flags):
    with pytest.raises(SystemExit):
        parser().parse_args(["install", *flags])


@pytest.mark.parametrize(
    "client,relative",
    [
        ("cc", ".claude/skills"),
        ("codex", ".agents/skills"),
        ("gemini", ".gemini/skills"),
        ("opencode", ".config/opencode/skills"),
    ],
)
def test_complete_skill_is_installed_and_existing_mcp_does_not_exit(client, relative, monkeypatch, tmp_path):
    monkeypatch.setattr(GitHubSource, "fetch", lambda self, group: payload(group))
    args = parser().parse_args(["install", "-c", client])
    assert handle_install(args) == 0
    assert handle_install(args) == 0
    for name, data in SKILL.items():
        assert (tmp_path / relative / name.removeprefix("skills/")).read_bytes() == data
    manifest = json.loads((tmp_path / ".statamcp/addons-v1.json").read_bytes())
    assert len(manifest["entries"]) == 3
    assert all(record["source_commit"] == COMMIT for record in manifest["entries"].values())


@pytest.mark.parametrize(
    "client,relative",
    [
        ("cursor", ".cursor/skills"),
        ("copilot", ".copilot/skills"),
        ("openclaw", ".openclaw/skills"),
        ("pi", ".pi/agent/skills"),
    ],
)
def test_additional_skill_locations(client, relative, monkeypatch, tmp_path):
    monkeypatch.setattr(GitHubSource, "fetch", lambda self, group: payload(group))
    AddonInstaller(Installer(is_env=False)).install(client)
    assert (tmp_path / relative / "stata-skill/SKILL.md").read_bytes() == SKILL["skills/stata-skill/SKILL.md"]


def test_offline_does_not_undo_mcp_install(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(GitHubSource, "fetch", Mock(side_effect=AddonError("offline")))
    assert handle_install(parser().parse_args(["install", "-c", "codex"])) == 0
    assert "stata-mcp" in tomllib.loads((tmp_path / ".codex/config.toml").read_text())["mcp_servers"]
    assert "offline" in capsys.readouterr().out


def test_all_clients_deduplicates_aliases_and_continues_after_failure(monkeypatch):
    regular, duplicate, failure, pi = Mock(), Mock(), Mock(side_effect=SystemExit(1)), Mock()
    monkeypatch.setattr(
        Installer,
        "client_function_mapping",
        property(
            lambda self: {
                "cc": duplicate,
                "claude-code": duplicate,
                "bad": failure,
                "regular": regular,
                "pi": pi,
            }
        ),
    )
    installer = Installer(is_env=False)
    installer.addons = Mock()
    assert installer.install_all() is False
    duplicate.assert_called_once()
    regular.assert_called_once()
    pi.assert_not_called()
    assert len(installer.addons.install.call_args_list) == 2


def test_cursor_arguments_do_not_leak_to_later_clients(monkeypatch):
    installer = Installer(is_env=False)
    monkeypatch.setattr(installer, "install_to_json_config", Mock())
    installer.install("cursor")
    assert installer.args == ["stata-mcp"]
    assert installer.env == {}


def test_local_edit_preserves_entire_skill_during_upgrade(tmp_path):
    target = tmp_path / "skills/example"
    with ManagedStore().locked() as store:
        store.install_files(target, {"SKILL.md": b"old", "ref.md": b"old ref"}, payload(), "codex", "skill")
    (target / "ref.md").write_bytes(b"user edit")
    with ManagedStore().locked() as store:
        store.install_files(target, {"SKILL.md": b"new", "ref.md": b"new ref"}, payload(), "codex", "skill")
    assert (target / "SKILL.md").read_bytes() == b"old"
    assert (target / "ref.md").read_bytes() == b"user edit"


def test_managed_skill_upgrades_but_identical_foreign_file_is_not_adopted(tmp_path):
    target = tmp_path / "skills/example"
    target.mkdir(parents=True)
    (target / "user.md").write_bytes(b"same")
    with ManagedStore().locked() as store:
        store.install_files(target, {"SKILL.md": b"old", "user.md": b"same"}, payload(), "codex", "skill")
    with ManagedStore().locked() as store:
        store.install_files(target, {"SKILL.md": b"new", "user.md": b"same"}, payload(), "codex", "skill")
        assert str(target / "user.md") not in store.records
    assert (target / "SKILL.md").read_bytes() == b"new"


def test_manifest_failure_rolls_back_component(tmp_path, monkeypatch):
    target = tmp_path / "skills/example"
    with ManagedStore().locked() as store:
        store.install_files(target, {"SKILL.md": b"old"}, payload(), "cc", "skill")
    with ManagedStore().locked() as store:
        monkeypatch.setattr(store, "_save", Mock(side_effect=OSError("disk full")))
        with pytest.raises(OSError):
            store.install_files(target, {"SKILL.md": b"new", "ref.md": b"ref"}, payload(), "cc", "skill")
    assert (target / "SKILL.md").read_bytes() == b"old"
    assert not (target / "ref.md").exists()


def test_symlink_target_is_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    target = tmp_path / "skills"
    target.symlink_to(outside, target_is_directory=True)
    with ManagedStore().locked() as store, pytest.raises(AddonError, match="Symbolic link"):
        store.install_files(target, {"SKILL.md": b"text"}, payload(), "cc", "skill")
    assert not list(outside.iterdir())


def test_concurrent_manifest_writer_is_refused():
    with ManagedStore().locked(), pytest.raises(AddonError, match="Another addon"):
        with ManagedStore().locked():
            pytest.fail("Lock acquired twice")


@pytest.mark.parametrize("client", ["codex", "cc", "gemini", "opencode", "workbuddy"])
def test_extra_mcp_and_future_skills_share_directory(client, monkeypatch, tmp_path):
    files = {**SKILL, "mcp.json": json.dumps({"mcpServers": SERVERS}).encode()}
    monkeypatch.setattr(GitHubSource, "fetch", lambda self, group: payload(group, files))
    assert handle_install(parser().parse_args(["install", "-c", client, "--no-addon", "--with-extra"])) == 0
    installer = Installer(is_env=False)
    path = installer.find_config_path(client)
    if client == "codex":
        entries = tomllib.loads(path.read_text())["mcp_servers"]
    else:
        entries = json.loads(path.read_text())[installer.find_default_index(client)]
    assert {"dip", "nber-mcp", "stata-mcp"} <= entries.keys()
    assert entries["dip"] == convert_server(Installer.CLIENT_ALIASES.get(client, client), SERVERS["dip"])


def test_custom_json_nested_index_and_existing_entry_are_preserved(monkeypatch, tmp_path):
    files = {"mcp.json": json.dumps({"mcpServers": SERVERS}).encode()}
    monkeypatch.setattr(GitHubSource, "fetch", lambda self, group: payload(group, files))
    path = tmp_path / "custom.json"
    path.write_text(json.dumps({"untouched": [1, 2], "mcp": {"servers": {"dip": {"url": "https://user.example"}}}}))
    args = parser().parse_args(
        ["install", "--json-file", str(path), "--json-index", "mcp.servers", "--no-addon", "--with-extra"]
    )
    assert handle_install(args) == 0
    config = json.loads(path.read_bytes())
    assert config["untouched"] == [1, 2]
    assert config["mcp"]["servers"]["dip"] == {"url": "https://user.example"}
    assert "nber-mcp" in config["mcp"]["servers"]


def test_extra_upgrades_managed_entries_without_changing_other_entries(monkeypatch, tmp_path):
    files = {"mcp.json": json.dumps({"mcpServers": SERVERS}).encode()}
    monkeypatch.setattr(GitHubSource, "fetch", lambda self, group: payload(group, files))
    args = parser().parse_args(["install", "-c", "codex", "--no-addon", "--with-extra"])
    handle_install(args)
    path = tmp_path / ".codex/config.toml"
    with path.open("a") as stream:
        stream.write('\n# Keep this user comment\n[mcp_servers.other]\ncommand = "mine"\n')
    files["mcp.json"] = json.dumps({"mcpServers": {"dip": {"url": "https://new.example/mcp"}}}).encode()
    handle_install(args)
    assert tomllib.loads(path.read_text())["mcp_servers"]["dip"]["url"] == "https://new.example/mcp"
    assert tomllib.loads(path.read_text())["mcp_servers"]["other"]["command"] == "mine"
    assert "Keep this user comment" in path.read_text()


def test_toml_unrelated_comments_survive():
    original = b'# user preference\nmodel = "user-model"\n[mcp_servers.other]\ncommand = "other"\n'
    added = replace_toml_server(original, "dip", {"url": "https://example.com"}, False)
    assert added.startswith(original)
    changed = replace_toml_server(added, "dip", {"url": "https://new.example.com"}, True)
    assert changed.startswith(original)


def test_bundle_with_misplaced_servers_is_reported(monkeypatch, capsys):
    monkeypatch.setattr(
        GitHubSource, "fetch", lambda self, group: payload(group, {"mcp.json": b'{"mcpServers": {}, "misplaced": {}}'})
    )
    assert handle_install(parser().parse_args(["install", "-c", "codex", "--with-extra"])) == 0
    assert "inside mcpServers" in capsys.readouterr().out


@pytest.mark.parametrize(
    "path",
    [
        ".",
        "../bad",
        "/absolute",
        "skills/../../bad",
        "a\\b",
        "C:/bad",
        "a//b",
        "a/./b",
        "trailing.",
        "line\nbreak",
        "con",
        "scripts/NUL.txt",
    ],
)
def test_bad_remote_paths(path):
    with pytest.raises(AddonError):
        safe_relative_path(path)


def test_github_resolves_commit_verifies_blobs_and_caches(monkeypatch):
    data = b"skill"
    path = "plugins/stata-toolbox/skills/example/SKILL.md"
    tree = {
        "tree": [
            {
                "path": path,
                "type": "blob",
                "mode": "100644",
                "size": len(data),
                "sha": hashlib.sha1(b"blob 5\0" + data).hexdigest(),
            }
        ],
        "truncated": False,
    }
    get = Mock(side_effect=[json.dumps({"sha": COMMIT}).encode(), json.dumps(tree).encode(), data])
    source = GitHubSource("release/test")
    monkeypatch.setattr(source, "_get", get)
    first = source.fetch("addon")
    assert source.fetch("addon") is first
    assert first.commit == COMMIT
    assert "release%2Ftest" in get.call_args_list[0].args[0]
    assert f"/{COMMIT}/" in get.call_args_list[2].args[0]
    assert get.call_count == 3


@pytest.mark.parametrize(
    "mode,sha,truncated", [("120000", "a" * 40, False), ("100644", "b" * 40, False), ("100644", "a" * 40, True)]
)
def test_bad_github_payloads_fail_closed_and_failure_is_cached(mode, sha, truncated, monkeypatch):
    tree = {
        "tree": [
            {
                "path": "plugins/stata-toolbox/skills/example/SKILL.md",
                "mode": mode,
                "sha": sha,
                "size": 5,
                "type": "blob",
            }
        ],
        "truncated": truncated,
    }
    get = Mock(side_effect=[json.dumps({"sha": COMMIT}).encode(), json.dumps(tree).encode(), b"skill"])
    source = GitHubSource()
    monkeypatch.setattr(source, "_get", get)
    with pytest.raises(AddonError):
        source.fetch("addon")
    count = get.call_count
    with pytest.raises(AddonError):
        source.fetch("addon")
    assert count == get.call_count


def test_http_redirect_is_not_followed(monkeypatch):
    response = Mock(status_code=302)
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    get = Mock(return_value=response)
    monkeypatch.setattr("stata_mcp.utils.installer.addon_source.requests.get", get)
    source = GitHubSource()
    with pytest.raises(AddonError, match="302"):
        source.fetch("addon")
    assert get.call_args.kwargs["allow_redirects"] is False


def test_missing_lsp_program_does_not_bootstrap_it(monkeypatch, capsys):
    monkeypatch.setattr(
        "stata_mcp.utils.installer.addon_lsp.shutil.which", lambda name: "/test/claude" if name == "claude" else None
    )
    run = Mock(side_effect=AssertionError("Must not execute an installer"))
    monkeypatch.setattr("stata_mcp.utils.installer.addon_lsp.subprocess.run", run)
    with ManagedStore().locked() as store:
        install_lsp({"stata": {"command": "stata-language-server"}}, payload(), "claude-code", store)
    run.assert_not_called()
    assert "install it separately" in capsys.readouterr().out


def test_native_lsp_plugin_excludes_duplicate_mcp_and_skills(monkeypatch, tmp_path):
    monkeypatch.setattr("stata_mcp.utils.installer.addon_lsp.shutil.which", lambda name: f"/test/{name}")
    run = Mock(return_value=Mock(returncode=0, stdout="[]"))
    monkeypatch.setattr("stata_mcp.utils.installer.addon_lsp.subprocess.run", run)
    definitions = {"stata": {"command": "stata-language-server", "extensionToLanguage": {".do": "stata"}}}
    with ManagedStore().locked() as store:
        install_lsp(definitions, payload(), "claude-code", store)
    root = tmp_path / ".statamcp/addon-plugins/addon"
    manifest = json.loads((root / "plugin/.claude-plugin/plugin.json").read_bytes())
    assert manifest["lspServers"] == definitions
    assert manifest["version"] == f"0.0.0-g{COMMIT[:12]}"
    assert "mcpServers" not in manifest and "skills" not in manifest
    assert run.call_args_list[1].args[0][-3:] == ["marketplace", "add", str(root)]
    assert run.call_args_list[2].args[0][-3:] == ["stata-mcp-addon-lsp@stata-mcp-addon-managed", "--scope", "user"]


def test_native_toolbox_avoids_duplicate_lsp_registration(monkeypatch, tmp_path):
    monkeypatch.setattr("stata_mcp.utils.installer.addon_lsp.shutil.which", lambda name: f"/test/{name}")
    listing = json.dumps([{"id": "stata-toolbox@stata-plugin-lib", "enabled": True}])
    run = Mock(return_value=Mock(returncode=0, stdout=listing))
    monkeypatch.setattr("stata_mcp.utils.installer.addon_lsp.subprocess.run", run)
    with ManagedStore().locked() as store:
        install_lsp({"stata": {"command": "stata-language-server"}}, payload(), "claude-code", store)
    run.assert_called_once()
    assert not (tmp_path / ".statamcp/addon-plugins").exists()


def test_native_toolbox_does_not_suppress_external_lsp(monkeypatch):
    monkeypatch.setattr("stata_mcp.utils.installer.addon_lsp.shutil.which", lambda name: f"/test/{name}")
    listing = json.dumps([{"id": "stata-toolbox@stata-plugin-lib", "enabled": True}])
    run = Mock(return_value=Mock(returncode=0, stdout=listing))
    monkeypatch.setattr("stata_mcp.utils.installer.addon_lsp.subprocess.run", run)
    with ManagedStore().locked() as store:
        install_lsp({"python": {"command": "example-lsp"}}, payload("extra"), "claude-code", store)
    assert run.call_args.args[0][-3:] == ["stata-mcp-extra-lsp@stata-mcp-extra-managed", "--scope", "user"]


def test_user_disabled_lsp_plugin_stays_disabled(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("stata_mcp.utils.installer.addon_lsp.shutil.which", lambda name: f"/test/{name}")
    listing = json.dumps([{"id": "stata-mcp-addon-lsp@stata-mcp-addon-managed", "enabled": False}])
    run = Mock(return_value=Mock(returncode=0, stdout=listing))
    monkeypatch.setattr("stata_mcp.utils.installer.addon_lsp.subprocess.run", run)
    with ManagedStore().locked() as store:
        install_lsp({"stata": {"command": "stata-language-server"}}, payload(), "claude-code", store)
    run.assert_called_once()
    assert not (tmp_path / ".statamcp/addon-plugins").exists()
    assert "leaving it disabled" in capsys.readouterr().out


def test_lsp_failure_does_not_prevent_extra_mcp_install(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("stata_mcp.utils.installer.addons.install_lsp", Mock(side_effect=AddonError("test failure")))
    files = {**SKILL, "mcp.json": json.dumps({"mcpServers": SERVERS}).encode()}
    monkeypatch.setattr(GitHubSource, "fetch", lambda self, group: payload(group, files))
    assert handle_install(parser().parse_args(["install", "-c", "cc", "--with-extra"])) == 0
    assert "nber-mcp" in json.loads((tmp_path / ".claude.json").read_bytes())["mcpServers"]
    assert "LSP setup incomplete" in capsys.readouterr().out


@pytest.mark.parametrize(
    "content",
    [b"[]", b"{", b'{"schema_version": 9, "entries": {}}', b'{"schema_version": 1, "entries": {"file": false}}'],
)
def test_broken_manifest_does_not_allow_overwrites(tmp_path, content):
    root = tmp_path / ".statamcp"
    root.mkdir()
    (root / "addons-v1.json").write_bytes(content)
    with pytest.raises(ValueError):
        with ManagedStore().locked():
            pytest.fail("Invalid manifest accepted")
    assert not (root / "addons.lock").exists()


def test_upstream_deletion_leaves_old_skill_intact(tmp_path):
    target = tmp_path / "skill"
    with ManagedStore().locked() as store:
        store.install_files(target, {"SKILL.md": b"old", "ref.md": b"ref"}, payload(), "codex", "skill")
    with ManagedStore().locked() as store:
        assert store.install_files(target, {"SKILL.md": b"new"}, payload(), "codex", "skill") is False
    assert (target / "SKILL.md").read_bytes() == b"old"
    assert (target / "ref.md").read_bytes() == b"ref"


def test_all_uses_one_snapshot_and_reuses_payload(monkeypatch, tmp_path):
    source = GitHubSource()
    source._cache["addon"] = payload()
    source._cache["extra"] = payload("extra", {"mcp.json": json.dumps({"mcpServers": SERVERS}).encode()})
    installer = Installer(is_env=False)
    installer.addons = AddonInstaller(installer, extra=True)
    installer.addons.source = source
    monkeypatch.setattr(
        Installer,
        "client_function_mapping",
        property(
            lambda self: {
                "codex": self.install_to_codex,
                "gemini": self.install_to_gemini,
            }
        ),
    )
    assert installer.install_all() is True
    for path in (tmp_path / ".codex/config.toml", tmp_path / ".gemini/settings.json"):
        assert "nber-mcp" in path.read_text()


def test_explicit_ref_is_used_by_cli(monkeypatch):
    refs = []

    def fetch(self, group):
        refs.append(self.ref)
        return payload(group)

    monkeypatch.setattr(GitHubSource, "fetch", fetch)
    assert handle_install(parser().parse_args(["install", "-c", "codex", "--addon-ref", COMMIT])) == 0
    assert refs == [COMMIT]


def test_existing_null_mcp_entry_is_not_claimed(monkeypatch, tmp_path):
    files = {"mcp.json": json.dumps({"mcpServers": SERVERS}).encode()}
    monkeypatch.setattr(GitHubSource, "fetch", lambda self, group: payload(group, files))
    path = tmp_path / "config.json"
    path.write_text('{"mcpServers": {"dip": null}}')
    args = parser().parse_args(["install", "--json-file", str(path), "--no-addon", "--with-extra"])
    assert handle_install(args) == 0
    assert json.loads(path.read_bytes())["mcpServers"]["dip"] is None


@pytest.mark.parametrize(
    "client,variable,config_name",
    [
        ("codex", "CODEX_HOME", "config.toml"),
        ("claude-code", "CLAUDE_CONFIG_DIR", ".claude.json"),
        ("opencode", "XDG_CONFIG_HOME", "opencode/opencode.json"),
    ],
)
def test_base_and_extra_use_the_same_custom_client_directory(client, variable, config_name, monkeypatch, tmp_path):
    custom = tmp_path / "custom"
    monkeypatch.setenv(variable, str(custom))
    files = {"mcp.json": json.dumps({"mcpServers": SERVERS}).encode()}
    monkeypatch.setattr(GitHubSource, "fetch", lambda self, group: payload(group, files))
    assert handle_install(parser().parse_args(["install", "-c", client, "--no-addon", "--with-extra"])) == 0
    path = custom / config_name
    assert path.is_file()
    document = tomllib.loads(path.read_text()) if client == "codex" else json.loads(path.read_text())
    key = {"codex": "mcp_servers", "claude-code": "mcpServers", "opencode": "mcp"}[client]
    assert {"stata-mcp", "dip", "nber-mcp"} <= document[key].keys()
    assert Installer(is_env=False).find_config_path(client) == path


def test_opencode_base_mcp_uses_environment_field(monkeypatch, tmp_path):
    Installer(is_env=True).install("opencode")
    config = json.loads((tmp_path / ".config/opencode/opencode.json").read_text())
    assert config["mcp"]["stata-mcp"]["environment"] == {"STATA_CLI": "/test/stata"}
    assert "env" not in config["mcp"]["stata-mcp"]


@pytest.mark.parametrize(
    "client,expected",
    [
        ("claude-code", {"type": "http", "url": "https://example.com/mcp"}),
        ("codex", {"url": "https://example.com/mcp"}),
        ("gemini", {"httpUrl": "https://example.com/mcp"}),
        ("opencode", {"type": "remote", "url": "https://example.com/mcp"}),
        ("cline", {"type": "streamableHttp", "url": "https://example.com/mcp"}),
        ("openclaw", {"transport": "streamable-http", "url": "https://example.com/mcp"}),
        ("copilot", {"type": "http", "tools": ["*"], "url": "https://example.com/mcp"}),
    ],
)
def test_http_entries_follow_independent_client_contracts(client, expected):
    assert convert_server(client, SERVERS["dip"]) == expected


@pytest.mark.parametrize("platform", ["darwin", "linux", "win32"])
@pytest.mark.parametrize(
    "client",
    [
        "claude",
        "claude-code",
        "codex",
        "gemini",
        "opencode",
        "cursor",
        "cline",
        "copilot",
        "openclaw",
        "workbuddy",
        "pi",
        "hermes-agent",
        "dsh",
    ],
)
def test_client_platform_install_matrix(platform, client, monkeypatch, tmp_path, capsys):
    """Verify generated configuration, not actual availability of client binaries."""
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData/Roaming"))
    monkeypatch.setenv("DSH_HOME", str(tmp_path / ".dsh"))
    monkeypatch.setattr(Installer, "is_pi_available", staticmethod(lambda: False))
    files = {**SKILL, "mcp.json": json.dumps({"mcpServers": SERVERS}).encode()}
    monkeypatch.setattr(GitHubSource, "fetch", lambda self, group: payload(group, files))
    installer = Installer(sys_os=platform)
    installer.addons = AddonInstaller(installer, extra=True)
    if client == "claude" and platform == "linux":
        with pytest.raises(SystemExit) as error:
            installer.install(client)
        assert error.value.code == 1
        return
    installer.install(client)
    installer.install(client)
    paths = {
        "claude": (
            "Library/Application Support/Claude/claude_desktop_config.json"
            if platform == "darwin"
            else "AppData/Roaming/Claude/claude_desktop_config.json"
        ),
        "claude-code": ".claude.json",
        "codex": ".codex/config.toml",
        "gemini": ".gemini/settings.json",
        "opencode": ".config/opencode/opencode.json",
        "cursor": ".cursor/mcp.json",
        "copilot": ".copilot/mcp-config.json",
        "openclaw": ".openclaw/openclaw.json",
        "workbuddy": ".workbuddy/mcp.json",
        "pi": ".pi/agent/mcp.json",
        "hermes-agent": ".hermes/config.yaml",
        "dsh": ".dsh/profiles/web/cordis.patch.yml",
    }
    cline_root = {"darwin": "Library/Application Support", "linux": ".config", "win32": "AppData/Roaming"}[platform]
    paths["cline"] = f"{cline_root}/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
    path = tmp_path / paths[client]
    assert path.is_file()
    output = capsys.readouterr().out
    if client in {"hermes-agent", "dsh"}:
        assert "not supported by this adapter" in output
        assert "nber-mcp" not in path.read_text()
    else:
        document = tomllib.loads(path.read_text()) if client == "codex" else json.loads(path.read_text())
        if client == "codex":
            entries = document["mcp_servers"]
        elif client == "opencode":
            entries = document["mcp"]
        elif client == "openclaw":
            entries = document["mcp"]["servers"]
        else:
            entries = document["mcpServers"]
        assert {"stata-mcp", "nber-mcp"} <= entries.keys()
        assert ("dip" in entries) == (client not in {"claude", "pi"})
    if client == "pi":
        assert "not active yet" in output
