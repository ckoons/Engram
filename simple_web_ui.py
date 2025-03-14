#!/usr/bin/env python
"""
Simplified Flask app for Claude Memory Bridge web UI
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import json
import urllib.parse
import urllib.request
from datetime import datetime

app = Flask(__name__, 
    template_folder=os.path.join('cmb', 'web', 'templates'),
    static_folder=os.path.join('cmb', 'web', 'static')
)
app.config['SECRET_KEY'] = 'dev-key-for-development-only'

# Default HTTP URL for the Claude Memory Bridge wrapper
DEFAULT_HTTP_URL = "http://127.0.0.1:8001"

def get_http_url():
    """Get the HTTP URL for the Claude Memory Bridge wrapper."""
    return os.environ.get("CMB_HTTP_URL", DEFAULT_HTTP_URL)

def safe_string(text):
    """URL-encode a string to make it safe for GET requests."""
    return urllib.parse.quote_plus(str(text))

def query_http_api(endpoint, params=None):
    """Query the HTTP API wrapper."""
    base_url = get_http_url()
    url = f"{base_url}/{endpoint}"
    
    if params:
        param_strings = []
        for key, value in params.items():
            if isinstance(value, dict) or isinstance(value, list):
                param_strings.append(f"{key}={safe_string(json.dumps(value))}")
            else:
                param_strings.append(f"{key}={safe_string(value)}")
        
        url = f"{url}?{'&'.join(param_strings)}"
    
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error querying API: {e}")
        return {"success": False, "error": str(e)}

@app.route('/')
def index():
    """Main dashboard page."""
    # Get memory stats
    stats = {
        "total_memories": 0,
        "by_namespace": {},
        "recent_activity": []
    }
    
    # Query health to check if service is running
    health = query_http_api("health")
    
    # Get memory counts by namespace
    for namespace in ["conversations", "thinking", "longterm", "session"]:
        result = query_http_api("query", {"query": "", "namespace": namespace, "limit": 1})
        count = result.get("count", 0)
        stats["total_memories"] += count
        stats["by_namespace"][namespace] = count
        
    # Get compartments
    compartments = query_http_api("compartment/list")
    
    # Get recent memories (across all namespaces)
    recent_memories = []
    for namespace in ["conversations", "thinking", "longterm", "session"]:
        result = query_http_api("query", {"query": "", "namespace": namespace, "limit": 5})
        for memory in result.get("results", []):
            memory["namespace"] = namespace
            recent_memories.append(memory)
    
    # Sort by timestamp (most recent first)
    recent_memories = sorted(recent_memories, key=lambda x: x.get("timestamp", 0), reverse=True)[:10]
    
    # Format timestamps
    for memory in recent_memories:
        ts = memory.get("timestamp", 0)
        if ts:
            memory["formatted_time"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        else:
            memory["formatted_time"] = "Unknown"
    
    # Dummy chart for display
    chart_json = json.dumps({"data": [], "layout": {"title": "Charts disabled"}})
    
    return render_template(
        'index.html',
        stats=stats,
        recent_memories=recent_memories,
        compartments=compartments.get("compartments", []),
        chart_json=chart_json,
        service_status=health.get("status", "unknown")
    )

@app.route('/memories')
def memories():
    """Browse all memories."""
    namespace = request.args.get('namespace', 'conversations')
    query = request.args.get('query', '')
    limit = int(request.args.get('limit', 100))
    
    result = query_http_api("query", {"query": query, "namespace": namespace, "limit": limit})
    
    memories = result.get("results", [])
    
    # Format timestamps
    for memory in memories:
        ts = memory.get("timestamp", 0)
        if ts:
            memory["formatted_time"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        else:
            memory["formatted_time"] = "Unknown"
    
    return render_template(
        'memories.html',
        memories=memories,
        namespace=namespace,
        query=query,
        limit=limit,
        count=result.get("count", 0)
    )

@app.route('/search')
def search():
    """Advanced search page."""
    query = request.args.get('query', '')
    namespaces = request.args.getlist('namespaces') or ["conversations", "thinking", "longterm", "session"]
    limit = int(request.args.get('limit', 100))
    
    results = []
    for namespace in namespaces:
        result = query_http_api("query", {"query": query, "namespace": namespace, "limit": limit})
        for memory in result.get("results", []):
            memory["namespace"] = namespace
            ts = memory.get("timestamp", 0)
            if ts:
                memory["formatted_time"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            else:
                memory["formatted_time"] = "Unknown"
            results.append(memory)
    
    # Sort by relevance if query provided, otherwise by timestamp
    if query:
        results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    else:
        results = sorted(results, key=lambda x: x.get("timestamp", 0), reverse=True)
    
    return render_template(
        'search.html',
        query=query,
        namespaces=namespaces,
        results=results,
        limit=limit,
        count=len(results)
    )

@app.route('/compartments')
def compartments():
    """Browse and manage memory compartments."""
    result = query_http_api("compartment/list")
    compartments = result.get("compartments", [])
    
    return render_template(
        'compartments.html',
        compartments=compartments
    )

@app.route('/compartment/<compartment_id>')
def compartment_details(compartment_id):
    """View details of a specific compartment."""
    # First, get all compartments to find the matching one
    result = query_http_api("compartment/list")
    compartments = result.get("compartments", [])
    
    compartment = None
    for c in compartments:
        if c.get("id") == compartment_id or c.get("name") == compartment_id:
            compartment = c
            break
    
    if not compartment:
        # Flash message not available in simplified version
        return redirect(url_for('compartments'))
    
    # Query memories in this compartment
    memory_result = query_http_api("query", {"query": "", "namespace": f"compartment:{compartment_id}", "limit": 100})
    memories = memory_result.get("results", [])
    
    # Format timestamps
    for memory in memories:
        ts = memory.get("timestamp", 0)
        if ts:
            memory["formatted_time"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        else:
            memory["formatted_time"] = "Unknown"
    
    return render_template(
        'compartment_details.html',
        compartment=compartment,
        memories=memories,
        count=memory_result.get("count", 0)
    )

@app.route('/memory/<memory_id>')
def memory_details(memory_id):
    """View details of a specific memory."""
    # We need to search across all namespaces to find this memory
    memory = None
    for namespace in ["conversations", "thinking", "longterm", "session"]:
        # This is inefficient but we don't have a direct memory lookup endpoint
        result = query_http_api("query", {"query": "", "namespace": namespace, "limit": 1000})
        
        for m in result.get("results", []):
            if m.get("id") == memory_id:
                memory = m
                memory["namespace"] = namespace
                break
        
        if memory:
            break
    
    if not memory:
        # Flash message not available in simplified version
        return redirect(url_for('memories'))
    
    # Format timestamp
    ts = memory.get("timestamp", 0)
    if ts:
        memory["formatted_time"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    else:
        memory["formatted_time"] = "Unknown"
    
    # Check if memory has expiration
    expires_at = memory.get("expires_at", 0)
    if expires_at:
        memory["expires_formatted"] = datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S")
        memory["days_remaining"] = (datetime.fromtimestamp(expires_at) - datetime.now()).days
    
    return render_template(
        'memory_details.html',
        memory=memory
    )

@app.route('/analytics')
def analytics():
    """Memory analytics and visualization page."""
    # Get counts by namespace
    namespace_counts = {}
    for namespace in ["conversations", "thinking", "longterm", "session"]:
        result = query_http_api("query", {"query": "", "namespace": namespace, "limit": 1})
        namespace_counts[namespace] = result.get("count", 0)
    
    # Get compartment counts
    result = query_http_api("compartment/list")
    compartments = result.get("compartments", [])
    compartment_counts = {}
    
    for c in compartments:
        memory_result = query_http_api("query", {"query": "", "namespace": f"compartment:{c.get('id')}", "limit": 1})
        compartment_counts[c.get("name")] = memory_result.get("count", 0)
    
    # Create dummy charts (instead of using pandas/plotly)
    dummy_chart = json.dumps({"data": [], "layout": {"title": "Charts disabled due to NumPy 2.x compatibility issue"}})
    
    return render_template(
        'analytics.html',
        namespace_chart=dummy_chart,
        compartment_chart=dummy_chart,
        growth_chart=dummy_chart,
        namespace_counts=namespace_counts,
        compartment_counts=compartment_counts
    )

# API endpoints for AJAX operations
@app.route('/api/toggle_compartment/<compartment_id>', methods=['POST'])
def toggle_compartment(compartment_id):
    """Activate or deactivate a compartment."""
    data = request.get_json() or {}
    action = data.get('action')
    
    if action == 'activate':
        result = query_http_api("compartment/activate", {"compartment": compartment_id})
    elif action == 'deactivate':
        result = query_http_api("compartment/deactivate", {"compartment": compartment_id})
    else:
        return jsonify({"success": False, "error": "Invalid action"})
    
    return jsonify(result)

@app.route('/api/forget_memory/<memory_id>', methods=['POST'])
def forget_memory(memory_id):
    """Mark a memory to be forgotten."""
    data = request.get_json() or {}
    memory_content = data.get('content', '')
    
    # Use the forget endpoint (via store with special namespace)
    forget_instruction = f"FORGET/IGNORE: {memory_content}"
    result = query_http_api("store", {
        "key": "forget", 
        "value": forget_instruction,
        "namespace": "longterm"
    })
    
    return jsonify(result)

@app.route('/api/keep_memory/<memory_id>', methods=['POST'])
def keep_memory(memory_id):
    """Set a memory's expiration date."""
    data = request.get_json() or {}
    days = int(data.get('days', 30))
    
    result = query_http_api("keep", {"memory_id": memory_id, "days": days})
    
    return jsonify(result)

@app.route('/api/compartment/create', methods=['POST'])
def create_compartment():
    """Create a new compartment."""
    data = request.get_json() or {}
    name = data.get('name')
    
    if not name:
        return jsonify({"success": False, "error": "Compartment name is required"})
    
    result = query_http_api("compartment/create", {"name": name})
    return jsonify(result)

@app.route('/api/compartment/store', methods=['POST'])
def store_in_compartment():
    """Store content in a compartment."""
    data = request.get_json() or {}
    compartment = data.get('compartment')
    content = data.get('content')
    
    if not compartment:
        return jsonify({"success": False, "error": "Compartment ID is required"})
    
    if not content:
        return jsonify({"success": False, "error": "Content is required"})
    
    result = query_http_api("compartment/store", {"compartment": compartment, "content": content})
    return jsonify(result)

if __name__ == '__main__':
    host = os.environ.get('CMB_WEB_HOST', '127.0.0.1')
    port = int(os.environ.get('CMB_WEB_PORT', 8003))
    debug = os.environ.get('CMB_WEB_DEBUG', 'true').lower() == 'true'
    
    print(f"Starting simplified Memory Bridge Web UI on {host}:{port}")
    app.run(host=host, port=port, debug=debug)