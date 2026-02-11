# app/services/ai/__init__.py
"""
BIZIO AI Copilot Services

This module contains all AI-related services for the Copilot feature:
- gemini_client: Wrapper for Google Gemini API with function calling
- rag_service: RAG implementation with hybrid search
- document_processor: Document chunking and embedding
- tool_registry: Function calling tools for database queries, calculations, etc.
- copilot_service: Main orchestrator for the AI Copilot
"""

from .gemini_client import GeminiClient
from .tool_registry import ToolRegistry, COPILOT_TOOLS
from .copilot_service import CopilotService

__all__ = [
    "GeminiClient",
    "ToolRegistry",
    "COPILOT_TOOLS",
    "CopilotService",
]
