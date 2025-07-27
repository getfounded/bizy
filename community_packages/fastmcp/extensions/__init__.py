"""FastMCP Extensions for Business Logic Integration.

This package provides extensions to FastMCP for business context
metadata and cross-framework tool coordination.
"""

from .business_context_extension import BusinessContextExtension
from .tool_metadata_extension import ToolMetadataExtension
from .framework_bridge_extension import FrameworkBridgeExtension

__all__ = [
    "BusinessContextExtension",
    "ToolMetadataExtension",
    "FrameworkBridgeExtension"
]