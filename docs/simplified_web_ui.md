# Simplified Web UI for Claude Memory Bridge

This document explains how to use the simplified web UI for environments where the full web UI might have dependency issues.

## Overview

The simplified web UI provides all the core functionality of the memory management interface without requiring complex dependencies like pandas and plotly. This makes it more compatible with various Python environments, including those with NumPy 2.x.

## Getting Started

### Prerequisites

- Python 3.6+
- Flask
- Virtual environment (recommended)

### Starting the Web UI

1. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install flask
   ```

3. **Make sure the memory bridge and HTTP wrapper are running**:
   ```bash
   ./cmb_start_all
   ```

4. **Start the simplified web UI**:
   ```bash
   python simple_web_ui.py
   ```

   Or to run in the background:
   ```bash
   nohup python simple_web_ui.py > web_ui.log 2>&1 &
   ```

5. **Access the web interface** at http://localhost:8002 (or the port you configured)

## Features

The simplified web UI provides all the core functionality of the memory management interface:

- Dashboard with memory statistics
- Memory browsing by namespace
- Compartment management
- Advanced search
- Memory details and actions
- Analytics (text-based alternatives to charts)

## Customization

You can customize the port by setting the `CMB_WEB_PORT` environment variable:

```bash
export CMB_WEB_PORT=8080
python simple_web_ui.py
```

## Troubleshooting

If you encounter issues:

1. **Check the logs**:
   ```bash
   cat web_ui.log
   ```

2. **Verify all services are running**:
   ```bash
   python test_web_access.py
   ```

3. **Common errors**:
   - Flask not installed: `pip install flask`
   - Port already in use: Change the port with `export CMB_WEB_PORT=8003`
   - Memory bridge not running: Start with `./cmb_start_all`

## Differences from Full Web UI

The simplified web UI differs from the full web UI in the following ways:

1. **No charts**: Uses text-based alternatives instead
2. **Fewer dependencies**: Only requires Flask, not pandas or plotly
3. **Simplified templates**: Uses direct CDN loading for Bootstrap
4. **Environment agnostic**: Works with various Python setups, including NumPy 2.x
5. **No flash messages**: Uses simpler redirects instead

## When to Use

Use the simplified web UI when:
- You encounter dependency issues with the full web UI
- You're using Python with NumPy 2.x
- You need a lightweight interface for memory management
- You value functionality over visual graphs and charts