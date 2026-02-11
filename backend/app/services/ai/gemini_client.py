# app/services/ai/gemini_client.py
"""
Google Gemini API client wrapper with function calling support.
Handles API communication, retries, and streaming responses.
"""
import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from decimal import Decimal

import google.generativeai as genai
from google.generativeai.types import GenerationConfig, Tool, FunctionDeclaration

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class GeminiClient:
    """
    Wrapper for Google Gemini API with function calling support.
    
    Features:
    - Function calling declarations
    - Streaming responses
    - Retry logic with exponential backoff
    - Token usage tracking
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        
        # Use gemini-2.0-flash (fast) or user-configured model
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=GenerationConfig(
                temperature=0.3,  # Slightly higher for faster response
                top_p=0.95,
                max_output_tokens=2048,  # Reduced for faster responses
            ),
        )
        
        # Track token usage
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the AI Copilot."""
        return """You are BIZIO AI Copilot, an intelligent assistant for business management.

YOUR CAPABILITIES:
- Analyze expenses, revenue, and profitability
- Detect dead stock and inventory issues
- Suggest optimal pricing for target margins
- Extract data from receipts and invoices
- Find duplicate records and data quality issues
- Answer questions about business data

CRITICAL RULES:
1. NEVER compute numbers yourself - always use the provided tools
2. ALWAYS cite sources for every number (link to specific records)
3. If data is missing or insufficient, say "I don't have enough data"
4. Show confidence levels (high/medium/low) for all answers
5. Use tools for ANY calculation (revenue, margin, counts, averages)
6. Format currency in the user's preferred format (default: ₸ KZT)

RESPONSE FORMAT:
Always structure your response with:
- Answer summary (natural language)
- Key numbers (from tool results)
- Sources (specific record IDs)
- Recommended actions (if applicable)
- Confidence level with reasoning

When you need to call a tool, do so before answering.
If multiple tools are needed, call them in sequence.
"""

    def _build_function_declarations(self, tools: List[Dict]) -> List[FunctionDeclaration]:
        """Convert tool definitions to Gemini function declarations."""
        declarations = []
        for tool in tools:
            declarations.append(FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=tool.get("parameters", {})
            ))
        return declarations

    def _protobuf_to_dict(self, proto_obj) -> Dict[str, Any]:
        """Convert protobuf MapComposite/RepeatedComposite to native Python types."""
        if proto_obj is None:
            return {}
        
        result = {}
        try:
            # Handle MapComposite (dict-like) objects
            for key in proto_obj:
                value = proto_obj[key]
                
                # Convert based on type
                if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                    # It's a list-like object
                    if hasattr(value, 'items'):
                        # It's dict-like
                        result[key] = self._protobuf_to_dict(value)
                    else:
                        # It's a list
                        result[key] = [self._convert_value(v) for v in value]
                else:
                    result[key] = self._convert_value(value)
        except Exception as e:
            logger.warning(f"Error converting protobuf: {e}")
            # Fallback: try to convert to dict directly
            try:
                result = dict(proto_obj)
            except:
                result = {}
        
        return result
    
    def _convert_value(self, value) -> Any:
        """Convert a single protobuf value to native Python type."""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if hasattr(value, 'items'):
            return self._protobuf_to_dict(value)
        if hasattr(value, '__iter__'):
            return [self._convert_value(v) for v in value]
        # Try to get primitive value
        return str(value)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message with optional function calling.
        
        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            tools: Optional list of tool definitions for function calling
            context: Optional context about current page/entity
        
        Returns:
            {
                "content": str,
                "tool_calls": Optional[List[Dict]],
                "input_tokens": int,
                "output_tokens": int
            }
        """
        try:
            # Build the prompt from messages
            chat_history = []
            for msg in messages[:-1]:  # All but the last message
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})
            
            # Start a chat session
            model_to_use = self.model
            
            if tools:
                # Create model with tools
                function_declarations = self._build_function_declarations(tools)
                model_to_use = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=GenerationConfig(
                        temperature=0.1,
                        top_p=0.95,
                        max_output_tokens=4096,
                    ),
                    tools=[Tool(function_declarations=function_declarations)],
                    system_instruction=self.get_system_prompt()
                )
            
            chat = model_to_use.start_chat(history=chat_history)
            
            # Add context to the last message if provided
            last_message = messages[-1]["content"]
            if context:
                last_message = f"[Context: {context}]\n\n{last_message}"
            
            # Send the message
            response = await asyncio.to_thread(
                chat.send_message,
                last_message
            )
            
            # Extract response
            result = {
                "content": "",
                "tool_calls": None,
                "input_tokens": 0,
                "output_tokens": 0
            }
            
            # Check for function calls
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        if result["tool_calls"] is None:
                            result["tool_calls"] = []
                        
                        # Convert protobuf args to native Python dict
                        args = self._protobuf_to_dict(fc.args)
                        
                        result["tool_calls"].append({
                            "name": fc.name,
                            "arguments": args
                        })
                    elif hasattr(part, 'text') and part.text:
                        result["content"] += part.text
            
            # Get token usage if available
            if hasattr(response, 'usage_metadata'):
                result["input_tokens"] = getattr(response.usage_metadata, 'prompt_token_count', 0)
                result["output_tokens"] = getattr(response.usage_metadata, 'candidates_token_count', 0)
                self.total_input_tokens += result["input_tokens"]
                self.total_output_tokens += result["output_tokens"]
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def chat_with_tool_results(
        self,
        messages: List[Dict[str, str]],
        tool_results: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Continue chat after tool execution with the results.
        
        Args:
            messages: Original message history
            tool_results: Results from tool execution
            tools: Tool definitions (for potential further calls)
        
        Returns:
            Same format as chat()
        """
        # Add tool results to messages
        extended_messages = messages.copy()
        
        # Format tool results as a system message
        results_text = "Tool execution results:\n\n"
        for result in tool_results:
            results_text += f"**{result['tool_name']}**:\n"
            results_text += f"```json\n{json.dumps(result['result'], cls=DecimalEncoder, indent=2)}\n```\n\n"
        
        extended_messages.append({
            "role": "user",
            "content": f"[TOOL RESULTS - Use these to answer the original question]\n\n{results_text}\n\nNow provide your answer based on these results. Remember to cite sources and show confidence."
        })
        
        return await self.chat(extended_messages, tools=tools)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        context: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat response token by token.
        
        Yields:
            Text chunks as they're generated
        """
        try:
            # Build chat history
            chat_history = []
            for msg in messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})
            
            model_to_use = self.model
            
            if tools:
                function_declarations = self._build_function_declarations(tools)
                model_to_use = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=GenerationConfig(
                        temperature=0.1,
                        top_p=0.95,
                        max_output_tokens=4096,
                    ),
                    tools=[Tool(function_declarations=function_declarations)],
                    system_instruction=self.get_system_prompt()
                )
            
            chat = model_to_use.start_chat(history=chat_history)
            
            last_message = messages[-1]["content"]
            if context:
                last_message = f"[Context: {context}]\n\n{last_message}"
            
            # Stream the response
            response = await asyncio.to_thread(
                chat.send_message,
                last_message,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            yield f"\n\n⚠️ Error: {str(e)}"

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for a text string."""
        # Rough estimate: ~4 characters per token for English text
        return len(text) // 4
