"""Translate discovered candidates into stable application identities."""
from ..application_discovery import ApplicationCandidate, WindowsApplicationResolver
from .models import ApplicationIdentity

class ApplicationIdentityService:
    def __init__(self, resolver: WindowsApplicationResolver | None = None):
        self.resolver=resolver or WindowsApplicationResolver()
    def resolve(self, query: str) -> ApplicationIdentity | None:
        candidate=self.resolver.resolve(query)
        return self.from_candidate(candidate) if candidate else None
    @staticmethod
    def from_candidate(candidate: ApplicationCandidate) -> ApplicationIdentity:
        process_names=(candidate.process_name,) if candidate.process_name else ()
        adapter="generic.windows"
        name=candidate.display_name.casefold()
        if "epic games" in name or "epicgameslauncher.exe" in " ".join(process_names).casefold(): adapter="epic.games.launcher"
        elif name in {"microsoft word","microsoft excel","microsoft powerpoint"}: adapter="microsoft.office"
        return ApplicationIdentity(candidate.application_id,candidate.display_name,candidate.launch_target,candidate.source,process_names,candidate.launch_target if candidate.launch_target.lower().endswith(".exe") else None,candidate.launch_target if candidate.source=="aumid" else None,adapter,(candidate.display_name,))
