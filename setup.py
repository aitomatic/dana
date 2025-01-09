"""Setup file for DXA package."""

from pathlib import Path

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages  # pylint: disable=deprecated-module

def read_requirements(filename: str) -> list[str]:
    """Read requirements from file."""
    return [line.strip() 
            for line in Path(filename).read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.startswith('#')]

setup(
    name="dxa",
    version="0.1.0",
    packages=find_packages(),
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        "dev": read_requirements('requirements-dev.txt'),
        "viz": read_requirements('requirements-viz.txt'),
    },
    python_requires=">=3.12",  # require Python 3.12+ for compatibility with other potential deps incl. OpenSSA
)
