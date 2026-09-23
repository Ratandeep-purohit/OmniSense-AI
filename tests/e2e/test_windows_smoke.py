import os,platform,pytest
from omnisense_ai.e2e import WindowsE2EHarness,DEFAULT_SMOKE_TARGETS
pytestmark=pytest.mark.skipif(platform.system()!="Windows" or os.environ.get("OMNISENSE_E2E")!="1",reason="Real Windows E2E requires OMNISENSE_E2E=1 on Windows.")
def test_discovery_matrix():
    results=WindowsE2EHarness().discover_matrix()
    assert len(results)==len(DEFAULT_SMOKE_TARGETS)
    assert all(target.required for target,_ in results)
