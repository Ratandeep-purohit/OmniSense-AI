$ErrorActionPreference="Stop"
python -m pip install --upgrade pip
python -m pip install -e ".[ui,ocr,automation,windows]"
python -m pytest
python -m pip install pyinstaller
pyinstaller packaging/omnisense.spec --clean --noconfirm
Write-Host "Build complete. Compile packaging/installer.iss with Inno Setup on Windows."
