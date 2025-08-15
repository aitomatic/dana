"""
Dana Libraries

Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Core library functions for the Dana language.

"""

__IS_WIRED_IN = True

if not __IS_WIRED_IN:
    #
    # Make sure this module path is in DANAPATH
    #
    import os
    from pathlib import Path

    def _ensure_libs_in_danapath():
        """Ensure libs are in DANAPATH for on-demand loading."""
        libs_path = str(Path(__file__).parent.resolve())
        danapath = os.environ.get("DANAPATH", "")
        paths = [p for p in danapath.split(os.pathsep) if p]
        if libs_path not in paths:
            paths.append(libs_path)
            os.environ["DANAPATH"] = os.pathsep.join(paths)
        print(f"DANAPATH: {os.environ['DANAPATH']}")

    _ensure_libs_in_danapath()

#
# Import the core and stdlib libraries
#
import dana.libs.corelib as __python_corelib  # noqa: F401
import dana.libs.stdlib as __python_stdlib  # noqa: F401

__all__ = []
