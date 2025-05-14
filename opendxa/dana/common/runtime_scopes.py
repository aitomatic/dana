"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
"""


class RuntimeScopes:
    LOCAL = ["local"]
    LOCAL_WITH_DOT = [f"{scope}." for scope in LOCAL]
    GLOBAL = ["private", "public", "system"]
    GLOBAL_WITH_DOT = [f"{scope}." for scope in GLOBAL]
    ALL = LOCAL + GLOBAL
    ALL_WITH_DOT = LOCAL_WITH_DOT + GLOBAL_WITH_DOT
