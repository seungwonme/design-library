#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0"]
# ///
import runpy
import sys
from pathlib import Path
sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[1]
runner = root / ".agents/skills/design-library-gallery/scripts/design-library.py"
if not runner.is_file():
    runner = root / ".design-library/scripts/design-library.py"
sys.path.insert(0, str(runner.parent))
sys.argv = [str(runner), "--workspace", str(root), *sys.argv[1:]]
runpy.run_path(str(runner), run_name="__main__")
