import sys

from . import big_namespace_submodule
from .big_namespace_submodule import small_submodule as small_submodule_in_big_namespace_submodule
from .big_namespace_submodule.small_submodule import (
    I_AM as SMALL_SUBMODULE_IN_BIG_NAMESPACE_SUBMODULE,

    util_submodule as util_submodule_imported_in_small_submodule_in_big_namespace_submodule,
    small_util_submodule_in_big_util_submodule as small_util_submodule_in_big_util_submodule_imported_in_small_submodule_in_big_namespace_submodule,
    SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE as SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE_IMPORTED_IN_SMALL_SUBMODULE_IN_BIG_NAMESPACE_SUBMODULE,
)

from . import big_submodule_with_empty_init
from .big_submodule_with_empty_init import small_submodule as small_submodule_in_big_submodule_with_empty_init
from .big_submodule_with_empty_init.small_submodule import (
    I_AM as SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_EMPTY_INIT,

    util_submodule as util_submodule_imported_in_small_submodule_in_big_submodule_with_empty_init,
    small_util_submodule_in_big_util_submodule as small_util_submodule_in_big_util_submodule_imported_in_small_submodule_in_big_submodule_with_empty_init,
    SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE as SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE_IMPORTED_IN_SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_EMPTY_INIT,
)

from . import big_submodule_with_nonempty_init
from .big_submodule_with_nonempty_init import I_AM as BIG_SUBMODULE_WITH_NONEMPTY_INIT

from .big_submodule_with_nonempty_init import small_submodule as small_submodule_in_big_submodule_with_nonempty_init
from .big_submodule_with_nonempty_init.small_submodule import (
    I_AM as SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT,

    util_submodule as util_submodule_imported_in_small_submodule_in_big_submodule_with_nonempty_init,
    small_util_submodule_in_big_util_submodule as small_util_submodule_in_big_util_submodule_imported_in_small_submodule_in_big_submodule_with_nonempty_init,
    SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE as SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE_IMPORTED_IN_SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT,
)
from .big_submodule_with_nonempty_init import (
    util_submodule as util_submodule_imported_in_big_submodule_with_nonempty_init,
    small_util_submodule_in_big_util_submodule as small_util_submodule_in_big_util_submodule_imported_in_big_submodule_with_nonempty_init,
    SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE as SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE_IMPORTED_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT,
)

from . import util_submodule
from .util_submodule import small_submodule as small_util_submodule_in_util_submodule
from .util_submodule.small_submodule import I_AM as SMALL_UTIL_SUBMODULE_IN_UTIL_SUBMODULE


I_AM = sys.modules[__name__].__name__


# pkg.big_namespace_submodule
print(f"""
IMPORTED: {big_namespace_submodule}
INTO: {I_AM}
""")

# pkg.big_namespace_submodule.small_submodule
print(f"""
ACCESSED: {big_namespace_submodule.small_submodule}
IN: {I_AM}
""")
print(f"""
IMPORTED: {small_submodule_in_big_namespace_submodule}
INTO: {I_AM}
""")

print(f"""
ACCESSED: {big_namespace_submodule.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_namespace_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
IMPORTED: {SMALL_SUBMODULE_IN_BIG_NAMESPACE_SUBMODULE}
INTO: {I_AM}
""")


# pkg.big_submodule_with_empty_init
print(f"""
IMPORTED: {big_submodule_with_empty_init}
INTO: {I_AM}
""")

# pkg.big_submodule_with_empty_init.small_submodule
print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule}
IN: {I_AM}
""")
print(f"""
IMPORTED: {small_submodule_in_big_submodule_with_empty_init}
INTO: {I_AM}
""")

print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.I_AM}
IN: {I_AM}
""")
print(f"""
IMPORTED: {SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_EMPTY_INIT}
INTO: {I_AM}
""")


# pkg.big_submodule_with_nonempty_init
print(f"""
IMPORTED: {big_submodule_with_nonempty_init}
INTO: {I_AM}
""")

