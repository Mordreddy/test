import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == "win32":
    base = "Console"

executables = [
    Executable(
        script="stage9.py",
        base=base,
        target_name="my_wget.exe"
    )
]

setup(
    name="MyWgetTool",
    version="1.0",
    description="Advanced Wget Tool (Threaded Progress + Resumable Download)",
    executables=executables,
    options={
        "build_exe": {
            "packages": ["requests", "threading", "time", "argparse", "os", "ssl", "urllib.parse"],
            "excludes": ["tensorflow", "numpy"],
            "optimize": 2,
            "include_files": [],
        }
    }
)