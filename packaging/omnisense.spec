from PyInstaller.utils.hooks import collect_submodules
hiddenimports=collect_submodules("omnisense_ai")
block_cipher=None
analysis=Analysis(["src/omnisense_ai/ui/main.py"],pathex=["src"],hiddenimports=hiddenimports,datas=[],binaries=[],excludes=[])
pyz=PYZ(analysis.pure,analysis.zipped_data,cipher=block_cipher)
exe=EXE(pyz,analysis.scripts,analysis.binaries,analysis.datas,[],name="OmniSenseAI",console=False)
