#!/usr/bin/env python3
"""
Performance optimizations for provenance tracking.

Ensures that provenance doesn't slow down basic memory operations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Set
from functools import wraps
from collections import defaultdict


class ProvenancePerformanceMonitor:
    """Monitor and optimize provenance operations."""
    
    def __init__(self):
        self.operation_times = defaultdict(list)
        self.slow_threshold_ms = 10  # Operations slower than this are logged
        
    def record_operation(self, operation: str, duration_ms: float):
        """Record operation timing."""
        self.operation_times[operation].append(duration_ms)
        
        # Log slow operations
        if duration_ms > self.slow_threshold_ms:
            print(f"Slow provenance operation: {operation} took {duration_ms:.2f}ms")
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics."""
        stats = {}
        for op, times in self.operation_times.items():
            if times:
                stats[op] = {
                    'count': len(times),
                    'avg_ms': sum(times) / len(times),
                    'max_ms': max(times),
                    'min_ms': min(times)
                }
        return stats


class LazyProvenanceLoader:
    """
    Lazy loader for provenance data.
    
    Only loads provenance when explicitly requested.
    """
    
    def __init__(self, memory_id: str, storage):
        self.memory_id = memory_id
        self.storage = storage
        self._loaded = False
        self._data = None
        
    async def load(self) -> Optional[Dict[str, Any]]:
        """Load provenance data on demand."""
        if not self._loaded:
            self._data = await self.storage.get_provenance(self.memory_id)
            self._loaded = True
        return self._data
    
    @property
    def is_loaded(self) -> bool:
        """Check if provenance has been loaded."""
        return self._loaded


class ProvenanceBatchProcessor:
    """
    Batch provenance operations for efficiency.
    
    Groups multiple provenance updates to reduce storage calls.
    """
    
    def __init__(self, storage, batch_size: int = 10, flush_interval: float = 1.0):
        self.storage = storage
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        self._batch = []
        self._lock = asyncio.Lock()
        self._flush_task = None
        
    async def start(self):
        """Start batch processor."""
        self._flush_task = asyncio.create_task(self._periodic_flush())
        
    async def stop(self):
        """Stop batch processor and flush remaining."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining items
        await self._flush()
    
    async def add_operation(self, operation: Dict[str, Any]):
        """Add operation to batch."""
        async with self._lock:
            self._batch.append(operation)
            
            # Flush if batch is full
            if len(self._batch) >= self.batch_size:
                await self._flush()
    
    async def _flush(self):
        """Flush batch to storage."""
        async with self._lock:
            if not self._batch:
                return
                
            # Group operations by memory_id for efficiency
            grouped = defaultdict(list)
            for op in self._batch:
                grouped[op['memory_id']].append(op)
            
            # Process each group
            for memory_id, ops in grouped.items():
                # Combine multiple operations on same memory
                await self._process_group(memory_id, ops)
            
            self._batch.clear()
    
    async def _process_group(self, memory_id: str, operations: List[Dict[str, Any]]):
        """Process grouped operations efficiently."""
        # Get existing provenance once
        prov_data = await self.storage.get_provenance(memory_id, use_cache=True)
        if not prov_data:
            prov_data = {
                "memory_id": memory_id,
                "chain": [],
                "current_branch": "main",
                "version": 1
            }
        
        # Apply all operations
        for op in operations:
            if op['type'] == 'edit':
                entry = {
                    "actor": op['actor'],
                    "action": op['action'],
                    "timestamp": op['timestamp'],
                    "note": op.get('note')
                }
                prov_data["chain"].append(entry)
                prov_data["version"] += 1
        
        # Write once
        await self.storage._write_provenance(memory_id, prov_data)
    
    async def _periodic_flush(self):
        """Periodically flush batch."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush()
            except asyncio.CancelledError:
                break


def track_performance(monitor: ProvenancePerformanceMonitor):
    """Decorator to track performance of async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start) * 1000
                monitor.record_operation(func.__name__, duration_ms)
        return wrapper
    return decorator


class OptimizedProvenanceStorage:
    """
    Performance-optimized provenance storage.
    
    Features:
    - Lazy loading
    - Batch processing
    - Performance monitoring
    - Smart caching
    """
    
    def __init__(self, base_storage):
        self.base_storage = base_storage
        self.monitor = ProvenancePerformanceMonitor()
        self.batch_processor = ProvenanceBatchProcessor(base_storage)
        
        # Cache configuration
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_size = 1000
        self._cache_timestamps = {}
        
    async def start(self):
        """Start optimized storage."""
        await self.base_storage.start()
        await self.batch_processor.start()
        
    async def stop(self):
        """Stop optimized storage."""
        await self.batch_processor.stop()
        await self.base_storage.stop()
        
        # Print performance stats
        stats = self.monitor.get_stats()
        if stats:
            print("Provenance Performance Stats:")
            for op, data in stats.items():
                print(f"  {op}: avg={data['avg_ms']:.2f}ms, max={data['max_ms']:.2f}ms")
    
    @track_performance
    async def track_creation(self, memory_id: str, creator: str,
                           content: str, metadata: Dict[str, Any]) -> None:
        """Track creation with batching."""
        await self.batch_processor.add_operation({
            'type': 'creation',
            'memory_id': memory_id,
            'actor': creator,
            'action': 'created',
            'timestamp': time.time(),
            'metadata': metadata
        })
    
    @track_performance
    async def get_provenance_lazy(self, memory_id: str) -> LazyProvenanceLoader:
        """Get lazy loader for provenance."""
        return LazyProvenanceLoader(memory_id, self.base_storage)
    
    def should_track(self, namespace: str, importance: int = 3) -> bool:
        """
        Determine if memory should be tracked based on heuristics.
        
        Skip tracking for:
        - Temporary namespaces
        - Low importance memories
        - High-frequency operations
        """
        # Skip temporary namespaces
        if namespace.startswith("_tmp_") or namespace == "session":
            return False
            
        # Skip low importance
        if importance < 3:
            return False
            
        # Always track important namespaces
        if namespace in {"shared", "longterm", "projects"}:
            return True
            
        # Default: track
        return True
    
    def _is_cache_valid(self, memory_id: str) -> bool:
        """Check if cached entry is still valid."""
        if memory_id not in self._cache_timestamps:
            return False
            
        age = time.time() - self._cache_timestamps[memory_id]
        return age < self.cache_ttl
    
    def _evict_old_cache(self):
        """Evict old cache entries if needed."""
        if len(self._cache_timestamps) > self.max_cache_size:
            # Evict oldest 10%
            sorted_ids = sorted(
                self._cache_timestamps.items(),
                key=lambda x: x[1]
            )
            to_evict = sorted_ids[:self.max_cache_size // 10]
            
            for memory_id, _ in to_evict:
                self._cache_timestamps.pop(memory_id, None)
                self.base_storage._cache.pop(memory_id, None)