#!/usr/bin/env python3
"""
LLM Adapter for Engram Memory System

This module implements an adapter for interacting with the Tekton LLM service,
providing a unified interface for LLM capabilities across the system.
"""

import os
import json
import logging
import requests
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("engram.llm_adapter")

class LLMAdapter:
    """
    Client for interacting with LLMs through the Tekton LLM Adapter.
    
    This class provides a unified interface for LLM operations, connecting
    to the centralized Tekton LLM adapter service.
    """
    
    def __init__(self, adapter_url: Optional[str] = None):
        """
        Initialize the LLM Adapter client.
        
        Args:
            adapter_url: URL for the LLM adapter service
        """
        # Default to environment variable or standard port
        rhetor_port = os.environ.get("RHETOR_PORT", "8003")
        default_adapter_url = f"http://localhost:{rhetor_port}"
        
        self.adapter_url = adapter_url or os.environ.get("LLM_ADAPTER_URL", default_adapter_url)
        self.default_provider = os.environ.get("LLM_PROVIDER", "anthropic")
        self.default_model = os.environ.get("LLM_MODEL", "claude-3-haiku-20240307")
        self.ws_url = self.adapter_url.replace("http://", "ws://").replace("https://", "wss://")
        
        # For WebSocket streaming
        self.ws_port = os.environ.get("LLM_ADAPTER_WS_PORT", "8301")
        if ":" in self.ws_url:
            # Replace the port in the URL
            base_url = self.ws_url.split(":")[0] + ":" + self.ws_url.split(":")[1]
            self.ws_url = f"{base_url}:{self.ws_port}"
        else:
            # Append the port
            self.ws_url = f"{self.ws_url}:{self.ws_port}"
            
        logger.info(f"LLM Adapter initialized with URL: {self.adapter_url}")
        logger.info(f"WebSocket URL for streaming: {self.ws_url}")
    
    async def chat(self, 
                  messages: List[Dict[str, str]],
                  model: Optional[str] = None,
                  temperature: float = 0.7,
                  max_tokens: Optional[int] = None,
                  stream: bool = False,
                  system_prompt: Optional[str] = None) -> Union[str, AsyncGenerator[str, None]]:
        """
        Send a chat request to the LLM adapter.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: LLM model to use (defaults to configured default)
            temperature: Temperature parameter for generation
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            system_prompt: Optional system prompt
            
        Returns:
            If stream=False, returns the complete response as a string
            If stream=True, returns an async generator yielding response chunks
        """
        if stream:
            return self._stream_chat(messages, model, temperature, max_tokens, system_prompt)
        
        # Standard synchronous request
        payload = {
            "provider": self.default_provider,
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            response = requests.post(
                f"{self.adapter_url}/v1/chat/completions",
                json=payload,
                timeout=120
            )
            
            if response.status_code != 200:
                logger.error(f"LLM request failed: {response.status_code}, {response.text}")
                return f"Error: Failed to get LLM response (Status: {response.status_code})"
                
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
        except requests.RequestException as e:
            logger.error(f"LLM request exception: {str(e)}")
            return self._get_fallback_response()
            
        except Exception as e:
            logger.error(f"Unexpected error in LLM request: {str(e)}")
            return f"Error: {str(e)}"
    
    async def _stream_chat(self, 
                         messages: List[Dict[str, str]],
                         model: Optional[str] = None,
                         temperature: float = 0.7,
                         max_tokens: Optional[int] = None,
                         system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Stream a chat response from the LLM adapter via WebSocket.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: LLM model to use (defaults to configured default)
            temperature: Temperature parameter for generation
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            
        Yields:
            Response chunks as they arrive
        """
        payload = {
            "provider": self.default_provider,
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(f"{self.ws_url}/v1/chat/completions/stream") as ws:
                    await ws.send_json(payload)
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                if data.get("type") == "content":
                                    yield data.get("content", "")
                                elif data.get("type") == "error":
                                    logger.error(f"Streaming error: {data.get('error')}")
                                    yield f"Error: {data.get('error')}"
                                    break
                                elif data.get("type") == "done":
                                    break
                            except json.JSONDecodeError:
                                logger.error(f"Invalid JSON in stream: {msg.data}")
                                continue
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WebSocket error: {ws.exception()}")
                            break
                            
        except aiohttp.ClientError as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            yield self._get_fallback_response()
        except Exception as e:
            logger.error(f"Unexpected error in streaming: {str(e)}")
            yield f"Error: {str(e)}"
    
    async def analyze_memory(self, 
                           content: str, 
                           context: Optional[str] = None, 
                           model: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze text using the LLM adapter to extract insights for memory.
        
        Args:
            content: The text content to analyze
            context: Optional additional context
            model: LLM model to use (defaults to configured default)
            
        Returns:
            Dictionary with analysis results
        """
        system_prompt = """
        You are an AI assistant helping to analyze and structure memory content.
        Extract key information, entities, and relationships from the provided text.
        Focus on identifying important concepts, facts, and potential connections to existing knowledge.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please analyze the following content:\n\n{content}"}
        ]
        
        if context:
            messages.append({
                "role": "user", 
                "content": f"Consider this additional context:\n\n{context}"
            })
            
        try:
            response = await self.chat(messages, model=model)
            return {
                "analysis": response,
                "success": True
            }
        except Exception as e:
            logger.error(f"Memory analysis error: {str(e)}")
            return {
                "analysis": "",
                "success": False,
                "error": str(e)
            }
    
    async def categorize_memory(self, 
                              content: str, 
                              categories: List[str],
                              model: Optional[str] = None) -> Dict[str, Any]:
        """
        Categorize memory content using the LLM adapter.
        
        Args:
            content: The text content to categorize
            categories: List of available categories
            model: LLM model to use (defaults to configured default)
            
        Returns:
            Dictionary with categorization results
        """
        categories_list = ", ".join(categories)
        
        system_prompt = f"""
        You are an AI assistant that categorizes content into predefined categories.
        The available categories are: {categories_list}
        Analyze the provided content and assign it to the most appropriate category.
        Return ONLY the category name without explanation or additional text.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Categorize this content:\n\n{content}"}
        ]
        
        try:
            response = await self.chat(messages, model=model, temperature=0.3)
            
            # Clean up response to get just the category
            response = response.strip()
            if response in categories:
                category = response
            else:
                # If exact match not found, try to extract from response
                for cat in categories:
                    if cat.lower() in response.lower():
                        category = cat
                        break
                else:
                    # Default to first category if no match
                    category = categories[0]
                    
            return {
                "category": category,
                "success": True
            }
        except Exception as e:
            logger.error(f"Memory categorization error: {str(e)}")
            return {
                "category": categories[0],
                "success": False,
                "error": str(e)
            }
    
    async def summarize_memories(self, 
                               memories: List[str], 
                               model: Optional[str] = None) -> str:
        """
        Summarize a collection of memories.
        
        Args:
            memories: List of memory contents to summarize
            model: LLM model to use (defaults to configured default)
            
        Returns:
            Summarized text
        """
        if not memories:
            return ""
            
        combined_memories = "\n\n".join(memories)
        
        system_prompt = """
        You are an AI assistant tasked with summarizing multiple related memories.
        Create a concise summary that captures the key information across all provided memories.
        Focus on identifying patterns, core facts, and essential information.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Summarize these related memories:\n\n{combined_memories}"}
        ]
        
        try:
            return await self.chat(messages, model=model)
        except Exception as e:
            logger.error(f"Memory summarization error: {str(e)}")
            return f"Error summarizing memories: {str(e)}"
    
    def _get_fallback_response(self) -> str:
        """
        Provide a fallback response when the LLM service is unavailable.
        
        Returns:
            A helpful error message
        """
        return (
            "I apologize, but I'm currently unable to connect to the LLM service. "
            "This could be due to network issues or the service being offline. "
            "Basic memory operations will continue to work, but advanced analysis "
            "and generation capabilities may be limited. Please try again later or "
            "contact your administrator if the problem persists."
        )
    
    def get_available_models(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get the list of available models from the LLM adapter.
        
        Returns:
            Dictionary mapping providers to their available models
        """
        try:
            response = requests.get(f"{self.adapter_url}/v1/models")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get models: {response.status_code}, {response.text}")
                return {
                    "anthropic": [
                        {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
                        {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"}
                    ]
                }
        except requests.RequestException as e:
            logger.error(f"Error getting models: {str(e)}")
            return {
                "anthropic": [
                    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
                    {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"}
                ]
            }