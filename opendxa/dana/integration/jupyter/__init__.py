"""
Dana Jupyter Integration

Provides IPython magic commands for running Dana code in Jupyter notebooks.
"""

from .magic import DanaMagics


def load_ipython_extension(ipython):
    """Load the Dana magic commands in IPython/Jupyter."""
    ipython.register_magic_functions(DanaMagics)


def unload_ipython_extension(ipython):
    """Unload the Dana magic commands from IPython/Jupyter."""
    # IPython handles this automatically
    pass


__all__ = ["DanaMagics", "load_ipython_extension", "unload_ipython_extension"]
