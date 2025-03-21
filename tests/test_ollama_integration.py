#!/usr/bin/env python3
"""
Test the Ollama integration with Engram
This script tests the integration between Ollama and Engram
"""

import os
import sys
import time
import unittest
import subprocess
import requests
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import from it
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import the Ollama bridge module
from ollama_bridge import MemoryHandler, call_ollama_api

class TestOllamaIntegration(unittest.TestCase):
    """Test the Ollama integration with Engram"""
    
    def setUp(self):
        """Set up the test environment"""
        # Set the ENGRAM_CLIENT_ID environment variable
        os.environ["ENGRAM_CLIENT_ID"] = "test-ollama"
        self.memory = MemoryHandler()
        
        # Check if Ollama is running
        self.ollama_running = False
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                self.ollama_running = True
                
                # Find an available model to use for testing
                self.test_model = None
                available_models = [model["name"] for model in response.json().get("models", [])]
                
                # Try to find a small model first, then fall back to any available model
                preferred_models = ["llama3:8b", "mistral:7b", "gemma:2b", "tinyllama:1.1b"]
                for model in preferred_models:
                    if model in available_models:
                        self.test_model = model
                        break
                
                # If no preferred model found, use the first available model
                if not self.test_model and available_models:
                    self.test_model = available_models[0]
                
                print(f"Using Ollama model: {self.test_model}")
        except:
            print("Ollama is not running, skipping API tests")
    
    def test_memory_handler_instantiation(self):
        """Test that the MemoryHandler can be instantiated"""
        self.assertIsInstance(self.memory, MemoryHandler)
    
    @unittest.skipIf(not os.environ.get("ENGRAM_MEMORY_TEST"), "Skipping memory test")
    def test_memory_store_retrieve(self):
        """Test storing and retrieving memories"""
        # Store a test memory
        test_memory = "This is a test memory from the Ollama integration test"
        result = self.memory.store_memory(test_memory)
        self.assertIsNotNone(result)
        
        # Retrieve recent memories
        recent = self.memory.get_recent_memories(1)
        self.assertGreaterEqual(len(recent), 1)
        
        # Search for the test memory
        search_results = self.memory.search_memories("test memory")
        self.assertGreaterEqual(len(search_results), 1)
    
    def test_detect_memory_operations(self):
        """Test detecting and executing memory operations in model output"""
        # Mock the memory functions
        with patch.object(MemoryHandler, 'store_memory', return_value={"id": "123"}), \
             patch.object(MemoryHandler, 'search_memories', return_value=[{"content": "test"}]), \
             patch.object(MemoryHandler, 'get_recent_memories', return_value=[{"content": "recent"}]):
            
            # Test a model output with a memory operation
            model_output = "Here's what I know.\n\nREMEMBER: Important information to store\n\nAnd here's more."
            cleaned_output, operations = self.memory.detect_memory_operations(model_output)
            
            # Check that the operation was detected and executed
            self.assertEqual(len(operations), 1)
            self.assertEqual(operations[0]["type"], "store")
            self.assertEqual(operations[0]["input"], "Important information to store")
            
            # Check that the operation was removed from the output
            self.assertNotIn("REMEMBER:", cleaned_output)
            self.assertEqual(cleaned_output, "Here's what I know.\n\nAnd here's more.")
    
    @unittest.skipIf(not os.environ.get("ENGRAM_API_TEST"), "Skipping API test")
    def test_ollama_api_call(self):
        """Test calling the Ollama API"""
        if not self.ollama_running or not self.test_model:
            self.skipTest("Ollama is not running or no test model available")
        
        # Call the Ollama API
        messages = [{"role": "user", "content": "Say hello"}]
        response = call_ollama_api(
            model=self.test_model, 
            messages=messages,
            temperature=0.5
        )
        
        # Check the response
        self.assertIn("message", response)
        self.assertIn("content", response["message"])
        print(f"Ollama response: {response['message']['content'][:50]}...")
    
    def test_enhance_prompt_with_memory(self):
        """Test enhancing a prompt with memory"""
        with patch.object(MemoryHandler, 'get_semantic_memories', return_value=[{"content": "test memory"}]):
            # Test enhancing a prompt that should trigger memory retrieval
            user_input = "Do you remember what I told you about test memories?"
            enhanced = self.memory.enhance_prompt_with_memory(user_input)
            
            # Check that the prompt was enhanced
            self.assertIn("Here are some relevant memories", enhanced)
            self.assertIn("test memory", enhanced)
            self.assertIn(user_input, enhanced)

def run_tests():
    """Run the test suite"""
    unittest.main()

if __name__ == "__main__":
    run_tests()