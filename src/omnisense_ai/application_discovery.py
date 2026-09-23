"""Windows application discovery and trust boundary for OmniSense.

The resolver discovers launchable applications from Windows-owned application
entry points instead of maintaining a developer-authored per-app allowlist.
It intentionally returns only Start Menu shortcuts and registered App Paths.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ApplicationCandidate:
    """A Windows application entry point discovered from trusted OS locations."""

    application_id: str
    display_name: str
    launch_target: str
    source: str
    process_name: str | None = None

    def __post_init__(self) -> None:
        if not self.application_id.strip() or not self.display_name.strip():
            raise ValueError("Application identity is required.")
        if not self.launch_target.strip():
            raise ValueError("Application launch target is required.")


class WindowsApplicationResolver:
    """Discover installed applications without a static application allowlist.

    Sources:
    * per-user and all-user Start Menu .lnk entries
    * HKCU/HKLM App Paths registrations

    A caller can only launch a target returned by this resolver. The backend
    revalidates the target before execution, so a user cannot replace the
    discovered target with an arbitrary executable path.
    """

    _APP_PATHS = (
        r"Software\Microsoft\Windows\CurrentVersion\App Paths",
        r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths",
    )

    def discover(self) -> tuple[ApplicationCandidate, ...]:
        if os.name != "nt":
            return ()
        candidates = list(self._start_menu_candidates())
        candidates.extend(self._app_path_candidates())
        candidates.extend(self._aumid_candidates())
        return self._deduplicate(candidates)

    def resolve(self, query: str) -> ApplicationCandidate | None:
        normalized = self._normalize(query)
        if not normalized:
            return None

        scored: list[tuple[int, ApplicationCandidate]] = []
        for candidate in self.discover():
            score = self._score(normalized, candidate.display_name)
            if candidate.process_name:
                score = max(score, self._score(normalized, Path(candidate.process_name).stem))
            if score:
                scored.append((score, candidate))

        scored.sort(
            key=lambda item: (
                -item[0],
                -int(bool(item[1].process_name)),
                item[1].display_name.casefold(),
                item[1].source,
                item[1].launch_target.casefold(),
            )
        )
        if not scored or scored[0][0] < 70:
            return None

        # Multiple Windows entries can represent the same logical application
        # (for example duplicate Start Menu shortcuts). Do not treat those as
        # ambiguity when their normalized display name is identical.
        top_score, top = scored[0]
        top_name = self._normalize(top.display_name)
        distinct = [
            item for item in scored[1:]
            if item[0] == top_score and self._normalize(item[1].display_name) != top_name
        ]
        if distinct:
            return None
        return top

    def is_trusted_target(self, target: str) -> bool:
        """Revalidate a launch target against current Windows discovery."""

        if os.name != "nt" or not target:
            return False
        if target.casefold().startswith("shell:appsfolder\\"):
            return any(
                target.casefold() == candidate.launch_target.casefold()
                for candidate in self.discover()
                if candidate.source == "aumid"
            )

        try:
            requested = Path(target).resolve(strict=True)
        except (OSError, RuntimeError):
            return False

        requested_text = str(requested).casefold()
        for candidate in self.discover():
            try:
                discovered = Path(candidate.launch_target).resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if requested_text == str(discovered).casefold():
                return True
        return False

    def _start_menu_candidates(self) -> Iterable[ApplicationCandidate]:
        roots = (
            Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
            Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        )
        for root in roots:
            if not root.is_dir():
                continue
            try:
                shortcuts = root.rglob("*.lnk")
            except OSError:
                continue
            for shortcut in shortcuts:
                try:
                    if not shortcut.is_file():
                        continue
                except OSError:
                    continue
                display = shortcut.stem.strip()
                if not display:
                    continue
                yield ApplicationCandidate(
                    application_id=f"startmenu:{str(shortcut.resolve()).casefold()}",
                    display_name=display,
                    launch_target=str(shortcut.resolve()),
                    source="start_menu",
                    process_name=None,
                )

    def _app_path_candidates(self) -> Iterable[ApplicationCandidate]:
        import winreg

        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for base in self._APP_PATHS:
                try:
                    with winreg.OpenKey(hive, base) as root:
                        count = winreg.QueryInfoKey(root)[0]
                        names = [
                            winreg.EnumKey(root, index)
                            for index in range(count)
                        ]
                except OSError:
                    continue

                for name in names:
                    if not name.casefold().endswith(".exe"):
                        continue
                    try:
                        with winreg.OpenKey(root, name) as key:
                            target, _ = winreg.QueryValueEx(key, None)
                    except OSError:
                        continue
                    if not isinstance(target, str):
                        continue
                    target = os.path.expandvars(target).strip().strip('"')
                    if not target.lower().endswith(".exe"):
                        continue
                    path = Path(target)
                    if not path.is_file():
                        continue
                    display = self._friendly_name(name)
                    yield ApplicationCandidate(
                        application_id=f"app-paths:{name.casefold()}:{str(path).casefold()}",
                        display_name=display,
                        launch_target=str(path.resolve()),
                        source="app_paths",
                        process_name=name,
                    )

    def _aumid_candidates(self) -> Iterable[ApplicationCandidate]:
        """Discover packaged apps from Windows AUMID registry entries.

        Microsoft documents AUMIDs as the identity used by Windows to launch
        packaged applications. The registry path below is read-only; no
        package state is modified.
        """
        import winreg

        base = r"Software\Classes\ActivatableClasses\Package"
        try:
            root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, base)
        except OSError:
            return

        stack: list[tuple[object, int]] = [(root, 0)]
        seen: set[str] = set()
        try:
            while stack:
                key, depth = stack.pop()
                if depth > 8:
                    try:
                        key.Close()
                    except OSError:
                        pass
                    continue
                try:
                    value_count = winreg.QueryInfoKey(key)[1]
                    for index in range(value_count):
                        try:
                            value_name, value, _ = winreg.EnumValue(key, index)
                        except OSError:
                            continue
                        if value_name.casefold() != "appusermodelid" or not isinstance(value, str):
                            continue
                        aumid = value.strip()
                        if "!" not in aumid or aumid.casefold() in seen:
                            continue
                        seen.add(aumid.casefold())
                        family = aumid.split("!", 1)[0]
                        display = family.rsplit("_", 1)[0].replace(".", " ").replace("_", " ").strip()
                        if not display:
                            display = family
                        yield ApplicationCandidate(
                            application_id=f"aumid:{aumid.casefold()}",
                            display_name=display,
                            launch_target=f"shell:AppsFolder\\{aumid}",
                            source="aumid",
                            process_name=None,
                        )

                    subkey_count = winreg.QueryInfoKey(key)[0]
                    for index in range(subkey_count):
                        try:
                            child = winreg.OpenKey(key, winreg.EnumKey(key, index))
                        except OSError:
                            continue
                        stack.append((child, depth + 1))
                finally:
                    try:
                        key.Close()
                    except OSError:
                        pass
        except OSError:
            return

    @staticmethod
    def _friendly_name(executable: str) -> str:
        return Path(executable).stem.replace("_", " ").replace("-", " ").strip()

    @classmethod
    def _score(cls, query: str, name: str) -> int:
        candidate = cls._normalize(name)
        if not candidate:
            return 0
        if query == candidate:
            return 100
        if query in candidate:
            return 90
        query_tokens = set(query.split())
        candidate_tokens = set(candidate.split())
        if query_tokens and query_tokens.issubset(candidate_tokens):
            return 85
        if len(query_tokens) == 1 and query_tokens & candidate_tokens:
            return 72
        return 0

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.casefold())).strip()

    @staticmethod
    def _deduplicate(
        candidates: list[ApplicationCandidate],
    ) -> tuple[ApplicationCandidate, ...]:
        seen: set[tuple[str, str]] = set()
        result: list[ApplicationCandidate] = []
        for candidate in candidates:
            key = (candidate.display_name.casefold(), candidate.launch_target.casefold())
            if key in seen:
                continue
            seen.add(key)
            result.append(candidate)
        return tuple(result)
