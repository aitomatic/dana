class RuntimeScopes:
    LOCAL = ["local"]
    LOCAL_WITH_DOT = [f"{scope}." for scope in LOCAL]
    GLOBAL = ["private", "public", "system"]
    GLOBAL_WITH_DOT = [f"{scope}." for scope in GLOBAL]
    ALL = LOCAL + GLOBAL
    ALL_WITH_DOT = LOCAL_WITH_DOT + GLOBAL_WITH_DOT
