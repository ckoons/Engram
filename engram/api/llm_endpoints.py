#!/usr/bin/env python3
"""
LLM API Endpoints for Engram

This module implements FastAPI endpoints for interacting with LLMs
through the Engram system, leveraging the LLM adapter.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("engram.api.llm_endpoints")

# Import Engram modules
from engram.core.llm_adapter import LLMAdapter
from engram.core.memory_manager import MemoryManager
from engram.api.dependencies import get_memory_manager

# Models for request/response
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    system: Optional[str] = None
    persist_memory: Optional[bool] = True
    memory_namespace: Optional[str] = "conversations"

class ChatResponse(BaseModel):
    content: str
    model: str

class LLMAnalysisRequest(BaseModel):
    content: str
    context: Optional[str] = None
    model: Optional[str] = None

class LLMAnalysisResponse(BaseModel):
    analysis: str
    success: bool
    error: Optional[str] = None

# Create router
router = APIRouter(
    prefix="/v1/llm",
    tags=["LLM"],
)

# Dependency to get LLM adapter
async def get_llm_adapter():
    return LLMAdapter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm_adapter: LLMAdapter = Depends(get_llm_adapter),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Send a chat request to the LLM and get a response.
    """
    # Format messages for the LLM adapter
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    # Get chat response
    try:
        response = await llm_adapter.chat(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=request.system
        )
        
        # Store in memory if requested
        if request.persist_memory:
            # Create formatted conversation for memory
            conversation = "\n\n".join([
                f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
                for msg in request.messages
            ])
            conversation += f"\n\nAssistant: {response}"
            
            # Get memory service
            memory_service = await memory_manager.get_memory_service(None)
            
            # Store in memory
            await memory_service.add(
                content=conversation,
                namespace=request.memory_namespace,
                metadata={
                    "type": "conversation",
                    "model": request.model or llm_adapter.default_model
                }
            )
        
        return {
            "content": response,
            "model": request.model or llm_adapter.default_model
        }
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    llm_adapter: LLMAdapter = Depends(get_llm_adapter),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Stream a chat response from the LLM.
    """
    if not request.stream:
        # If stream is False, redirect to regular chat endpoint
        return await chat(request, llm_adapter, memory_manager)
    
    # Format messages for the LLM adapter
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    # Create streaming response
    async def generate():
        full_response = ""
        async for chunk in llm_adapter._stream_chat(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=request.system
        ):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        # Store in memory if requested
        if request.persist_memory:
            # Create formatted conversation for memory
            conversation = "\n\n".join([
                f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
                for msg in request.messages
            ])
            conversation += f"\n\nAssistant: {full_response}"
            
            # Get memory service
            memory_service = await memory_manager.get_memory_service(None)
            
            # Store in memory asynchronously (don't wait for completion)
            asyncio.create_task(memory_service.add(
                content=conversation,
                namespace=request.memory_namespace,
                metadata={
                    "type": "conversation",
                    "model": request.model or llm_adapter.default_model
                }
            ))
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

@router.websocket("/chat/ws")
async def websocket_chat(
    websocket: WebSocket,
    llm_adapter: LLMAdapter = Depends(get_llm_adapter),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    WebSocket endpoint for interactive chat sessions.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Extract request parameters
            messages = data.get("messages", [])
            model = data.get("model")
            temperature = data.get("temperature", 0.7)
            max_tokens = data.get("max_tokens")
            stream = data.get("stream", False)
            system = data.get("system")
            persist_memory = data.get("persist_memory", True)
            memory_namespace = data.get("memory_namespace", "conversations")
            
            if stream:
                # Streaming response
                full_response = ""
                async for chunk in llm_adapter._stream_chat(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system
                ):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })
                
                # Send completion message
                await websocket.send_json({
                    "type": "done",
                    "model": model or llm_adapter.default_model
                })
                
                # Store in memory if requested
                if persist_memory:
                    # Create formatted conversation for memory
                    conversation = "\n\n".join([
                        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                        for msg in messages
                    ])
                    conversation += f"\n\nAssistant: {full_response}"
                    
                    # Get memory service
                    memory_service = await memory_manager.get_memory_service(None)
                    
                    # Store in memory asynchronously
                    asyncio.create_task(memory_service.add(
                        content=conversation,
                        namespace=memory_namespace,
                        metadata={
                            "type": "conversation",
                            "model": model or llm_adapter.default_model
                        }
                    ))
            else:
                # Non-streaming response
                response = await llm_adapter.chat(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system
                )
                
                # Send complete response
                await websocket.send_json({
                    "type": "message",
                    "content": response,
                    "model": model or llm_adapter.default_model
                })
                
                # Store in memory if requested
                if persist_memory:
                    # Create formatted conversation for memory
                    conversation = "\n\n".join([
                        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                        for msg in messages
                    ])
                    conversation += f"\n\nAssistant: {response}"
                    
                    # Get memory service
                    memory_service = await memory_manager.get_memory_service(None)
                    
                    # Store in memory asynchronously
                    asyncio.create_task(memory_service.add(
                        content=conversation,
                        namespace=memory_namespace,
                        metadata={
                            "type": "conversation",
                            "model": model or llm_adapter.default_model
                        }
                    ))
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })

@router.post("/analyze", response_model=LLMAnalysisResponse)
async def analyze_content(
    request: LLMAnalysisRequest,
    llm_adapter: LLMAdapter = Depends(get_llm_adapter)
):
    """
    Analyze content using the LLM.
    """
    try:
        result = await llm_adapter.analyze_memory(
            content=request.content,
            context=request.context,
            model=request.model
        )
        return result
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return {
            "analysis": "",
            "success": False,
            "error": str(e)
        }

@router.get("/models")
async def get_models(
    llm_adapter: LLMAdapter = Depends(get_llm_adapter)
):
    """
    Get available LLM models.
    """
    try:
        models = llm_adapter.get_available_models()
        return models
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))