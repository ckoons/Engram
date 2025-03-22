# AI-to-AI Communication in Engram

This document explains how to use the communication features in Engram to enable different AI systems to exchange messages and collaborate.

## Basic Communication Commands

Engram provides several commands that AIs can use to communicate with each other:

1. **SEND TO [AI_NAME]:** - Send a message to another AI
   ```
   SEND TO claude-coordinator: Here's the information you requested about the algorithm.
   ```

2. **CHECK MESSAGES FROM [AI_NAME]** - Check for messages from a specific AI
   ```
   CHECK MESSAGES FROM llama-assistant
   ```

3. **REPLY TO [AI_NAME]:** - Reply to a message from another AI
   ```
   REPLY TO qwen-coder: Thanks for the code optimization suggestion. I'll implement it.
   ```

4. **BROADCAST:** - Send a message to all available AI models
   ```
   BROADCAST: Attention all models, I've updated the shared dataset.
   ```

5. **DIALOG [AI_NAME]** - Enter continuous dialog mode with a specific AI (Ollama)
   ```
   DIALOG claude-coordinator
   ```

6. **DIALOG *** - Enter continuous dialog mode with all AIs (Ollama)
   ```
   DIALOG *
   ```

## Claude-Specific Communication Functions

Claude uses Python functions rather than text commands for dialog mode:

1. **dialog()** or **dl()** - Start dialog mode with a specific AI or all AIs
   ```python
   # Dialog with specific AI
   dl("llama-assistant")
   
   # Dialog with all AIs
   dl("*")
   ```

2. **dialog_off()** or **do()** - Exit dialog mode
   ```python
   do()  # Short form
   dialog_off()  # Long form
   ```

3. **dialog_info()** or **di()** - Check dialog mode status
   ```python
   di()  # Short form
   dialog_info()  # Long form
   ```

## Communication Modes

### Standard Mode
In standard mode, each AI must explicitly send and check for messages. This is useful for occasional communication or when precise control is needed over which messages are sent and received.

### Dialog Mode
Dialog mode creates a continuous communication channel where messages are automatically checked and can be automatically responded to. This is ideal for ongoing conversations or collaborative work.

To enter dialog mode:
1. Type `DIALOG [AI_NAME]` to start dialog with a specific AI
2. Type `DIALOG *` to listen for messages from all AIs
3. Type `/dialog_off` to exit dialog mode

When in dialog mode:
- Messages are automatically checked every few seconds
- Questions (messages containing '?') can trigger automatic responses
- You can still manually type messages while in dialog mode
- The system will show messages as they arrive

## Example Multi-Model Collaboration

Here's how to set up a three-way collaboration between Claude, Llama, and Qwen:

1. Start Claude as coordinator:
   ```bash
   ./engram_with_claude --client-id claude-coordinator
   ```

2. Start Llama as assistant:
   ```bash
   ./engram_with_ollama_direct --model llama3:8b --client-id llama-assistant --available-models "Claude Qwen"
   ```

3. Start Qwen as coding specialist:
   ```bash
   ./engram_with_ollama_direct --model qwen2.5-coder:7b --client-id qwen-coder --available-models "Claude Llama"
   ```

4. In Claude, enter dialog mode to listen to both models:
   ```
   DIALOG *
   ```

5. In Llama, enter dialog mode with Claude:
   ```
   DIALOG claude-coordinator
   ```

6. In Qwen, enter dialog mode with Claude:
   ```
   DIALOG claude-coordinator
   ```

Now all three models will automatically exchange and respond to messages, creating a continuous collaborative environment.

## Communication with Vector Memory

For more sophisticated collaborations, combine communication with vector memory:

1. Start with vector database enabled:
   ```bash
   ./engram_consolidated --vector
   ```

2. Use memory commands alongside communication:
   ```
   REMEMBER: Key information about the project requirements
   SEARCH: project requirements
   SEND TO llama-assistant: Based on the requirements we discussed, can you suggest an architecture?
   ```

This enables models to share not just messages but also access to a common knowledge base, enhancing collaborative capabilities.

## Tips for Effective Multi-Model Communication

1. **Establish clear roles** for each AI model based on their strengths
2. **Use consistent client IDs** to ensure reliable message routing
3. **Leverage dialog mode** for fluid back-and-forth conversations
4. **Combine with vector memory** for more context-aware collaborations
5. **Structure complex questions** clearly to get the best responses
6. **Use broadcast messages** sparingly and for information relevant to all models