print(f"""
ACCESSED: {big_submodule_with_nonempty_init.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {BIG_SUBMODULE_WITH_NONEMPTY_INIT}
IN: {I_AM}
""")

# pkg.big_submodule_with_nonempty_init.small_submodule
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.small_submodule}
IN: {I_AM}
""")
print(f"""
IMPORTED: {small_submodule_in_big_submodule_with_nonempty_init}
INTO: {I_AM}
""")

print(f"""
ACCESSED: {big_submodule_with_nonempty_init.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_nonempty_init.I_AM}
IN: {I_AM}
""")
print(f"""
IMPORTED: {SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT}
INTO: {I_AM}
""")


# pkg.util_submodule
print(f"""
IMPORTED: {util_submodule}
INTO: {I_AM}
""")

# pkg.util_submodule through pkg.big_namespace_submodule.small_submodule
print(f"""
ACCESSED: {big_namespace_submodule.small_submodule.util_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_namespace_submodule.util_submodule}
IN: {I_AM}
""")
print(f"""
IMPORTED: {util_submodule_imported_in_small_submodule_in_big_namespace_submodule}
INTO: {I_AM}
""")

# pkg.util_submodule through pkg.big_submodule_with_empty_init.small_submodule
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.util_submodule}
IN: {I_AM}
""")
print(f"""
IMPORTED: {util_submodule_imported_in_small_submodule_in_big_submodule_with_empty_init}
IN: {I_AM}
""")

# pkg.util_submodule through pkg.big_submodule_with_nonempty_init.small_submodule
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_nonempty_init.util_submodule}
IN: {I_AM}
""")
print(f"""
IMPORTED: {util_submodule_imported_in_small_submodule_in_big_submodule_with_nonempty_init}
INTO: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.small_submodule.util_submodule}
IN: {I_AM}
""")

# pkg.util_submodule through pkg.big_submodule_with_nonempty_init
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.util_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {util_submodule_imported_in_big_submodule_with_nonempty_init}
IN: {I_AM}
""")


# pkg.util_submodule.small_submodule
print(f"""
ACCESSED: {util_submodule.small_submodule}
IN: {I_AM}
""")
print(f"""
IMPORTED: {small_util_submodule_in_util_submodule}
INTO: {I_AM}
""")

# pkg.util_submodule.small_submodule through pkg.big_namespace_submodule.small_submodule
print(f"""
ACCESSED: {big_namespace_submodule.small_submodule.util_submodule.small_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_namespace_submodule.small_submodule.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_namespace_submodule.util_submodule.small_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_namespace_submodule.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {util_submodule_imported_in_small_submodule_in_big_namespace_submodule.small_submodule}
IN: {I_AM}
""")
print(f"""
IMPORTED: {small_util_submodule_in_big_util_submodule_imported_in_small_submodule_in_big_namespace_submodule}
INTO: {I_AM}
""")

# pkg.util_submodule.small_submodule through pkg.big_submodule_with_empty_init.small_submodule
print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule.util_submodule.small_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.util_submodule.small_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {util_submodule_imported_in_small_submodule_in_big_submodule_with_empty_init.small_submodule}
IN: {I_AM}
""")
print(f"""
IMPORTED: {small_util_submodule_in_big_util_submodule_imported_in_small_submodule_in_big_submodule_with_empty_init}
INTO: {I_AM}
""")

# pkg.util_submodule.small_submodule through pkg.big_submodule_with_nonempty_init.small_submodule
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_nonempty_init.util_submodule.small_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_nonempty_init.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {util_submodule_imported_in_small_submodule_in_big_submodule_with_nonempty_init.small_submodule}
IN: {I_AM}
""")
print(f"""
IMPORTED: {small_util_submodule_in_big_util_submodule_imported_in_small_submodule_in_big_submodule_with_nonempty_init}
INTO: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.small_submodule.util_submodule.small_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.small_submodule.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
""")

