"""Fetch optional payloads from the official repository at one immutable commit."""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import quote

import requests

REPOSITORY = "SepineTam/mcp-for-stata"
BUNDLE_PATHS = {"addon": "plugins/stata-toolbox", "extra": "plugins/external"}
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_BUNDLE_BYTES = 16 * 1024 * 1024
MAX_FILES = 256


class AddonError(ValueError):
    """An optional component cannot be installed safely."""


def safe_relative_path(value: str) -> PurePosixPath:
    """Accept only portable, normalized paths inside a bundle."""
    path = PurePosixPath(value)
    if (
        not value
        or not path.parts
        or path.is_absolute()
        or path.as_posix() != value
        or any(part in {".", ".."} for part in path.parts)
        or any(character in value for character in "\\:\x00")
        or any(ord(character) < 32 for character in value)
        or any(part.endswith((".", " ")) for part in path.parts)
        or any(re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part) for part in path.parts)
    ):
        raise AddonError(f"Invalid bundle path: {value!r}")
    return path


@dataclass(frozen=True)
class Bundle:
    group: str
    commit: str
    files: dict[str, bytes]


class GitHubSource:
    """Download each selected directory once, never following HTTP redirects."""

    def __init__(self, ref: str = "master") -> None:
        if not ref or len(ref) > 200 or any(ord(char) < 32 for char in ref):
            raise AddonError("Invalid GitHub ref")
        self.ref = ref
        self.commit = ""
        self._tree: list[dict] | None = None
        self._cache: dict[str, Bundle | str] = {}
        self._failure: str | None = None
        self._deadline = 0.0

    def _get(self, url: str, limit: int) -> bytes:
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise AddonError("GitHub download time limit exceeded")
        try:
            with requests.get(
                url,
                timeout=(min(5, remaining), min(10, remaining)),
                headers={"User-Agent": "stata-mcp-addon-installer"},
                stream=True,
                allow_redirects=False,
            ) as response:
                if response.status_code != 200:
                    raise AddonError(f"GitHub returned HTTP {response.status_code}")
                content = bytearray()
                for chunk in response.iter_content(65536):
                    content.extend(chunk)
                    if len(content) > limit:
                        raise AddonError("GitHub response exceeds the size limit")
                    if time.monotonic() > self._deadline:
                        raise AddonError("GitHub download time limit exceeded")
                return bytes(content)
        except requests.RequestException as error:
            raise AddonError(f"GitHub download failed ({type(error).__name__})") from error

    def _load_tree(self) -> list[dict]:
        if self._failure:
            raise AddonError(self._failure)
        if self._tree is None:
            try:
                base = f"https://api.github.com/repos/{REPOSITORY}"
                commit = json.loads(self._get(f"{base}/commits/{quote(self.ref, safe='')}", MAX_FILE_BYTES))
                if not isinstance(commit, dict):
                    raise AddonError("Invalid GitHub commit response")
                self.commit = commit["sha"]
                if not isinstance(self.commit, str) or not re.fullmatch(r"[0-9a-f]{40}", self.commit):
                    raise AddonError("Invalid GitHub commit response")
                tree = json.loads(self._get(f"{base}/git/trees/{self.commit}?recursive=1", MAX_BUNDLE_BYTES))
                if not isinstance(tree, dict) or tree.get("truncated") or not isinstance(tree.get("tree"), list):
                    raise AddonError("GitHub returned an incomplete repository tree")
                if any(not isinstance(item, dict) or not isinstance(item.get("path"), str) for item in tree["tree"]):
                    raise AddonError("Invalid GitHub tree entries")
                self._tree = tree["tree"]
            except (KeyError, TypeError, ValueError) as error:
                self._failure = str(error)
                raise AddonError(f"Cannot read GitHub source: {error}") from error
        return self._tree

    def fetch(self, group: str) -> Bundle:
        cached = self._cache.get(group)
        if isinstance(cached, Bundle):
            return cached
        if isinstance(cached, str):
            raise AddonError(cached)
        self._deadline = time.monotonic() + 90
        try:
            prefix = BUNDLE_PATHS[group] + "/"
            entries = [item for item in self._load_tree() if item.get("path", "").startswith(prefix)]
            files: dict[str, bytes] = {}
            seen: set[str] = set()
            total = 0
            for item in entries:
                relative = item["path"][len(prefix) :]
                safe_relative_path(relative)
                if item.get("type") == "tree":
                    continue
                if item.get("type") != "blob" or item.get("mode") not in {"100644", "100755"}:
                    raise AddonError(f"Unsupported Git object: {relative}")
                if relative.casefold() in seen:
                    raise AddonError(f"Duplicate bundle path: {relative}")
                seen.add(relative.casefold())
                size = item.get("size", MAX_FILE_BYTES + 1)
                if not isinstance(size, int) or size < 0 or size > MAX_FILE_BYTES:
                    raise AddonError(f"Oversized bundle file: {relative}")
                total += size
                if total > MAX_BUNDLE_BYTES or len(seen) > MAX_FILES:
                    raise AddonError("Bundle exceeds the size/file-count limit")
                url = f"https://raw.githubusercontent.com/{REPOSITORY}/{self.commit}/{quote(item['path'], safe='/')}"
                data = self._get(url, MAX_FILE_BYTES)
                blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
                if len(data) != size or blob != item.get("sha"):
                    raise AddonError(f"GitHub content does not match the selected tree: {relative}")
                files[relative] = data
            if not files:
                raise AddonError(f"{BUNDLE_PATHS[group]} is absent at {self.ref}")
            bundle = Bundle(group, self.commit, files)
            self._cache[group] = bundle
            return bundle
        except (KeyError, TypeError, ValueError) as error:
            self._cache[group] = str(error)
            raise AddonError(str(error)) from error
