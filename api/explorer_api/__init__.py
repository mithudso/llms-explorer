"""explorer-api — the LLMS-Explorer accounts, metering and hosted-MCP service.

Build-order step 3 of docs/site/00-platform-design.md §10. The hub
(``~/.global-ai-hub``) is read-only to this service: it is imported and called,
never written.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