# pkg.util_submodule.small_submodule through pkg.big_submodule_with_nonempty_init
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.util_submodule.small_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
""")
print(f"""
ACCESSED: {util_submodule_imported_in_big_submodule_with_nonempty_init.small_submodule}
IN: {I_AM}
""")
print(f"""
IMPORTED: {small_util_submodule_in_big_util_submodule_imported_in_big_submodule_with_nonempty_init}
INTO: {I_AM}
""")


# pkg.util_submodule.small_submodule.I_AM
print(f"""
ACCESSED: {util_submodule.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_util_submodule_in_util_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
IMPORTED: {SMALL_UTIL_SUBMODULE_IN_UTIL_SUBMODULE}
INTO: {I_AM}
""")

# pkg.util_submodule.small_submodule.I_AM through pkg.big_namespace_submodule.small_submodule
print(f"""
ACCESSED: {big_namespace_submodule.small_submodule.util_submodule.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_namespace_submodule.small_submodule.small_util_submodule_in_big_util_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_namespace_submodule.small_submodule.SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_namespace_submodule.util_submodule.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_namespace_submodule.small_util_submodule_in_big_util_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_namespace_submodule.SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
IN: {I_AM}
""")
print(f"""
ACCESSED: {util_submodule_imported_in_small_submodule_in_big_namespace_submodule.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_util_submodule_in_big_util_submodule_imported_in_small_submodule_in_big_namespace_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
IMPORTED: {SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE_IMPORTED_IN_SMALL_SUBMODULE_IN_BIG_NAMESPACE_SUBMODULE}
INTO: {I_AM}
""")

# pkg.util_submodule.small_submodule.I_AM through pkg.big_submodule_with_empty_init.small_submodule
print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule.util_submodule.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule.small_util_submodule_in_big_util_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule.SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.util_submodule.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.small_util_submodule_in_big_util_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
IN: {I_AM}
""")
print(f"""
ACCESSED: {util_submodule_imported_in_small_submodule_in_big_submodule_with_empty_init.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_util_submodule_in_big_util_submodule_imported_in_small_submodule_in_big_submodule_with_empty_init.I_AM}
INTO: {I_AM}
""")
print(f"""
IMPORTED: {SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE_IMPORTED_IN_SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_EMPTY_INIT}
INTO: {I_AM}
""")

# pkg.util_submodule.small_submodule.I_AM through pkg.big_submodule_with_nonempty_init.small_submodule
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_nonempty_init.util_submodule.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_nonempty_init.small_util_submodule_in_big_util_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_nonempty_init.SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
IN: {I_AM}
""")
print(f"""
ACCESSED: {util_submodule_imported_in_small_submodule_in_big_submodule_with_nonempty_init.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
IMPORTED: {small_util_submodule_in_big_util_submodule_imported_in_small_submodule_in_big_submodule_with_nonempty_init.I_AM}
INTO: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.small_submodule.util_submodule.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.small_submodule.small_util_submodule_in_big_util_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.small_submodule.SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
IN: {I_AM}
""")
print(f"""
IMPORTED: {SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE_IMPORTED_IN_SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT}
INTO: {I_AM}
""")

# pkg.util_submodule.small_submodule.I_AM through pkg.big_submodule_with_nonempty_init
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.util_submodule.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.small_util_submodule_in_big_util_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {big_submodule_with_nonempty_init.SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
IN: {I_AM}
""")
print(f"""
ACCESSED: {util_submodule_imported_in_big_submodule_with_nonempty_init.small_submodule.I_AM}
IN: {I_AM}
""")
print(f"""
ACCESSED: {small_util_submodule_in_big_util_submodule_imported_in_big_submodule_with_nonempty_init.I_AM}
IN: {I_AM}
""")
print(f"""
IMPORTED: {SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE_IMPORTED_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT}
INTO: {I_AM}
""")
