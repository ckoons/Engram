#!/usr/bin/env python3
"""
Tests for the Structured Memory and Nexus Interface

These tests verify the core functionality of the Claude Memory Bridge
structured memory and memory-enabled AI assistant capabilities.
"""

import os
import json
import pytest
import tempfile
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import the memory services
from cmb.core.memory import MemoryService
from cmb.core.structured_memory import StructuredMemory
from cmb.core.nexus import NexusInterface

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def structured_memory(temp_data_dir):
    """Create a structured memory service instance for testing."""
    memory = StructuredMemory(client_id="test", data_dir=temp_data_dir)
    return memory

@pytest.fixture
def memory_service(temp_data_dir):
    """Create a legacy memory service instance for testing."""
    service = MemoryService(client_id="test", data_dir=temp_data_dir)
    return service

@pytest.fixture
def nexus_interface(memory_service, structured_memory):
    """Create a nexus interface for testing."""
    interface = NexusInterface(memory_service=memory_service, structured_memory=structured_memory)
    return interface

class TestStructuredMemory:
    """Test suite for the StructuredMemory class."""

    def test_init(self, structured_memory, temp_data_dir):
        """Test that the structured memory service initializes correctly."""
        assert structured_memory is not None
        assert structured_memory.client_id == "test"
        assert structured_memory.base_dir.exists()
        
        # Check that category directories were created
        for category in ["personal", "projects", "facts", "preferences", "session", "private"]:
            assert (structured_memory.base_dir / category).exists()
            assert (structured_memory.base_dir / category / "test").exists()
        
        # Check that metadata index was initialized
        assert structured_memory.metadata_index is not None
        assert "categories" in structured_memory.metadata_index
        assert "memory_count" in structured_memory.metadata_index
        assert "importance_counters" in structured_memory.metadata_index
        
    @pytest.mark.asyncio
    async def test_add_memory(self, structured_memory):
        """Test adding a memory."""
        # Add a memory
        memory_id = await structured_memory.add_memory(
            content="This is a test memory",
            category="projects",
            importance=4,
            metadata={"test_key": "test_value"},
            tags=["test", "memory"]
        )
        
        # Verify it was added
        assert memory_id is not None
        assert "projects" in memory_id
        
        # Check memory path exists
        memory_path = structured_memory._get_memory_path(memory_id, "projects")
        assert memory_path.exists()
        
        # Check metadata index was updated
        assert structured_memory.metadata_index["memory_count"] == 1
        assert structured_memory.metadata_index["importance_counters"]["4"] == 1
        assert memory_id in structured_memory.metadata_index["categories"]["projects"]["memories"]
        
        # Test getting the memory
        memory = await structured_memory.get_memory(memory_id)
        assert memory is not None
        assert memory["content"] == "This is a test memory"
        assert memory["category"] == "projects"
        assert memory["importance"] == 4
        assert memory["metadata"]["test_key"] == "test_value"
        assert "test" in memory["tags"]
        assert "memory" in memory["tags"]
    
    @pytest.mark.asyncio
    async def test_search_memories(self, structured_memory):
        """Test searching for memories."""
        # Add multiple memories with different categories and importance
        await structured_memory.add_memory(
            content="Important Python project information",
            category="projects",
            importance=5,
            tags=["python", "project"]
        )
        
        await structured_memory.add_memory(
            content="Less important Python note",
            category="facts",
            importance=2,
            tags=["python", "note"]
        )
        
        await structured_memory.add_memory(
            content="Personal preferences for Python coding",
            category="preferences",
            importance=4,
            tags=["python", "preference"]
        )
        
        # Search by query
        results = await structured_memory.search_memories(
            query="Python",
            min_importance=1,
            limit=10,
            sort_by="importance"
        )
        
        assert len(results) == 3
        assert results[0]["importance"] == 5  # Should be sorted by importance
        assert "project" in results[0]["content"]
        
        # Search by category
        project_results = await structured_memory.search_memories(
            categories=["projects"],
            min_importance=1
        )
        
        assert len(project_results) == 1
        assert project_results[0]["category"] == "projects"
        
        # Search by tags
        preference_results = await structured_memory.search_memories(
            tags=["preference"],
            min_importance=1
        )
        
        assert len(preference_results) == 1
        assert preference_results[0]["category"] == "preferences"
        
        # Search by minimum importance
        important_results = await structured_memory.search_memories(
            min_importance=4
        )
        
        assert len(important_results) == 2
        for result in important_results:
            assert result["importance"] >= 4
    
    @pytest.mark.asyncio
    async def test_auto_categorization(self, structured_memory):
        """Test automatic categorization of memories."""
        # Test with content that should be categorized as personal
        auto_cat, auto_imp, auto_tags = await structured_memory.auto_categorize_memory(
            "My name is Casey and I live in Seattle"
        )
        
        assert auto_cat == "personal"
        assert auto_imp == 5
        assert "personal-info" in auto_tags
        
        # Test with content that should be categorized as project
        # Note: we avoid using 'I'm' which would match personal patterns
        auto_cat, auto_imp, auto_tags = await structured_memory.auto_categorize_memory(
            "Working on a project to implement memory systems for AI"
        )
        
        assert auto_cat == "projects"
        assert auto_imp == 4
        assert "project" in auto_tags
        
        # Test with content that should be categorized as preferences
        auto_cat, auto_imp, auto_tags = await structured_memory.auto_categorize_memory(
            "I prefer using Python over JavaScript for most tasks"
        )
        
        assert auto_cat == "preferences"
        assert auto_imp == 4
        assert "preference" in auto_tags
        assert "coding" in auto_tags
    
    @pytest.mark.asyncio
    async def test_add_auto_categorized_memory(self, structured_memory):
        """Test adding a memory with automatic categorization."""
        # Add memory with auto categorization
        memory_id = await structured_memory.add_auto_categorized_memory(
            content="My name is Casey and I'm working on Claude Memory Bridge"
        )
        
        assert memory_id is not None
        
        # Get the memory to verify auto-categorization
        memory = await structured_memory.get_memory(memory_id)
        
        assert memory is not None
        assert memory["category"] == "personal"  # Should detect name as personal
        assert memory["importance"] == 5  # Personal info has high importance
        assert memory["metadata"]["auto_categorized"] is True
        
        # Test with manual override
        memory_id2 = await structured_memory.add_auto_categorized_memory(
            content="My name is Casey and I'm working on Claude Memory Bridge",
            manual_category="projects",
            manual_importance=3,
            manual_tags=["override-test"]
        )
        
        memory2 = await structured_memory.get_memory(memory_id2)
        assert memory2["category"] == "projects"  # Manual override
        assert memory2["importance"] == 3  # Manual override
        assert memory2["metadata"]["auto_categorized"] is False
        assert "override-test" in memory2["tags"]
    
    @pytest.mark.asyncio
    async def test_memory_importance(self, structured_memory):
        """Test updating memory importance."""
        # Add a memory
        memory_id = await structured_memory.add_memory(
            content="Test importance update",
            category="facts",
            importance=2
        )
        
        # Update importance
        result = await structured_memory.set_memory_importance(memory_id, 5)
        assert result is True
        
        # Verify update
        memory = await structured_memory.get_memory(memory_id)
        assert memory["importance"] == 5
        assert memory["metadata"]["importance_reason"] == "Manually updated importance"
        
        # Check metadata index update
        assert structured_memory.metadata_index["importance_counters"]["2"] == 0
        assert structured_memory.metadata_index["importance_counters"]["5"] == 1
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, structured_memory):
        """Test deleting a memory."""
        # Add a memory
        memory_id = await structured_memory.add_memory(
            content="This memory will be deleted",
            category="session",
            importance=3,
            tags=["temporary"]
        )
        
        # Verify it was added
        assert structured_memory.metadata_index["memory_count"] == 1
        
        # Delete the memory
        result = await structured_memory.delete_memory(memory_id)
        assert result is True
        
        # Verify it was deleted
        memory_path = structured_memory._get_memory_path(memory_id, "session")
        assert not memory_path.exists()
        
        # Check metadata index was updated
        assert structured_memory.metadata_index["memory_count"] == 0
        assert structured_memory.metadata_index["importance_counters"]["3"] == 0
        assert memory_id not in structured_memory.metadata_index["categories"]["session"]["memories"]
        assert "temporary" not in structured_memory.metadata_index["tags"] or memory_id not in structured_memory.metadata_index["tags"]["temporary"]
    
    @pytest.mark.asyncio
    async def test_memory_digest(self, structured_memory):
        """Test generating a memory digest."""
        # Add various memories
        await structured_memory.add_memory(
            content="Very important personal info",
            category="personal",
            importance=5
        )
        
        await structured_memory.add_memory(
            content="Important project milestone",
            category="projects",
            importance=4
        )
        
        await structured_memory.add_memory(
            content="Regular session note",
            category="session",
            importance=3
        )
        
        await structured_memory.add_memory(
            content="Private thought",
            category="private",
            importance=5
        )
        
        # Get digest without private memories
        digest = await structured_memory.get_memory_digest(include_private=False)
        assert "Memory Digest" in digest
        assert "Personal" in digest
        assert "Very important personal info" in digest
        assert "Projects" in digest
        assert "Important project milestone" in digest
        assert "Session" in digest
        assert "Regular session note" in digest
        assert "Private" not in digest
        assert "Private thought" not in digest
        
        # Get digest with private memories
        digest_with_private = await structured_memory.get_memory_digest(include_private=True)
        assert "Private" in digest_with_private
        assert "Private thought" in digest_with_private
    
    @pytest.mark.asyncio
    async def test_context_memories(self, structured_memory):
        """Test getting memories relevant to context."""
        # Add various memories
        await structured_memory.add_memory(
            content="Python is a programming language often used for AI applications",
            category="facts",
            importance=3
        )
        
        await structured_memory.add_memory(
            content="Claude Memory Bridge is a project for persistent memory across sessions",
            category="projects",
            importance=4
        )
        
        await structured_memory.add_memory(
            content="Structured Memory is better than simple key-value storage",
            category="preferences",
            importance=3
        )
        
        # Get memories relevant to a coding context
        context_memories = await structured_memory.get_context_memories(
            text="I'm working on a Python project for language models",
            max_memories=2
        )
        
        assert len(context_memories) <= 2  # May return fewer if relevance is low
        
        # Check if Python is mentioned in one of the results
        found_python = False
        for memory in context_memories:
            if "Python" in memory["content"]:
                found_python = True
                break
        
        assert found_python, "No Python-related memory found in context"


