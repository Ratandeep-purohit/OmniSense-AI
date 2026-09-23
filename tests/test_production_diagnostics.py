from omnisense_ai.production_diagnostics import collect_diagnostics
def test_diagnostics_is_real_capability_based():
    report=collect_diagnostics(); assert report.compatibility.os_version; assert isinstance(report.native_uia_available,bool)
