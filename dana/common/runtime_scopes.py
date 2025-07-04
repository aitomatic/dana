"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
"""


class RuntimeScopes:
    LOCAL = ["local"]
    LOCAL_WITH_DOT = [f"{scope}." for scope in LOCAL]
    LOCAL_WITH_COLON = [f"{scope}:" for scope in LOCAL]
    GLOBAL = ["private", "public", "system"]
    GLOBAL_WITH_DOT = [f"{scope}." for scope in GLOBAL]
    GLOBAL_WITH_COLON = [f"{scope}:" for scope in GLOBAL]
    ALL = LOCAL + GLOBAL
    ALL_WITH_DOT = LOCAL_WITH_DOT + GLOBAL_WITH_DOT
    ALL_WITH_COLON = LOCAL_WITH_COLON + GLOBAL_WITH_COLON
    ALL_WITH_SEPARATOR = ALL_WITH_DOT + ALL_WITH_COLON
    SENSITIVE = ["private", "system"]
    NOT_SENSITIVE = [scope for scope in ALL if scope not in ["private", "system"]]