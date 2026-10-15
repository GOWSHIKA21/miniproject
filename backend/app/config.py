"""
Compatibility re-export layer: redirects all imports to backend.app.core.config.
"""
from backend.app.core.config import settings, Settings

__all__ = ["settings", "Settings"]
