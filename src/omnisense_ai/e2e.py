"""Real Windows E2E harness. Disabled unless explicitly opted in."""
from dataclasses import dataclass
import os,platform,time
from .application_discovery import WindowsApplicationResolver
@dataclass(frozen=True,slots=True)
class SmokeTarget:
    query:str; expected_processes:tuple[str,...]=(); required:bool=True
DEFAULT_SMOKE_TARGETS = (
    SmokeTarget("notepad", ("notepad.exe",)),
    SmokeTarget("calculator", ("calculatorapp.exe", "applicationframehost.exe")),
    SmokeTarget("microsoft word", ("winword.exe",)),
    SmokeTarget("microsoft excel", ("excel.exe",)),
    SmokeTarget("microsoft powerpoint", ("powerpnt.exe",)),
    SmokeTarget("chrome", ("chrome.exe",)),
    SmokeTarget("edge", ("msedge.exe",)),
    SmokeTarget("visual studio code", ("code.exe",)),
    SmokeTarget("steam", ("steam.exe",)),
    SmokeTarget("epic games launcher", ("epicgameslauncher.exe",)),
    SmokeTarget("file explorer", ("explorer.exe",)),
)

class WindowsE2EHarness:
    def __init__(self,resolver=None): self.resolver=resolver or WindowsApplicationResolver()
    def require_enabled(self):
        if platform.system()!="Windows": raise RuntimeError("Windows E2E requires a Windows runner.")
        if os.environ.get("OMNISENSE_E2E","").casefold()!="1": raise RuntimeError("Set OMNISENSE_E2E=1 to enable real desktop E2E tests.")
    def discover_matrix(self,targets=DEFAULT_SMOKE_TARGETS):
        self.require_enabled(); return tuple((t,self.resolver.resolve(t.query)) for t in targets)
    def wait_for_process(self,process_names,timeout=10):
        self.require_enabled(); deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            for p in process_names:
                if self._process_exists(p): return p
            time.sleep(.25)
        return None
    @staticmethod
    def _process_exists(name):
        import subprocess
        try:
            out=subprocess.check_output(["tasklist","/FI",f"IMAGENAME eq {name}"],text=True,creationflags=0x08000000)
            return name.casefold() in out.casefold()
        except Exception:return False
