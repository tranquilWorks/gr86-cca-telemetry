#!/usr/bin/env python3
"""Normalize generated I27 publication state before committing it.

The I26 verifier intentionally rewrites a historical-reference binding in its
working tree. Older revisions of that rewrite were not idempotent because the
literal ``PCB_HASH=`` token also occurs inside ``REFERENCE_PCB_HASH=``. Native
analysis also imports tracked legacy bytecode files. Neither effect is release
evidence, so publication normalizes the binding and restores tracked bytecode
before staging.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
W = ROOT / 'docs/engineering/rvb22'
RUN_REVIEW = W / 'analyses/convergence_01/run_review.py'
CURRENT = 'a04f42b358fa65a332128115a7b648e1a2297531ecb47466ac24697de536a936'
HISTORICAL = '5b373f6033fdbd18f126f8ca054b619abada2568778c5a8fc303c4e756fb06c8'

text = RUN_REVIEW.read_text()
# Collapse every generated/reference binding immediately following PCB_HASH into
# one unambiguous historical reference. Parentheses deliberately prevent the
# legacy substring replacement from matching this assignment on later runs.
text = re.sub(
    r"(?m)^PCB_HASH='[^']+'\n(?:REFERENCE_PCB_HASH='[^']+'\n|REFERENCE_PCB_HASH=\('[^']+'\)\n)*",
    f"PCB_HASH='{CURRENT}'\nREFERENCE_PCB_HASH=('{HISTORICAL}')\n",
    text,
    count=1,
)
if f"PCB_HASH='{CURRENT}'" not in text or f"REFERENCE_PCB_HASH=('{HISTORICAL}')" not in text:
    raise SystemExit('Unable to normalize run_review PCB bindings')
RUN_REVIEW.write_text(text)

tracked = subprocess.check_output(['git','ls-files','*.pyc'], cwd=ROOT, text=True).splitlines()
if tracked:
    subprocess.run(['git','restore','--worktree','--',*tracked], cwd=ROOT, check=True)

print(f'normalized {RUN_REVIEW.relative_to(ROOT)}; restored {len(tracked)} tracked bytecode files')
