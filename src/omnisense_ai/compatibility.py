"""Windows compatibility matrix and runtime capability checks."""
from dataclasses import dataclass
import platform,sys
@dataclass(frozen=True,slots=True)
class CompatibilityReport:
    supported:bool; os_version:str; python_version:str; architecture:str; checks:tuple[str,...]
def check_windows_compatibility()->CompatibilityReport:
    os_version=platform.platform(); py=platform.python_version(); arch=platform.machine(); checks=[]
    if platform.system()!="Windows": return CompatibilityReport(False,os_version,py,arch,("Windows 11 is required for the production desktop target.",))
    checks.append("windows")
    checks.append("python>=3.11") if sys.version_info>=(3,11) else checks.append("python version unsupported")
    checks.append("x64") if arch.lower() in {"amd64","x86_64","arm64"} else checks.append("unsupported architecture")
    return CompatibilityReport(all("unsupported" not in c and "required" not in c for c in checks),os_version,py,arch,tuple(checks))
