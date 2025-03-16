# Engram Configuration Guide

Engram provides a flexible configuration system that allows you to customize its behavior to suit your needs. This guide explains how to use the configuration system effectively.

## Configuration Methods

Engram settings can be configured in three ways, in order of precedence:

1. **Environment Variables**: For quick temporary changes
2. **Configuration File**: For persistent settings
3. **Default Values**: Applied if not overridden

## Configuration File

The default configuration file is located at `~/.engram/config.json`. This JSON file contains all configurable settings with their values.

### Example Configuration

```json
{
  "client_id": "claude",
  "data_dir": "/Users/username/.engram",
  "host": "127.0.0.1",
  "port": 8000,
  "auto_agency": true,
  "debug": false,
  "default_importance": 3,
  "max_memories_per_request": 10,
  "memory_expiration_days": 90,
  "vector_search_enabled": true
}
```

## Configuration Utility

Engram provides a command-line utility to manage your configuration:

```bash
./engram_config
```

This utility provides several options:

- **Interactive Mode**: Guided setup of all settings
- **Show Current Config**: Display all current settings
- **Edit Config**: Open the config file in your text editor
- **Reset Config**: Restore defaults

### Interactive Configuration

The default mode is interactive configuration, which walks you through all available settings:

```bash
./engram_config --interactive
```

This will prompt you for each setting with the current default in brackets.

### Viewing Configuration

To view your current configuration:

```bash
./engram_config --show
```

### Editing Configuration

To edit the configuration manually:

```bash
./engram_config --edit
```

This opens the configuration file in your default text editor (set by the `EDITOR` environment variable).

### Resetting Configuration

To reset all settings to their defaults:

```bash
./engram_config --reset
```

## Environment Variables

All settings can be overridden with environment variables using the format:

```
ENGRAM_UPPERCASE_SETTING=value
```

For example:

```bash
# Set port to 9000 and enable debug mode
export ENGRAM_PORT=9000
export ENGRAM_DEBUG=true

# Then run Engram
./engram_consolidated
```

## Available Settings

### Core Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `client_id` | string | "claude" | Identifier for memory storage |
| `data_dir` | string | "~/.engram" | Directory to store memory data |

### Server Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `host` | string | "127.0.0.1" | Host address to bind server |
| `port` | integer | 8000 | Port number for server |

### Feature Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `auto_agency` | boolean | true | Automatically activate agency for all user messages |
| `debug` | boolean | false | Enable debug logging and verbose output |

### Memory Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `default_importance` | integer | 3 | Default importance level (1-5) for memories |
| `max_memories_per_request` | integer | 10 | Maximum memories to return per request |

### Advanced Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `memory_expiration_days` | integer | 90 | Default expiration for memories in days |
| `vector_search_enabled` | boolean | true | Enable vector-based semantic search |

## Programmatic Usage

In your Python code, you can access the configuration as follows:

```python
from engram.core.config import get_config

# Get the global configuration
config = get_config()

# Access a setting
port = config["port"]

# Update a setting
config["debug"] = True

# Save changes
config.save()
```

## Best Practices

1. **Use configuration files** for persistent settings that you want to keep across sessions
2. **Use environment variables** for temporary changes or in deployment scripts
3. **Keep security-sensitive settings** like API keys in environment variables, not in config files
4. **Version control** your config files with sensitive information removed