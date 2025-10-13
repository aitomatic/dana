#!/usr/bin/env python3
"""AISuite/Anthropic compatibility patch for Dana.

This module applies monkey patches to fix the known compatibility issue between
AISuite 0.1.11, Anthropic 0.30.1, and httpx 0.28.1 where the 'proxies' parameter
causes a TypeError.

The issue is that:
1. AISuite 0.1.11 requires anthropic>=0.30.1,<0.31.0
2. Anthropic 0.30.1 has a bug where it passes 'proxies' to httpx
3. httpx 0.28.1 doesn't accept 'proxies' in the way Anthropic passes it
4. This causes Client.__init__() got an unexpected keyword argument 'proxies'

This patch fixes the issue by:
1. Ensuring 'proxies' parameter is set to None where needed
2. Filtering out 'proxies' from httpx calls where it causes issues
"""

# Global flag to track if patch has been applied
_PATCH_APPLIED = False


def apply_aisuite_patch() -> bool:
    """Apply the AISuite/Anthropic compatibility patch.

    Returns:
        bool: True if patch was applied successfully, False otherwise
    """
    global _PATCH_APPLIED

    if _PATCH_APPLIED:
        return True

    try:
        from anthropic import Anthropic

        # Store the original __init__ method
        original_init = Anthropic.__init__

        def patched_init(self, **kwargs):
            """Patched __init__ that filters out the 'proxies' parameter."""
            # Remove 'proxies' parameter that causes issues with httpx
            if "proxies" in kwargs:
                del kwargs["proxies"]
            return original_init(self, **kwargs)

        # Apply the patch
        Anthropic.__init__ = patched_init

        # Patch the base client to ensure proxies is set correctly
        try:
            from anthropic._base_client import BaseClient

            original_base_init = BaseClient.__init__

            def patched_base_init(self, **kwargs):
                """Patched BaseClient __init__ that ensures 'proxies' is set to None."""
                # Ensure 'proxies' is set to None if not provided (it's required but should be None)
                if "proxies" not in kwargs:
                    kwargs["proxies"] = None
                return original_base_init(self, **kwargs)

            # Apply the patch
            BaseClient.__init__ = patched_base_init

        except ImportError:
            # BaseClient patch is optional
            pass

        # Patch SyncHttpxClientWrapper to filter proxies before passing to httpx
        try:
            from anthropic._base_client import SyncHttpxClientWrapper

            original_sync_init = SyncHttpxClientWrapper.__init__

            def patched_sync_init(self, **kwargs):
                """Patched SyncHttpxClientWrapper __init__ that filters out proxies before passing to httpx."""
                # Remove 'proxies' parameter before passing to httpx since it doesn't accept it
                if "proxies" in kwargs:
                    del kwargs["proxies"]
                return original_sync_init(self, **kwargs)

            # Apply the patch
            SyncHttpxClientWrapper.__init__ = patched_sync_init

        except ImportError:
            # SyncHttpxClientWrapper patch is optional
            pass

        # Also try to patch httpx.Client if it's available
        try:
            import httpx

            original_httpx_init = httpx.Client.__init__

            def patched_httpx_init(self, **kwargs):
                """Patched httpx.Client __init__ that filters out 'proxies' parameter."""
                # Remove 'proxies' parameter that causes issues
                if "proxies" in kwargs:
                    del kwargs["proxies"]
                return original_httpx_init(self, **kwargs)

            # Apply the patch
            httpx.Client.__init__ = patched_httpx_init

        except ImportError:
            # httpx patch is optional
            pass

        _PATCH_APPLIED = True
        return True

    except Exception as e:
        print(f"Warning: Failed to apply AISuite patch: {e}")
        return False


def is_patch_applied() -> bool:
    """Check if the AISuite patch has been applied.

    Returns:
        bool: True if patch is applied, False otherwise
    """
    return _PATCH_APPLIED


# Auto-apply patch when module is imported
apply_aisuite_patch()
