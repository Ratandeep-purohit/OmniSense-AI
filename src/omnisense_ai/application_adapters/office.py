"""Microsoft Office semantic hints; no hard-coded launch authority."""
from .base import ApplicationAdapter
class MicrosoftOfficeAdapter:
    adapter_id="microsoft.office"
    _apps={"microsoft word","microsoft excel","microsoft powerpoint"}
    def supports(self,identity): return identity.display_name.casefold() in self._apps
    def semantic_aliases(self,text): return (text.strip(), "File", "Home")
    def preferred_window_tokens(self,identity): return (identity.display_name, identity.display_name.removeprefix("Microsoft "))
