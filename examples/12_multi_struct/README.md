# Multi-Struct Example: Understanding Dana's Import and Method System

This example demonstrates how to work with structs and methods across multiple files in Dana.

## The Problem

When you define structs and methods in one file and import them in another, you may encounter issues with method calls. This is due to how Dana's import system handles method registration.

## Solution 1: Traditional Struct Functions (Recommended)

Use the traditional Dana pattern where functions take struct instances as their first parameter:

### file_loader.na
```dana
struct FileLoader:
    name : str = "FileLoader"

def say_hi(loader: FileLoader):
    return "Hello, world!"

def list_files(loader: FileLoader, path: str = "."):
    print(say_hi(loader))
    return ["file1.txt", "file2.txt", "file3.txt"]

loader = FileLoader()
```

### main.na
```dana
import file_loader

loader = file_loader.FileLoader()

name = loader.name # This works
print(name)

# Use the functions directly from the module
files = file_loader.list_files(loader) # This works
print(files)

print(file_loader.say_hi(loader))
```

## Solution 2: Method Syntax (Limited Support)

The receiver syntax `def (instance: Type) method()` works within the same file but has limited support across module boundaries:

### file_loader.na
```dana
struct FileLoader:
    name : str = "FileLoader"

def (loader: FileLoader) say_hi():
    return "Hello, world!"

def (loader: FileLoader) list_files(path: str = "."):
    print(loader.say_hi())
    return ["file1.txt", "file2.txt", "file3.txt"]

loader = FileLoader()
```

### main.na
```dana
import file_loader

loader = file_loader.FileLoader()

name = loader.name # This works
print(name)

# Method syntax may not work across module boundaries
files = loader.list_files() # This may fail
print(files)

print(loader.say_hi())
```

## Why This Happens

1. **Module Isolation**: When you import a module, the methods defined in that module are not automatically registered in the global struct function registry.

2. **Method Registration**: Dana's receiver syntax methods need to be registered in the `STRUCT_FUNCTION_REGISTRY` to work with method syntax calls.

3. **Import Context**: The import system creates isolated contexts, and method registration doesn't always propagate correctly.

## Best Practices

1. **Use Traditional Struct Functions**: For cross-module usage, prefer the traditional `def function_name(instance: Type)` pattern.

2. **Method Syntax for Local Use**: Use receiver syntax only within the same file where the struct and methods are defined.

3. **Explicit Function Calls**: When importing from other modules, call functions explicitly: `module.function(instance)`.

## Testing

Run the examples to see the difference:

```bash
# Test traditional approach (works)
python -m dana examples/12_multi_struct/main.na
# Output: FileLoader, ['file1.txt', 'file2.txt', 'file3.txt'], Hello, world!

# Test method syntax approach (fails)
python -m dana examples/12_multi_struct/main_methods.na
# Error: AttributeError - 'FileLoader' object has no method 'list_files'
```

## Summary

The traditional struct function approach (`def function_name(instance: Type)`) works reliably across module boundaries, while the receiver syntax (`def (instance: Type) method()`) has limitations when importing from other modules.

For cross-module usage, always use the traditional approach and call functions explicitly: `module.function(instance)`.
