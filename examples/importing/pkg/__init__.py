from . import big_namespace_submodule
from .big_namespace_submodule import small_submodule as small_submodule_in_big_namespace_submodule
from .big_namespace_submodule.small_submodule import I_AM as SMALL_SUBMODULE_IN_BIG_NAMESPACE_SUBMODULE

from . import big_submodule_with_empty_init
from .big_submodule_with_empty_init import small_submodule as small_submodule_in_big_submodule_with_empty_init
from .big_submodule_with_empty_init.small_submodule import I_AM as SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_EMPTY_INIT

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
    util_submodule as util_submodule_in_big_submodule_with_nonempty_init,
    small_util_submodule_in_big_util_submodule as small_util_submodule_in_big_util_submodule_imported_in_big_submodule_with_nonempty_init,
    SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE as SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE_IMPORTED_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT,
)

from . import util_submodule
from .util_submodule import small_submodule as small_util_submodule_in_util_submodule
from .util_submodule.small_submodule import I_AM as SMALL_UTIL_SUBMODULE_IN_UTIL_SUBMODULE


I_AM = 'a package'


# access `big_namespace_submodule` and its nested objects
print(f"""
IMPORTED: {big_namespace_submodule}
INTO: {I_AM}
""")

print(f"""
ACCESSED: {big_namespace_submodule.small_submodule}
IN: {I_AM}
""")

print(f"""
ACCESSED: {big_namespace_submodule.small_submodule.I_AM}
IN: {I_AM}
""")

print(f"""
ACCESSED: {big_namespace_submodule.small_submodule.util_submodule}
IN: {I_AM}
""")

print(f"""
ACCESSED: {big_namespace_submodule.small_submodule.util_submodule.small_submodule}
IN: {I_AM}
""")

print(f"""
ACCESSED: {big_namespace_submodule.small_submodule.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
""")

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


# access `small_submodule_in_big_namespace_submodule` and its nested objects
print(f"""
USED: {small_submodule_in_big_namespace_submodule}
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

print(f"""
ACCESSED: {small_submodule_in_big_namespace_submodule.util_submodule}
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


# access `big_submodule_with_empty_init` and its nested objects
print(f"""
IMPORTED: {big_submodule_with_empty_init}
IN: {I_AM}
""")

print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule}
IN: {I_AM}
""")

print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule.I_AM}
IN: {I_AM}
""")

print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule.util_submodule}
IN: {I_AM}
""")

print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule.util_submodule.small_submodule}
IN: {I_AM}
""")

print(f"""
ACCESSED: {big_submodule_with_empty_init.small_submodule.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
""")

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


# access `small_submodule_in_big_submodule_with_empty_init` and its nested objects
print(f"""
IMPORTED: {small_submodule_in_big_submodule_with_empty_init}
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

print(f"""
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.util_submodule}
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


# access `big_submodule_with_nonempty_init` and its nested objects
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

print(f"""
ACCESSED: {big_submodule_with_nonempty_init.util_submodule}
IN: {I_AM}
""")

print(f"""
ACCESSED: {big_submodule_with_nonempty_init.util_submodule.small_submodule}
IN: {I_AM}
""")

print(f"""
ACCESSED: {big_submodule_with_nonempty_init.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
""")

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




# ====== TEMP AREA


print(f'
IMPORTED: {SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_EMPTY_INIT}
INTO: {I_AM}
')

print(f'
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.util_submodule}
IN: {I_AM}
')

print(f'
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.util_submodule.small_submodule}
IN: {I_AM}
')

print(f'
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
')

print(f'
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.util_submodule.small_submodule.I_AM}
IN: {I_AM}
')

print(f'
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.small_util_submodule_in_big_util_submodule.I_AM}
IN: {I_AM}
')

print(f'
ACCESSED: {small_submodule_in_big_submodule_with_empty_init.SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
IN: {I_AM}
')

# =======

print(f'
ACCESSED: {big_submodule_with_nonempty_init.small_submodule}
IN: {I_AM}
')
print(f'
ACCESSED: {big_submodule_with_nonempty_init.small_submodule_in_big_submodule_with_nonempty_init}
IN: {I_AM}
')

print(f'
ACCESSED: {big_submodule_with_nonempty_init.small_submodule.I_AM}
IN: {I_AM}
')
print(f'
ACCESSED: {big_submodule_with_empty_init.small_submodule_in_big_submodule_with_nonempty_init.I_AM}
IN: {I_AM}
')

print(f'
USED: {big_submodule_with_nonempty_init.small_submodule.util_submodule}
IN: {I_AM}
')

print(f'
USED: {big_submodule_with_nonempty_init.small_submodule.util_submodule.small_submodule}
IN: {I_AM}
')

print(f'
USED: {big_submodule_with_nonempty_init.small_submodule.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
')

print(f'
USED: {big_submodule_with_nonempty_init.small_submodule.util_submodule.small_submodule.I_AM}
IN: {I_AM}
')

print(f'
USED: {big_submodule_with_nonempty_init.small_submodule.small_util_submodule_in_big_util_submodule.I_AM}
IN: {I_AM}
')

print(f'
USED: {big_submodule_with_nonempty_init.small_submodule.SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
IN: {I_AM}
')


# access `small_submodule_in_big_submodule_with_nonempty_init` and its nested objects
print(f'
USED: {small_submodule_in_big_submodule_with_nonempty_init}
IN: {I_AM}
')

print(f'
USED: {small_submodule_in_big_submodule_with_nonempty_init.I_AM}
IN: {I_AM}
')

print(f'
USED: {small_submodule_in_big_submodule_with_nonempty_init.util_submodule}
IN: {I_AM}
')

print(f'
USED: {small_submodule_in_big_submodule_with_nonempty_init.util_submodule.small_submodule}
IN: {I_AM}
')

print(f'
USED: {small_submodule_in_big_submodule_with_nonempty_init.small_util_submodule_in_big_util_submodule}
IN: {I_AM}
')

print(f'
USED: {small_submodule_in_big_submodule_with_nonempty_init.util_submodule.small_submodule.I_AM}
IN: {I_AM}
')

print(f'
USED: {small_submodule_in_big_submodule_with_nonempty_init.small_util_submodule_in_big_util_submodule.I_AM}
IN: {I_AM}
')

print(f'
USED: {small_submodule_in_big_submodule_with_nonempty_init.SMALL_UTIL_SUBMODULE_IN_BIG_UTIL_SUBMODULE}
IN: {I_AM}
')


# access `SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT`
print(f'
IMPORTED: {SMALL_SUBMODULE_IN_BIG_SUBMODULE_WITH_NONEMPTY_INIT}
INTO: {I_AM}
')


# access `util_submodule` and its nested objects
print(f"""
IMPORTED: {util_submodule}
INTO: {I_AM}
""")

print(f"""
ACCESSED: {util_submodule.small_submodule}
IN: {I_AM}
""")

print(f"""
ACCESSED: {util_submodule.small_submodule.I_AM}
IN: {I_AM}
""")


# access `small_util_submodule_in_util_submodule` and its nested objects
print(f"""
IMPORTED: {small_util_submodule_in_util_submodule}
INTO: {I_AM}
""")

print(f"""
ACCESSED: {small_util_submodule_in_util_submodule.I_AM}
IN: {I_AM}
""")


# access `SMALL_UTIL_SUBMODULE_IN_UTIL_SUBMODULE`
print(f"""
IMPORTED: {SMALL_UTIL_SUBMODULE_IN_UTIL_SUBMODULE}
INTO: {I_AM}
""")
