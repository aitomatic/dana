"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
"""


class RuntimeScopes:
    LOCAL = "local"
    SYSTEM = "system"
    PRIVATE = "private"
    PUBLIC = "public"

    LOCALS = [LOCAL]
    SYSTEMS = [SYSTEM]
    PRIVATES = [PRIVATE]
    PUBLICS = [PUBLIC]

    LOCALS_WITH_DOT = [f"{scope}." for scope in LOCALS]
    LOCALS_WITH_COLON = [f"{scope}:" for scope in LOCALS]

    GLOBALS = [PRIVATE, PUBLIC, SYSTEM]
    GLOBALS_WITH_DOT = [f"{scope}." for scope in GLOBALS]
    GLOBALS_WITH_COLON = [f"{scope}:" for scope in GLOBALS]

    ALL = LOCALS + GLOBALS
    ALL_WITH_DOT = LOCALS_WITH_DOT + GLOBALS_WITH_DOT
    ALL_WITH_COLON = LOCALS_WITH_COLON + GLOBALS_WITH_COLON
    ALL_WITH_SEPARATOR = ALL_WITH_DOT + ALL_WITH_COLON

    SENSITIVE = [PRIVATE, SYSTEM]
    NOT_SENSITIVE = [LOCAL, PUBLIC]
