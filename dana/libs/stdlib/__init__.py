"""
Dana Standard Library

Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Standard library functions for the Dana language.

This package provides implementations of core Dana functions including:
- Core functions (log, reason, str, etc.)
- Agent functions
- POET functions
- KNOWS functions
- Math functions (sum_range, is_odd, is_even, factorial)
- Math and utility functions
"""

#
# Just make sure this module path is in DANA_PATH
#
import os
from pathlib import Path


def _ensure_stdlib_in_danapath():
    """Ensure stdlib is in DANA_PATH for on-demand loading."""
    stdlib_path = str(Path(__file__).parent.resolve())
    danapath = os.environ.get("DANA_PATH", "")
    paths = [p for p in danapath.split(os.pathsep) if p]
    if stdlib_path not in paths:
        paths.append(stdlib_path)
        os.environ["DANA_PATH"] = os.pathsep.join(paths)


_ensure_stdlib_in_danapath()
