$ErrorActionPreference="Stop"
$env:OMNISENSE_E2E="1"
python -m pytest tests/e2e -q
if($LASTEXITCODE -ne 0){throw "Windows production smoke tests failed."}
Write-Host "Windows production smoke suite passed."
