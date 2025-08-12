"""
Dana Stdlib Resources

This directory contains pure Dana resource implementations that extend
the core resource system. Only Dana (.na) files should be placed here
to encourage Dana-first development.

Python resources should go in dana/core/resource/plugins/ if absolutely necessary.

All resources in this directory are automatically discovered and loaded by
the ResourceLoader when the resource system initializes.

Current Resources:
- simple_cache.na - In-memory cache resource (Dana)
- webhook_resource.na - Webhook endpoint resource (Dana)
- memory_resource.na - Memory management resource (Dana)
- knowledge_base_resource.na - Knowledge base resource (Dana)
- coding_resource.na - Code generation resource (Dana)

To add a new resource:
1. Create a .na file in this directory (Dana implementations only!)
2. Define your resource following the Dana resource pattern
3. The resource will be automatically available at runtime

Example Dana resource (my_resource.na):
```dana
resource MyCustomResource:
    kind: str = "custom"
    endpoint: str = ""

def (resource: MyCustomResource) query(request: str) -> str:
    return f"Custom response for: {request}"
```
"""
