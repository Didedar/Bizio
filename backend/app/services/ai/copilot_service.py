# app/services/ai/copilot_service.py
"""
Main orchestrator for the BIZIO AI Copilot.
Handles conversation management, tool execution, and response formatting.
"""
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from .gemini_client import GeminiClient, DecimalEncoder
from .tool_registry import ToolRegistry, COPILOT_TOOLS

logger = logging.getLogger(__name__)


class CopilotService:
    """
    Main service for the BIZIO AI Copilot.
    
    Responsibilities:
    - Manage conversations and message history
    - Execute tool calls and collect results
    - Format responses with citations and confidence
    - Handle streaming responses
    """
    
    def __init__(self, db: AsyncSession, tenant_id: int, user_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.gemini = GeminiClient()
        self.tool_registry = ToolRegistry(db, tenant_id)
    
    async def create_conversation(
        self,
        context_type: Optional[str] = None,
        context_id: Optional[int] = None
    ) -> models.CopilotConversation:
        """Create a new conversation."""
        conversation = models.CopilotConversation(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            context_type=context_type,
            context_id=context_id
        )
        self.db.add(conversation)
        await self.db.flush()
        return conversation
    
    async def get_conversation(self, conversation_id: int) -> Optional[models.CopilotConversation]:
        """Get a conversation by ID with messages."""
        query = (
            select(models.CopilotConversation)
            .options(selectinload(models.CopilotConversation.messages))
            .where(
                models.CopilotConversation.id == conversation_id,
                models.CopilotConversation.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_conversations(self, limit: int = 20) -> List[models.CopilotConversation]:
        """List recent conversations for the user."""
        query = (
            select(models.CopilotConversation)
            .options(selectinload(models.CopilotConversation.messages))
            .where(
                models.CopilotConversation.user_id == self.user_id,
                models.CopilotConversation.tenant_id == self.tenant_id
            )
            .order_by(models.CopilotConversation.updated_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        response_data: Optional[Dict] = None,
        tool_calls: Optional[List[Dict]] = None,
        tool_results: Optional[List[Dict]] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        processing_time_ms: int = 0
    ) -> models.CopilotMessage:
        """Add a message to a conversation."""
        message = models.CopilotMessage(
            conversation_id=conversation_id,
            role=models.MessageRole(role),
            content=content,
            response_data=response_data,
            tool_calls=tool_calls,
            tool_results=tool_results,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            processing_time_ms=processing_time_ms
        )
        self.db.add(message)
        
        # Update conversation title from first user message
        if role == "user":
            conversation = await self.get_conversation(conversation_id)
            if conversation and not conversation.title:
                # Use first 50 chars of message as title
                conversation.title = content[:50] + ("..." if len(content) > 50 else "")
                conversation.updated_at = datetime.utcnow()
        
        await self.db.flush()
        return message
    
    async def chat(
        self,
        conversation_id: int,
        user_message: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and return the AI response.
        
        Args:
            conversation_id: ID of the conversation
            user_message: The user's question/request
            context: Optional context about current page/entity
        
        Returns:
            {
                "content": str,
                "response_data": {...},
                "tool_calls": [...],
                "tool_results": [...],
                "processing_time_ms": int
            }
        """
        start_time = time.time()
        
        # Get conversation with history
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Copy messages list to avoid lazy loading issues
        history_messages = list(conversation.messages[-10:])  # Last 10 messages for context
        
        # Save user message
        await self.add_message(conversation_id, "user", user_message)
        
        # Build message history for context
        messages = []
        for msg in history_messages:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # Add new user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Gemini with tools
        response = await self.gemini.chat(messages, tools=COPILOT_TOOLS, context=context)
        
        tool_calls = response.get("tool_calls")
        tool_results = []
        
        # Execute any tool calls
        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]
                
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                result = await self.tool_registry.execute(tool_name, tool_args)
                tool_results.append({
                    "tool_name": tool_name,
                    "result": result
                })
            
            # Get final response with tool results
            response = await self.gemini.chat_with_tool_results(
                messages,
                tool_results,
                tools=COPILOT_TOOLS
            )
        
        # Format response data
        response_data = self._format_response_data(response["content"], tool_results)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Save assistant message
        await self.add_message(
            conversation_id,
            "assistant",
            response["content"],
            response_data=response_data,
            tool_calls=tool_calls,
            tool_results=tool_results,
            input_tokens=response.get("input_tokens", 0),
            output_tokens=response.get("output_tokens", 0),
            processing_time_ms=processing_time_ms
        )
        
        await self.db.commit()
        
        return {
            "content": response["content"],
            "response_data": response_data,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "processing_time_ms": processing_time_ms
        }
    
    async def chat_stream(
        self,
        conversation_id: int,
        user_message: str,
        context: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a chat response with tool execution.
        
        Yields:
            {"type": "tool_call", "name": str, "status": str}
            {"type": "text", "content": str}
            {"type": "done", "response_data": {...}}
        """
        start_time = time.time()
        
        # Get conversation
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            yield {"type": "error", "message": "Conversation not found"}
            return
        
        # Copy messages list to avoid lazy loading issues
        history_messages = list(conversation.messages[-10:])
        
        # Save user message
        await self.add_message(conversation_id, "user", user_message)
        await self.db.commit()
        
        # Build message history
        messages = []
        for msg in history_messages:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        messages.append({"role": "user", "content": user_message})
        
        # First call to check for tool calls
        response = await self.gemini.chat(messages, tools=COPILOT_TOOLS, context=context)
        
        tool_calls = response.get("tool_calls")
        tool_results = []
        
        if tool_calls:
            # Execute tools and yield progress
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                
                yield {
                    "type": "tool_call",
                    "name": tool_name,
                    "status": "executing"
                }
                
                result = await self.tool_registry.execute(tool_name, tool_call["arguments"])
                tool_results.append({
                    "tool_name": tool_name,
                    "result": result
                })
                
                yield {
                    "type": "tool_call",
                    "name": tool_name,
                    "status": "complete",
                    "result_preview": self._preview_result(result)
                }
            
            # Stream final response with tool results
            extended_messages = messages.copy()
            results_text = "Tool execution results:\n\n"
            for result in tool_results:
                results_text += f"**{result['tool_name']}**:\n"
                results_text += f"```json\n{json.dumps(result['result'], cls=DecimalEncoder, indent=2)}\n```\n\n"
            
            extended_messages.append({
                "role": "user",
                "content": f"[TOOL RESULTS]\n\n{results_text}\n\nProvide your answer based on these results."
            })
            
            full_content = ""
            async for chunk in self.gemini.stream_chat(extended_messages, tools=COPILOT_TOOLS):
                yield {"type": "text", "content": chunk}
                full_content += chunk
        else:
            # No tools needed, stream directly
            full_content = ""
            async for chunk in self.gemini.stream_chat(messages, tools=COPILOT_TOOLS, context=context):
                yield {"type": "text", "content": chunk}
                full_content += chunk
        
        # Format and save response
        response_data = self._format_response_data(full_content, tool_results)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        await self.add_message(
            conversation_id,
            "assistant",
            full_content,
            response_data=response_data,
            tool_calls=tool_calls,
            tool_results=tool_results,
            processing_time_ms=processing_time_ms
        )
        await self.db.commit()
        
        yield {
            "type": "done",
            "response_data": response_data,
            "tool_calls": tool_calls,
            "processing_time_ms": processing_time_ms
        }
    
    def _format_response_data(
        self,
        content: str,
        tool_results: List[Dict]
    ) -> Dict[str, Any]:
        """Format response data with key numbers, sources, and confidence."""
        
        # Extract key numbers from tool results
        key_numbers = []
        sources = []
        
        for result in tool_results:
            tool_name = result["tool_name"]
            data = result.get("result", {})
            
            if not data.get("success", True):
                continue
            
            inner = data.get("result", data)
            
            # Extract value and formula if present
            if "value" in inner:
                key_numbers.append({
                    "label": inner.get("metric", tool_name),
                    "value": inner["value"],
                    "formula": inner.get("formula"),
                    "source": tool_name
                })
            
            # Extract sources
            if "sources" in inner:
                sources.extend(inner["sources"])
        
        # Determine confidence level
        confidence = self._estimate_confidence(tool_results, content)
        
        return {
            "key_numbers": key_numbers,
            "sources": list(set(sources))[:20],  # Dedupe, limit to 20
            "confidence": confidence,
            "has_tool_data": len(tool_results) > 0
        }
    
    def _estimate_confidence(
        self,
        tool_results: List[Dict],
        content: str
    ) -> Dict[str, Any]:
        """Estimate confidence level based on data quality."""
        
        # High confidence: multiple successful tool calls, specific data
        # Medium: some tool calls, partial data
        # Low: no tool calls, or errors
        
        successful_tools = sum(1 for r in tool_results if r.get("result", {}).get("success", True))
        total_tools = len(tool_results)
        
        if total_tools == 0:
            # No tools used - might be a general question
            if "I don't have" in content or "I couldn't find" in content:
                return {
                    "level": "low",
                    "reason": "No data available to answer this question"
                }
            return {
                "level": "medium",
                "reason": "Answer based on general knowledge, no specific data queried"
            }
        
        if successful_tools == total_tools and total_tools >= 2:
            return {
                "level": "high",
                "reason": f"Based on {successful_tools} successful data queries"
            }
        elif successful_tools > 0:
            return {
                "level": "medium",
                "reason": f"{successful_tools}/{total_tools} queries returned data"
            }
        else:
            return {
                "level": "low",
                "reason": "Data queries failed or returned no results"
            }
    
    def _preview_result(self, result: Dict) -> str:
        """Create a short preview of a tool result."""
        if not result.get("success", True):
            return f"Error: {result.get('error', 'Unknown error')}"
        
        inner = result.get("result", result)
        
        if "value" in inner:
            return f"Value: {inner['value']}"
        if "count" in inner:
            return f"Found {inner['count']} items"
        if "total" in inner:
            return f"Total: {inner['total']}"
        if "rows" in inner:
            return f"Found {len(inner['rows'])} records"
        
        return "Completed"
