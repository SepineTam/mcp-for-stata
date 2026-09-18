"""Ownership-aware writes for downloaded skills and individual configuration entries."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .addon_source import AddonError, Bundle, safe_relative_path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def check_path(path: Path) -> Path:
    """Reject symlinks rather than writing through user-selected redirects."""
    path = Path(os.path.abspath(path))
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise AddonError(f"Symbolic link is not an installation target: {parent}")
    return path


def atomic_write(path: Path, data: bytes) -> None:
    path = check_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            temporary_path.chmod(path.stat().st_mode & 0o777)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


class ManagedStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.home() / ".statamcp"
        self.manifest_path = self.root / "addons-v1.json"
        self.records: dict[str, dict] = {}

    @contextmanager
    def locked(self):
        """Serialize manifest updates; a crashed install requires explicit lock recovery."""
        check_path(self.root).mkdir(parents=True, exist_ok=True)
        lock = check_path(self.root / "addons.lock")
        try:
            descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            raise AddonError(f"Another addon installation holds {lock}; retry when it finishes") from error
        try:
            with os.fdopen(descriptor, "w") as stream:
                stream.write(str(os.getpid()))
            manifest = check_path(self.manifest_path)
            if manifest.exists():
                saved = json.loads(manifest.read_bytes())
                if (
                    not isinstance(saved, dict)
                    or saved.get("schema_version") != 1
                    or not isinstance(saved.get("entries"), dict)
                ):
                    raise AddonError("Unsupported addon manifest; existing installations were left unchanged")
                if any(not isinstance(value, dict) for value in saved["entries"].values()):
                    raise AddonError("Invalid addon ownership records")
                self.records = saved["entries"]
            yield self
        finally:
            lock.unlink()

    def _save(self) -> None:
        atomic_write(self.manifest_path, json_bytes({"schema_version": 1, "entries": self.records}))

    def _decision(self, key: str, current: bytes | None, incoming: bytes, group: str) -> str:
        record = self.records.get(key)
        if current is None:
            return "INSTALL"
        if current == incoming:
            return "SKIP"
        if record and record.get("group") == group and record.get("sha256") == digest(current):
            return "UPGRADE"
        return "CONFLICT"

    def _record(self, key: str, data: bytes, bundle: Bundle, client: str, kind: str) -> None:
        self.records[key] = {
            "client": client,
            "group": bundle.group,
            "kind": kind,
            "sha256": digest(data),
            "source_commit": bundle.commit,
            "source_path": "plugins/stata-toolbox" if bundle.group == "addon" else "plugins/external",
            "installed_at": datetime.now(timezone.utc).isoformat(),
        }

    def install_files(self, target: Path, files: dict[str, bytes], bundle: Bundle, client: str, kind: str) -> bool:
        """Preflight a whole component, then roll back writes if any file fails."""
        target = check_path(target)
        changes: list[tuple[Path, bytes | None, bytes]] = []
        for relative, data in sorted(files.items()):
            destination = check_path(target / safe_relative_path(relative))
            current = destination.read_bytes() if destination.exists() else None
            decision = self._decision(str(destination), current, data, bundle.group)
            if decision == "CONFLICT":
                print(f"[SKIP]\t{client}: {kind} {target.name}: local file differs ({relative}); component unchanged")
                return False
            if decision != "SKIP":
                changes.append((destination, current, data))
        # Do not leave a mixture of old and new versions when upstream removes files.
        for key, record in self.records.items():
            if record.get("kind") != kind or record.get("group") != bundle.group:
                continue
            old = Path(key)
            if old.is_relative_to(target) and old.exists() and old.relative_to(target).as_posix() not in files:
                print(f"[SKIP]\t{client}: {kind} {target.name}: upstream removed files; review {target}")
                return False
        if not changes:
            print(f"[SKIP]\t{client}: {kind} {target.name}: already present")
            return True
        previous_records = self.records.copy()
        written: list[tuple[Path, bytes | None]] = []
        try:
            for destination, current, data in changes:
                if (destination.read_bytes() if destination.exists() else None) != current:
                    raise AddonError(f"File changed during installation: {destination}; retry")
                atomic_write(destination, data)
                written.append((destination, current))
                self._record(str(destination), data, bundle, client, kind)
            self._save()
        except (OSError, AddonError):
            self.records = previous_records
            for destination, current in reversed(written):
                if current is None:
                    destination.unlink(missing_ok=True)
                else:
                    atomic_write(destination, current)
            raise
        print(f"[DONE]\t{client}: {kind} {target.name} ({len(changes)} files, {bundle.commit[:12]})")
        return True

    def install_entry(
        self,
        path: Path,
        key: str,
        current: object | None,
        incoming: object,
        content: bytes,
        original: bytes | None,
        bundle: Bundle,
        client: str,
    ) -> None:
        path = check_path(path)
        record_key = f"{path}#{key}"
        incoming_bytes = json_bytes(incoming)
        decision = self._decision(
            record_key, None if current is None else json_bytes(current), incoming_bytes, bundle.group
        )
        if decision == "CONFLICT":
            print(f"[SKIP]\t{client}: {key}: existing configuration differs; not overwritten")
            return
        if decision == "SKIP":
            print(f"[SKIP]\t{client}: {key}: already present")
            return
        if (path.read_bytes() if path.exists() else None) != original:
            raise AddonError(f"Configuration changed during installation: {path}; retry")
        if original is not None:
            backup = self.root / "addon-backups" / f"{digest(str(path).encode())[:16]}-{digest(original)}{path.suffix}"
            atomic_write(backup, original)
        previous_records = self.records.copy()
        atomic_write(path, content)
        try:
            self._record(record_key, incoming_bytes, bundle, client, "config-entry")
            self._save()
        except (OSError, AddonError):
            self.records = previous_records
            if original is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, original)
            raise
        print(f"[{decision}]\t{client}: {key}")
