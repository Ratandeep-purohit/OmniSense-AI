"""Product diagnostics composed from real runtime capabilities only."""
from dataclasses import dataclass
from .compatibility import check_windows_compatibility
from .capabilities import CapabilityManager
@dataclass(frozen=True,slots=True)
class DiagnosticsReport:
    compatibility:object; automation_capability:bool; native_uia_available:bool; checks:tuple[str,...]
def collect_diagnostics(capabilities:CapabilityManager|None=None)->DiagnosticsReport:
    from .ui_automation import NativeUIAutomationService
    compatibility=check_windows_compatibility(); uia=NativeUIAutomationService().available
    checks=list(compatibility.checks)
    checks.append("native_uia" if uia else "native_uia_unavailable")
    checks.append("desktop_execute_granted" if capabilities and capabilities.has("desktop.execute") else "desktop_execute_not_granted")
    return DiagnosticsReport(compatibility,bool(capabilities and capabilities.has("desktop.execute")),uia,tuple(checks))
