# Memory Visualization in Claude Memory Bridge

The Memory Visualization feature provides a web-based interface for browsing, managing, and analyzing memories in the Claude Memory Bridge.

## Overview

The Memory Visualization dashboard offers a comprehensive view of Claude's memories, allowing you to:

- Browse memories across all namespaces
- Search for specific memories with advanced filtering
- Manage compartments and their content
- View analytics on memory distribution
- Control memory expiration
- Mark memories for forgetting
- Add new memories to compartments

## Getting Started

### Starting the Web UI

You can start all services (memory bridge, HTTP wrapper, and web UI) at once with:

#### Foreground Mode (Interactive)

This mode runs the web UI in the foreground, showing logs directly in the terminal:

```bash
# Start all services with web UI in foreground
./cmb_start_web

# Start with custom host and port
./cmb_start_web --host 0.0.0.0 --port 8080

# Start in debug mode
./cmb_start_web --debug
```

#### Background Mode (Non-Interactive)

This mode runs all services in the background, letting you continue using the terminal:

```bash
# Start all services in background
./cmb_start_web_bg

# Start with custom host and port
./cmb_start_web_bg --host 0.0.0.0 --port 8080

# Start in debug mode
./cmb_start_web_bg --debug

# Stop all background services when done
./cmb_stop_web
```

#### Starting Services Individually

You can also start services individually if needed:

```bash
# Start the memory services
./cmb_start_all

# Then start the web UI separately
./cmb_web

# Start with custom settings
./cmb_web --host 0.0.0.0 --port 8080 --debug
```

Once started, access the web UI at: http://localhost:8002 (or your custom host/port)

## Key Features

### Dashboard

The dashboard provides an overview of your memory system, including:

- Memory counts by namespace
- Distribution chart
- Recent memories
- Active compartments
- Service status

![Dashboard](../docs/images/dashboard.png)

### Memory Browser

The Memory Browser allows you to browse and search memories within a specific namespace:

- Filter by namespace (conversations, thinking, longterm, session)
- Search by keyword
- Control the number of results shown
- View memory details
- Mark memories for forgetting

### Compartment Management

The Compartment Management section provides tools for organizing memories:

- Create new compartments
- Activate/deactivate compartments
- View compartment hierarchies
- Store new memories in compartments
- Browse memories within compartments

### Memory Details

The Memory Details page shows comprehensive information about a single memory:

- Full content
- Metadata (creation date, namespace, etc.)
- Expiration information
- Controls for setting expiration or marking for forgetting

### Advanced Search

The Advanced Search page allows cross-namespace searching with multiple filters:

- Search across multiple namespaces simultaneously
- Filter by relevance or timestamp
- View detailed search results

### Analytics

The Analytics page provides visual insights into your memory system:

- Distribution of memories by namespace
- Distribution by compartment
- Memory growth over time
- Detailed statistics

## Usage Examples

### Creating and Managing Compartments

1. Navigate to the Compartments page
2. Click "New Compartment"
3. Enter a name (use dot notation for hierarchical compartments, e.g., "Project.Backend")
4. Optionally add initial content
5. Click "Create"

To activate or deactivate a compartment, use the toggle buttons on the compartment list.

### Searching Memories

1. Use the search bar at the top of any page for quick searches
2. For advanced searches, navigate to the Advanced Search page
3. Select which namespaces to search in
4. Enter your search query
5. Click "Search"

### Setting Memory Expiration

1. Navigate to the memory details page for a specific memory
2. Click "Set Expiration"
3. Choose the desired retention period (7 days, 30 days, 90 days, etc.)
4. Click "Save"

### Marking Memories for Forgetting

1. Find the memory in any of the memory lists
2. Click the trash icon
3. Confirm the operation
4. The memory will be marked for forgetting and filtered out of future retrievals

## Technical Implementation

The Memory Visualization web UI is built with:

- Flask for the web framework
- Bootstrap for the UI components
- Plotly for data visualization
- jQuery for interactive elements

The web UI communicates with the Claude Memory Bridge through the HTTP wrapper API, making it easy to integrate with the existing memory system.

## Troubleshooting

- If the web UI cannot connect to the memory bridge, check that the HTTP wrapper is running on the expected port (default: 8001)
- If charts or visualizations don't load, ensure you have the required dependencies installed (`plotly`, `pandas`)
- If you encounter errors when managing compartments, check the memory bridge logs for more detailed error messages

## Security Considerations

The Memory Visualization web UI is intended for local use and does not include authentication by default. If deploying in a shared environment:

- Consider running behind a reverse proxy with authentication
- Limit access to trusted networks
- Do not expose the interface to the public internet without proper security measures

## Testing the Web UI

To verify that the Memory Visualization is working properly:

1. **Start all services with one command**:
   ```bash
   # Start all services (memory bridge, HTTP wrapper, and web UI)
   ./cmb_start_web
   ```
   
   Or start each service separately in different terminals:
   ```bash
   # Terminal 1: Start the memory bridge
   ./cmb
   
   # Terminal 2: Start the HTTP wrapper
   ./cmb_http
   
   # Terminal 3: Start the web UI
   ./cmb_web
   ```

2. **Access the web interface** by opening a browser and navigating to:
   ```
   http://localhost:8002
   ```

3. **Test key functionality**:
   - Check that the dashboard loads with memory statistics
   - Navigate to the Memories section and verify you can browse memories
   - Test creating a new compartment in the Compartments section
   - Try the search functionality
   - View the analytics page to check that charts render properly

### Troubleshooting

If you encounter errors when working with the web UI, check the following:

- If the web UI cannot connect to the memory bridge, check that the HTTP wrapper is running on the expected port (default: 8001)
- If charts or visualizations don't load, ensure you have the required dependencies installed (`plotly`, `pandas`)
- If you encounter errors when managing compartments, check the memory bridge logs for more detailed error messages
- Check the terminal where you started the web UI for any error messages or stack traces

#### Common Dependency Issues

##### NumPy 2.x Compatibility Issue

If you're using NumPy 2.x, you may encounter errors when running the web UI:

```
A module that was compiled using NumPy 1.x cannot be run in
NumPy 2.2.1 as it may crash...
```

In this case, you have two options:

1. **Simplified Web UI (Recommended for NumPy 2.x)**:
   Use our simplified web UI that doesn't depend on NumPy:
   ```bash
   python simple_web_ui.py
   ```
   See [Simplified Web UI](simplified_web_ui.md) for details.

2. **Downgrade NumPy** to version 1.x:
   ```bash
   pip install numpy==1.26.0
   ```

##### Missing Packages

If you encounter ModuleNotFoundError for any of these packages, install them manually:

```bash
# Install basic dependencies
pip install flask flask-wtf bootstrap-flask

# Install visualization dependencies (only if NumPy 1.x is used)
pip install pandas plotly

# If bootstrap-flask installation fails, try the alternative
pip install flask-bootstrap
```

The web UI has been designed to gracefully handle missing dependencies where possible. Basic functionality will work even if some packages are missing.