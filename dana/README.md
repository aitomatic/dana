# Dana - Backward Compatibility Shim

⚠️ **DEPRECATED**: This package provides backward compatibility only.

## Migration Guide

**Old code:**
```python
import dana
from dana import DanaParser, py2na
```

**New code:**
```python
import dana_lang
from dana_lang import DanaParser, py2na
```

## Why the change?

The package has been renamed from `dana` to `dana_lang` to better reflect its purpose and avoid naming conflicts.

## Timeline

- **Now**: `dana` package works but shows deprecation warnings
- **Future**: This compatibility shim will be removed

Please update your imports to use `dana_lang` directly.

