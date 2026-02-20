"""
jackknife — a dual-purpose foundational toolkit.

Import individual blades:
    from jackknife.blades.llm import create_llm, LLMRequest
    from jackknife.blades.memory import create_memory_store, MemoryEntry
    from jackknife.blades.storage import create_storage
    from jackknife.blades.data import create_connector
    from jackknife.blades.mcp import create_mcp_client
    from jackknife.blades.agents import create_orchestrator

Or use core utilities directly:
    from jackknife.core import get_settings, get_logger, JackknifeError
"""

__version__ = "0.1.0"
__author__ = "Brian Raney"

from jackknife.core.config import Settings, get_settings, validate_config_on_startup
from jackknife.core.exceptions import JackknifeError
from jackknife.core.logging import configure_logging, get_logger

__all__ = [
    "__version__",
    # Config
    "Settings",
    "get_settings",
    "validate_config_on_startup",
    # Exceptions
    "JackknifeError",
    # Logging
    "configure_logging",
    "get_logger",
]