class TestNexusInterface:
    """Test suite for the NexusInterface class."""
    
    @pytest.mark.asyncio
    async def test_start_session(self, nexus_interface):
        """Test starting a session with memory digest."""
        # Initialize session
        result = await nexus_interface.start_session("Test Session")
        
        assert "Nexus Session Started" in result
        assert "Session: Test Session" in result
        assert "Memory Digest" in result
    
    @pytest.mark.asyncio
    async def test_process_message(self, nexus_interface, structured_memory):
        """Test processing a message through Nexus."""
        # Add some memories for context
        await structured_memory.add_memory(
            content="Casey enjoys hiking in the mountains",
            category="personal",
            importance=4
        )
        
        await structured_memory.add_memory(
            content="Casey is working on a memory bridge for Claude",
            category="projects",
            importance=5
        )
        
        # Process a user message
        context = await nexus_interface.process_message(
            message="Let's continue our discussion about Claude Memory Bridge",
            is_user=True
        )
        
        # Should have enhanced with relevant memory
        assert "Relevant Memory Context" in context
        assert "memory bridge" in context.lower()
        
        # Check that message was added to conversation history
        assert len(nexus_interface.conversation_history) == 1
        assert nexus_interface.conversation_history[0]["role"] == "user"
        
        # Process an assistant message
        assistant_result = await nexus_interface.process_message(
            message="I'll help you with the Claude Memory Bridge project",
            is_user=False
        )
        
        # Assistant messages should just be stored, not return context
        assert assistant_result == ""
        
        # Check that assistant message was added to conversation history
        assert len(nexus_interface.conversation_history) == 2
        assert nexus_interface.conversation_history[1]["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_store_memory(self, nexus_interface):
        """Test storing a memory with Nexus interface."""
        # Store a memory
        result = await nexus_interface.store_memory(
            content="This is an important test memory",
            category="facts",
            importance=4,
            tags=["test", "nexus"],
            metadata={"source": "test_suite"}
        )
        
        # Should have stored in both memory systems
        assert "structured_memory_id" in result
        assert "legacy_success" in result
        assert result["legacy_success"] is True
        
        # Verify in structured memory
        memory_id = result["structured_memory_id"]
        memory = await nexus_interface.structured_memory.get_memory(memory_id)
        
        assert memory is not None
        assert memory["content"] == "This is an important test memory"
        assert memory["category"] == "facts"
        assert memory["importance"] == 4
        assert "test" in memory["tags"]
        assert "nexus" in memory["tags"]
    
    @pytest.mark.asyncio
    async def test_forget_memory(self, nexus_interface, structured_memory):
        """Test marking information to be forgotten."""
        # Add a memory
        memory_id = await structured_memory.add_memory(
            content="This information should be forgotten",
            category="session",
            importance=3
        )
        
        # Verify it exists
        memory = await structured_memory.get_memory(memory_id)
        assert memory is not None
        
        # Forget it
        result = await nexus_interface.forget_memory("This information should be forgotten")
        assert result is True
        
        # Verify it was deleted from structured memory
        memory_after = await structured_memory.get_memory(memory_id)
        assert memory_after is None
        
        # Verify forget instruction was added to longterm
        search_result = await nexus_interface.memory_service.search(
            query="FORGET/IGNORE",
            namespace="longterm",
            limit=1
        )
        
        assert len(search_result["results"]) == 1
        assert "FORGET/IGNORE" in search_result["results"][0]["content"]
        assert "This information should be forgotten" in search_result["results"][0]["content"]
    
    @pytest.mark.asyncio
    async def test_search_memories(self, nexus_interface, structured_memory, memory_service):
        """Test searching for memories across memory systems."""
        # Add memories to both systems
        await structured_memory.add_memory(
            content="Structured memory about Python",
            category="facts",
            importance=3,
            tags=["python"]
        )
        
        await memory_service.add(
            content="Legacy memory about Python",
            namespace="conversations"
        )
        
        # Search memories
        results = await nexus_interface.search_memories(
            query="Python",
            categories=["facts"],
            min_importance=2,
            limit=10
        )
        
        # Should return results from both systems
        assert "structured" in results
        assert "legacy" in results
        assert "combined" in results
        
        assert len(results["structured"]) >= 1
        assert "Structured memory about Python" in results["structured"][0]["content"]
        
        assert len(results["combined"]) >= 1
        
        # At least one result should contain Python
        found_python = False
        for memory in results["combined"]:
            if "Python" in memory["content"]:
                found_python = True
                break
                
        assert found_python, "No Python-related memory found in combined results"
    
    @pytest.mark.asyncio
    async def test_end_session(self, nexus_interface):
        """Test ending a Nexus session."""
        # Start a session and add some conversation
        await nexus_interface.start_session("Test Session")
        
        await nexus_interface.process_message("Hello, this is a test message", is_user=True)
        await nexus_interface.process_message("Hello! I'm responding to your test", is_user=False)
        
        # End session with summary
        result = await nexus_interface.end_session("Successfully tested the Nexus interface")
        
        assert "Session ended" in result
        assert "Successfully tested" in result
        
        # Check that session end was recorded in both memory systems
        structured_search = await nexus_interface.structured_memory.search_memories(
            query="session ended",
            categories=["session"]
        )
        
        legacy_search = await nexus_interface.memory_service.search(
            query="session ended",
            namespace="session"
        )
        
        assert len(structured_search) >= 1
        assert len(legacy_search["results"]) >= 1


if __name__ == "__main__":
    pytest.main(["-xvs", "test_structured_memory.py"])