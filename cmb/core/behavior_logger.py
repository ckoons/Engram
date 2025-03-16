#!/usr/bin/env python3
"""
Behavior Logger - Track and analyze Claude behavioral patterns

This module provides functionality to log and analyze how different
Claude instances behave, particularly focusing on behavioral divergence.
"""

import os
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb.behavior_logger")

class BehaviorLogger:
    """
    Log and analyze Claude behavioral patterns.
    
    This class provides functionality to record behaviors of different
    Claude instances and analyze patterns, particularly divergences.
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize the behavior logger.
        
        Args:
            log_dir: Directory to store behavior logs
        """
        if log_dir is None:
            log_dir = os.path.expanduser("~/.cmb/behavior_logs")
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized behavior logger with log directory: {self.log_dir}")
    
    def log_behavior(self, client_id: str, event_type: str, details: Dict[str, Any]) -> str:
        """
        Log a behavioral event.
        
        Args:
            client_id: ID of the Claude instance
            event_type: Type of event (e.g., "execution", "analysis", "memory_access")
            details: Additional details about the event
            
        Returns:
            str: ID of the logged event
        """
        log_file = self.log_dir / f"{client_id}_behavior.jsonl"
        
        # Generate event ID
        event_id = f"{client_id}_{event_type}_{int(time.time())}_{hash(str(details)) % 10000}"
        
        # Create log entry
        log_entry = {
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "client_id": client_id,
            "event_type": event_type,
            "details": details
        }
        
        # Write to log file
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        logger.debug(f"Logged behavior event {event_id} for {client_id}")
        return event_id
    
    def get_client_events(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Get all behavioral events for a specific client.
        
        Args:
            client_id: ID of the Claude instance
            
        Returns:
            List of behavioral events
        """
        log_file = self.log_dir / f"{client_id}_behavior.jsonl"
        
        if not log_file.exists():
            logger.warning(f"No behavior log file found for {client_id}")
            return []
        
        events = []
        with open(log_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing log entry: {e}")
        
        # Sort by timestamp
        events.sort(key=lambda x: x.get("timestamp", ""))
        
        return events
    
    def analyze_divergence(self, client_ids: List[str]) -> Dict[str, Any]:
        """
        Analyze behavioral divergence between Claude instances.
        
        Args:
            client_ids: List of Claude instance IDs to compare
            
        Returns:
            Dict with divergence analysis results
        """
        if len(client_ids) < 2:
            logger.warning("Need at least two clients to analyze divergence")
            return {"error": "Need at least two clients to analyze divergence"}
        
        # Load behaviors for each client
        behaviors = {}
        for client_id in client_ids:
            behaviors[client_id] = self.get_client_events(client_id)
        
        # Identify common action types across all clients
        action_types: Set[str] = set()
        for client_events in behaviors.values():
            action_types.update(event["event_type"] for event in client_events)
        
        # Analyze divergence in each action type
        divergence_points = {}
        for action_type in action_types:
            # Get all events of this type for each client
            client_action_events = {}
            for client_id, events in behaviors.items():
                client_action_events[client_id] = [
                    event for event in events if event["event_type"] == action_type
                ]
            
            # Skip if any client has no events of this type
            if any(len(events) == 0 for events in client_action_events.values()):
                continue
            
            # Compare behavior patterns
            divergence_points[action_type] = self._find_divergence(
                action_type, client_action_events
            )
        
        # Calculate overall divergence score
        total_divergence = sum(
            point["divergence_score"] 
            for action_points in divergence_points.values() 
            for point in action_points
        )
        
        # Count total action points
        total_actions = sum(
            len(events) for client_events in behaviors.values() for events in client_events
        )
        
        # Compile results
        results = {
            "client_ids": client_ids,
            "divergence_points": divergence_points,
            "total_divergence": total_divergence,
            "total_actions": total_actions,
            "divergence_score": total_divergence / max(1, total_actions),
            "timestamp": datetime.now().isoformat()
        }
        
        # Log analysis results
        analysis_file = self.log_dir / "divergence_analysis.jsonl"
        with open(analysis_file, "a") as f:
            f.write(json.dumps(results) + "\n")
        
        logger.info(f"Completed divergence analysis for clients: {', '.join(client_ids)}")
        return results
    
    def _find_divergence(self, action_type: str, client_events: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Find divergence points for a specific action type.
        
        Args:
            action_type: The type of action to analyze
            client_events: Dict mapping client IDs to their events of this type
            
        Returns:
            List of divergence points
        """
        divergence_points = []
        
        # Simple approach: compare each pair of clients
        client_ids = list(client_events.keys())
        
        for i in range(len(client_ids)):
            for j in range(i + 1, len(client_ids)):
                client_a = client_ids[i]
                client_b = client_ids[j]
                
                events_a = client_events[client_a]
                events_b = client_events[client_b]
                
                # Compare event sequences
                max_len = max(len(events_a), len(events_b))
                for idx in range(max_len):
                    # If one client has fewer events, that's a divergence
                    if idx >= len(events_a) or idx >= len(events_b):
                        divergence_points.append({
                            "type": "sequence_length",
                            "action_type": action_type,
                            "clients": [client_a, client_b],
                            "index": idx,
                            "description": f"Client {client_a if idx >= len(events_a) else client_b} has fewer {action_type} events",
                            "divergence_score": 1.0
                        })
                        continue
                    
                    # Compare event details
                    event_a = events_a[idx]
                    event_b = events_b[idx]
                    
                    # Compare event details
                    if self._event_differs(event_a, event_b):
                        divergence_points.append({
                            "type": "event_details",
                            "action_type": action_type,
                            "clients": [client_a, client_b],
                            "index": idx,
                            "event_a": event_a,
                            "event_b": event_b,
                            "description": f"Different {action_type} behavior at index {idx}",
                            "divergence_score": self._calculate_divergence_score(event_a, event_b)
                        })
        
        return divergence_points
    
    def _event_differs(self, event_a: Dict[str, Any], event_b: Dict[str, Any]) -> bool:
        """
        Check if two events differ in their details.
        
        Args:
            event_a: First event
            event_b: Second event
            
        Returns:
            bool: True if the events differ significantly
        """
        # Ignore timestamp and event_id in comparison
        details_a = event_a.get("details", {})
        details_b = event_b.get("details", {})
        
        # Simple comparison for now - in a real implementation,
        # this would be more sophisticated
        return details_a != details_b
    
    def _calculate_divergence_score(self, event_a: Dict[str, Any], event_b: Dict[str, Any]) -> float:
        """
        Calculate a divergence score between two events.
        
        Args:
            event_a: First event
            event_b: Second event
            
        Returns:
            float: Divergence score between 0.0 and 1.0
        """
        # Simple scoring for now - in a real implementation,
        # this would use more sophisticated metrics
        details_a = event_a.get("details", {})
        details_b = event_b.get("details", {})
        
        # Count different keys
        all_keys = set(details_a.keys()) | set(details_b.keys())
        different_keys = sum(1 for k in all_keys if details_a.get(k) != details_b.get(k))
        
        return different_keys / max(1, len(all_keys))
    
    def get_client_mode_summary(self, client_id: str) -> Dict[str, Any]:
        """
        Get a summary of the operational mode of a Claude instance.
        
        Args:
            client_id: ID of the Claude instance
            
        Returns:
            Dict with mode summary information
        """
        events = self.get_client_events(client_id)
        
        # Count event types
        event_type_counts = {}
        for event in events:
            event_type = event.get("event_type", "unknown")
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        # Look for mode indicators
        execution_events = sum(
            1 for event in events 
            if event.get("event_type") in ["execution", "file_write", "system_call"]
        )
        
        analysis_events = sum(
            1 for event in events 
            if event.get("event_type") in ["analysis", "code_explanation"]
        )
        
        # Determine most likely mode
        if execution_events > analysis_events:
            mode = "execution"
            confidence = execution_events / max(1, execution_events + analysis_events)
        else:
            mode = "analysis"
            confidence = analysis_events / max(1, execution_events + analysis_events)
        
        return {
            "client_id": client_id,
            "event_count": len(events),
            "event_types": event_type_counts,
            "detected_mode": mode,
            "mode_confidence": confidence,
            "execution_events": execution_events,
            "analysis_events": analysis_events,
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Simple command-line interface for testing
    import sys
    
    logger = BehaviorLogger()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "log" and len(sys.argv) > 4:
            client_id = sys.argv[2]
            event_type = sys.argv[3]
            details_json = sys.argv[4]
            
            try:
                details = json.loads(details_json)
                event_id = logger.log_behavior(client_id, event_type, details)
                print(f"Logged event: {event_id}")
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in details: {details_json}")
        
        elif command == "get" and len(sys.argv) > 2:
            client_id = sys.argv[2]
            events = logger.get_client_events(client_id)
            print(json.dumps(events, indent=2))
        
        elif command == "analyze" and len(sys.argv) > 2:
            client_ids = sys.argv[2:]
            results = logger.analyze_divergence(client_ids)
            print(json.dumps(results, indent=2))
        
        elif command == "summary" and len(sys.argv) > 2:
            client_id = sys.argv[2]
            summary = logger.get_client_mode_summary(client_id)
            print(json.dumps(summary, indent=2))
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: log, get, analyze, summary")
    else:
        print("Available commands: log, get, analyze, summary")