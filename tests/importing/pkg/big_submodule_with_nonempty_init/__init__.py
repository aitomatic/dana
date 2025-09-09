import sys

from . import small_submodule
from .small_submodule import (
    I_AM_PY as SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT,

    util_submodule as util_submodule_imported_in_small_submodule_in_big_submodule_with_nonempty_init,
    small_util_submodule_in_big_util_submodule as small_util_submodule_in_big_util_submodule_imported_in_small_submodule_in_big_submodule_with_nonempty_init,
    SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE as SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE_IMPORTED_IN_SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT,
)

from .. import util_submodule
from ..util_submodule import small_submodule as small_util_submodule_in_big_util_submodule
from ..util_submodule.small_submodule import I_AM_PY as SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE


I_AM_PY = sys.modules[__name__].__name__


print(f"""
IMPORTED: {small_submodule}
INTO: {I_AM_PY}
""")

print(f"""
ACCESSED: {small_submodule.I_AM_PY}
IN: {I_AM_PY}
""")
print(f"""
IMPORTED: {SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT}
INTO: {I_AM_PY}
""")

print(f"""
ACCESSED: {small_submodule.util_submodule}
IN: {I_AM_PY}
""")
print(f"""
IMPORTED: {util_submodule_imported_in_small_submodule_in_big_submodule_with_nonempty_init}
INTO: {I_AM_PY}
""")
print(f"""
IMPORTED: {util_submodule}
INTO: {I_AM_PY}
""")

print(f"""
ACCESSED: {small_submodule.util_submodule.small_submodule}
IN: {I_AM_PY}
""")
print(f"""
ACCESSED: {small_submodule.small_util_submodule_in_big_util_submodule}
IN: {I_AM_PY}
""")
print(f"""
IMPORTED: {small_util_submodule_in_big_util_submodule_imported_in_small_submodule_in_big_submodule_with_nonempty_init}
INTO: {I_AM_PY}
""")
print(f"""
ACCESSED: {util_submodule.small_submodule}
IN: {I_AM_PY}
""")
print(f"""
IMPORTED: {small_util_submodule_in_big_util_submodule}
INTO: {I_AM_PY}
""")

print(f"""
ACCESSED: {small_submodule.util_submodule.small_submodule.I_AM_PY}
IN: {I_AM_PY}
""")
print(f"""
ACCESSED: {small_submodule.small_util_submodule_in_big_util_submodule.I_AM_PY}
IN: {I_AM_PY}
""")
print(f"""
ACCESSED: {small_submodule.SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
IN: {I_AM_PY}
""")
print(f"""
IMPORTED: {SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE_IMPORTED_IN_SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT}
INTO: {I_AM_PY}
""")
print(f"""
ACCESSED: {util_submodule.small_submodule.I_AM_PY}
IN: {I_AM_PY}
""")
print(f"""
ACCESSED: {small_util_submodule_in_big_util_submodule.I_AM_PY}
IN: {I_AM_PY}
""")
print(f"""
IMPORTED: {SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
INTO: {I_AM_PY}
""")
