"""Canonical application identity model used across discovery, adapters and verification."""
from dataclasses import dataclass
from enum import StrEnum

class IdentitySource(StrEnum):
    START_MENU="start_menu"; APP_PATHS="app_paths"; AUMID="aumid"; RUNTIME="runtime"

@dataclass(frozen=True, slots=True)
class ApplicationIdentity:
    application_id: str
    display_name: str
    launch_target: str
    source: IdentitySource | str
    process_names: tuple[str, ...] = ()
    executable_path: str | None = None
    aumid: str | None = None
    adapter_id: str = "generic.windows"
    aliases: tuple[str, ...] = ()
    def __post_init__(self):
        for value, name in ((self.application_id,"application_id"),(self.display_name,"display_name"),(self.launch_target,"launch_target")):
            if not value.strip(): raise ValueError(f"{name} is required.")
        if len(self.process_names)>32 or len(self.aliases)>64: raise ValueError("Application identity contains too many aliases.")

    def matches_process(self, process_name: str | None) -> bool:
        if not process_name: return False
        return process_name.casefold() in {p.casefold() for p in self.process_names}
