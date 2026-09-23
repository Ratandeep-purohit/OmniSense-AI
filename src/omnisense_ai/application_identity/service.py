"""Translate discovered candidates into canonical identities."""
from ..application_discovery import ApplicationCandidate,WindowsApplicationResolver
from .models import ApplicationIdentity
class ApplicationIdentityService:
    def __init__(self,resolver=None): self.resolver=resolver or WindowsApplicationResolver()
    def resolve(self,query):
        c=self.resolver.resolve(query); return self.from_candidate(c) if c else None
    @staticmethod
    def from_candidate(c:ApplicationCandidate):
        processes=(c.process_name,) if c.process_name else (); name=c.display_name.casefold(); adapter="generic.windows"
        if "epic games" in name or "epicgameslauncher.exe" in " ".join(processes).casefold(): adapter="epic.games.launcher"
        elif name in {"microsoft word","microsoft excel","microsoft powerpoint"}: adapter="microsoft.office"
        return ApplicationIdentity(c.application_id,c.display_name,c.launch_target,c.source,processes,c.launch_target if c.launch_target.lower().endswith(".exe") else None,c.launch_target if c.source=="aumid" else None,adapter,(c.display_name,))
