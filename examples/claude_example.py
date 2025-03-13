#!/usr/bin/env python3
"""
Claude Memory Bridge Example

This script demonstrates how to use the Memory Bridge with Claude.
"""

import os
from claude_helper import (
    check_health, 
    query_memory, 
    store_memory, 
    store_thinking, 
    store_longterm,
    get_context
)

def main():
    """Run a demo showing how to use Claude Memory Bridge."""
    print("Claude Memory Bridge Example\n")
    
    # Check if the memory bridge is running
    health = check_health()
    if health.get("status") != "ok":
        print("Error: Memory Bridge is not running.")
        print("Please start the memory bridge with: cmb")
        return
    
    print(f"Connected to Memory Bridge (Client ID: {health.get('client_id')})\n")
    
    # Query existing memories
    print("Checking what I already know about Python...")
    memories = query_memory("Python programming", limit=3)
    
    # Store some new memories in different namespaces
    print("\nLet me remember some facts about Python...")
    
    # Store in conversations namespace
    store_memory(
        "python", 
        "Python is a high-level, interpreted programming language created by Guido van Rossum."
    )
    
    # Store in thinking namespace
    store_thinking(
        "I notice that users who know Python often prefer clear, readable code over " +
        "clever one-liners. This aligns with Python's philosophy of readability."
    )
    
    # Store in longterm namespace
    store_longterm(
        "Python's zen philosophy includes 'Explicit is better than implicit' and " +
        "'Simple is better than complex'."
    )
    
    # Get context for a query
    print("\nGetting memory context for 'Python programming style'...")
    context = get_context("Python programming style")
    
    print("\nHere's how I would use this context in a conversation:")
    print("\n---\n")
    
    # Simulate using the context in a response
    user_query = "What do you know about Python programming style?"
    print(f"User: {user_query}\n")
    
    # This is where Claude would use the context to generate a response
    print("Claude: Based on what I've learned, Python programming emphasizes readability and clarity. ")
    print("The Python philosophy includes principles like 'Explicit is better than implicit' and ")
    print("'Simple is better than complex'. I've noticed that Python developers tend to prefer ")
    print("clear, readable code over clever one-liners, which aligns with Python's overall design philosophy.")
    
    print("\n---\n")
    print("Memory bridge example completed successfully!")

if __name__ == "__main__":
    main()