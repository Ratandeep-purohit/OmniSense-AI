"""Epic Games Launcher adapter for launcher-specific window identity."""
from .base import ApplicationAdapter
class EpicGamesLauncherAdapter:
    adapter_id="epic.games.launcher"
    def supports(self,identity): return identity.adapter_id==self.adapter_id
    def semantic_aliases(self,text): return (text.strip(), "Epic Games Launcher", "Library", "Store")
    def preferred_window_tokens(self,identity): return ("Epic Games Launcher","Epic Games")
