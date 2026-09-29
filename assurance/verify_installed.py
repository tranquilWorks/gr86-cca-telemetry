#!/usr/bin/env python3
"""Exercise the pinned GR86 CLI and actual MCP; never approve engineering gates."""
from pathlib import Path
from installed_smoke import main
HERE = Path(__file__).resolve().parent
if __name__ == '__main__':
    raise SystemExit(main(HERE.parent, HERE / 'bridge.py', 'gr86-revb-jlcpcb'))
