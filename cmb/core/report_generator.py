#!/usr/bin/env python3
"""
Report Generator - Generate reports from multiple Claude perspectives

This module provides functionality to collect perspectives from multiple
Claude instances and generate comprehensive reports incorporating
all viewpoints.
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb.report_generator")

# Try to import memory access modules
try:
    from cmb.core.memory import MemoryService
except ImportError:
    try:
        from engram.core.memory import MemoryService
    except ImportError:
        logger.warning("Memory service modules not available. Some functionality will be limited.")
        MemoryService = None

class MultiClaudeReport:
    """
    Generate reports from multiple Claude perspectives.
    
    This class collects perspectives from different Claude instances
    and synthesizes them into comprehensive reports.
    """
    
    def __init__(self, claude_ids: List[str], report_dir: Optional[str] = None, data_dir: Optional[str] = None):
        """
        Initialize the multi-Claude report generator.
        
        Args:
            claude_ids: List of Claude instance IDs to include
            report_dir: Directory to store generated reports
            data_dir: Directory containing memory data
        """
        self.claude_ids = claude_ids
        self.perspectives = {}
        
        # Set up report directory
        if report_dir is None:
            report_dir = os.path.expanduser("~/.cmb/reports")
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up data directory for memory access
        self.data_dir = data_dir
        
        # Initialize memory service if available
        self.memory_service = None
        if MemoryService is not None:
            try:
                # We're using an async init pattern, so we can't fully initialize
                # here, but we can set up the instance
                self.memory_service = MemoryService(data_dir=self.data_dir)
            except Exception as e:
                logger.error(f"Error initializing memory service: {e}")
        
        logger.info(f"Initialized multi-Claude report generator for {len(claude_ids)} instances")
    
    async def collect_perspectives(self, topic: str, namespace: str = "perspectives") -> Dict[str, str]:
        """
        Collect perspectives from each Claude instance.
        
        Args:
            topic: The topic to collect perspectives on
            namespace: The memory namespace to search
            
        Returns:
            Dict mapping Claude IDs to their perspectives
        """
        logger.info(f"Collecting perspectives on '{topic}' from {len(self.claude_ids)} instances")
        
        # Reset perspectives
        self.perspectives = {}
        
        # Use memory service if available
        if self.memory_service is not None:
            for claude_id in self.claude_ids:
                try:
                    # Search for perspectives from this Claude instance
                    query = f"perspective {topic} from {claude_id}"
                    results = await self.memory_service.search(
                        query=query,
                        namespace=namespace,
                        limit=5
                    )
                    
                    # Extract perspective text
                    if results.get("count", 0) > 0:
                        memory_items = results.get("results", [])
                        perspective_texts = []
                        
                        for item in memory_items:
                            content = item.get("content", "")
                            # Check if this is likely a perspective
                            if f"claude_id: {claude_id}" in content or f"client_id: {claude_id}" in content or f"from: {claude_id}" in content:
                                perspective_texts.append(content)
                        
                        if perspective_texts:
                            self.perspectives[claude_id] = "\n\n".join(perspective_texts)
                        else:
                            logger.warning(f"No perspective found for {claude_id} on topic '{topic}'")
                    else:
                        logger.warning(f"No memory items found for {claude_id} on topic '{topic}'")
                        
                except Exception as e:
                    logger.error(f"Error collecting perspective from {claude_id}: {e}")
        else:
            logger.warning("Memory service not available. Cannot collect perspectives.")
        
        # Return the collected perspectives
        return self.perspectives
    
    def _format_markdown_report(self, title: str, introduction: str, content_sections: Dict[str, str], synthesis: str) -> str:
        """
        Format a markdown report with the given sections.
        
        Args:
            title: Report title
            introduction: Introduction text
            content_sections: Dict mapping section names to content
            synthesis: Synthesis text
            
        Returns:
            str: Formatted markdown report
        """
        # Format the report
        report = f"# {title}\n\n{introduction}\n\n"
        
        # Add content sections
        for section_name, section_content in content_sections.items():
            report += f"## {section_name}\n\n{section_content}\n\n"
        
        # Add synthesis
        report += f"## Synthesis\n\n{synthesis}\n\n"
        
        # Add metadata
        report += f"---\n\nGenerated: {datetime.now().isoformat()[:19]}\n"
        report += f"Claude Instances: {', '.join(self.claude_ids)}\n"
        
        return report
    
    async def generate_report(self, title: str, introduction: str, synthesis: Optional[str] = None) -> str:
        """
        Generate a multi-perspective report.
        
        Args:
            title: Report title
            introduction: Introduction text
            synthesis: Optional synthesis text (if None, will be generated)
            
        Returns:
            str: Generated report
        """
        logger.info(f"Generating report: {title}")
        
        # Make sure we have perspectives
        if not self.perspectives:
            logger.warning("No perspectives collected. Report will be limited.")
        
        # Organize content sections
        content_sections = {}
        
        # Add perspective sections
        for claude_id, perspective in self.perspectives.items():
            section_name = f"Perspective from {claude_id}"
            content_sections[section_name] = perspective
        
        # Generate synthesis if not provided
        if synthesis is None:
            if self.perspectives:
                # Simple synthesis: find common themes
                all_text = "\n\n".join(self.perspectives.values())
                synthesis = self._generate_synthesis(all_text)
            else:
                synthesis = "No perspectives were collected to synthesize."
        
        # Format the report
        report = self._format_markdown_report(title, introduction, content_sections, synthesis)
        
        # Save the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.report_dir / f"report_{timestamp}.md"
        
        with open(report_file, "w") as f:
            f.write(report)
        
        logger.info(f"Saved report to {report_file}")
        return report
    
    def _generate_synthesis(self, text: str) -> str:
        """
        Generate a synthesis from the given text.
        
        Args:
            text: Text to synthesize
            
        Returns:
            str: Synthesized text
        """
        # In a real implementation, this would use more sophisticated
        # NLP techniques or even call another Claude instance
        
        # For now, we'll just do a simple word frequency analysis
        # to identify potential themes
        
        # Tokenize and count words
        words = text.lower().split()
        word_counts = {}
        for word in words:
            # Skip short words and common stopwords
            if len(word) < 4 or word in ["this", "that", "with", "from", "have", "what"]:
                continue
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get top words
        top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Generate synthesis
        synthesis = "### Common Themes\n\n"
        synthesis += "Based on the various perspectives, the following themes emerge:\n\n"
        
        for word, count in top_words:
            synthesis += f"- **{word}**: Mentioned {count} times across perspectives\n"
        
        synthesis += "\n### Integration of Perspectives\n\n"
        synthesis += "The perspectives presented offer complementary viewpoints on the topic. "
        synthesis += "While a full synthesis would require deeper analysis, "
        synthesis += "it's clear that there are both areas of agreement and divergence "
        synthesis += "among the different Claude instances.\n\n"
        
        synthesis += "A more comprehensive synthesis would be possible with "
        synthesis += "advanced natural language processing or by having another "
        synthesis += "Claude instance analyze these perspectives in detail."
        
        return synthesis
    
    def save_perspective(self, claude_id: str, topic: str, perspective: str) -> Dict[str, Any]:
        """
        Save a perspective from a Claude instance for later use in reports.
        
        Args:
            claude_id: ID of the Claude instance
            topic: Topic of the perspective
            perspective: Perspective text
            
        Returns:
            Dict with save result information
        """
        # Store in memory
        self.perspectives[claude_id] = perspective
        
        # Save to disk as well
        perspective_dir = self.report_dir / "perspectives"
        perspective_dir.mkdir(exist_ok=True)
        
        # Create filename
        sanitized_topic = "".join(c if c.isalnum() else "_" for c in topic)
        perspective_file = perspective_dir / f"{claude_id}_{sanitized_topic}.md"
        
        # Save to file
        with open(perspective_file, "w") as f:
            f.write(f"# Perspective from {claude_id} on {topic}\n\n")
            f.write(f"Claude ID: {claude_id}\n")
            f.write(f"Topic: {topic}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n\n")
            f.write(perspective)
        
        logger.info(f"Saved perspective from {claude_id} on topic '{topic}'")
        
        return {
            "success": True,
            "claude_id": claude_id,
            "topic": topic,
            "file": str(perspective_file),
            "timestamp": datetime.now().isoformat()
        }
    
    def list_available_perspectives(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List all available perspectives saved to disk.
        
        Returns:
            Dict mapping Claude IDs to lists of their perspectives
        """
        perspective_dir = self.report_dir / "perspectives"
        if not perspective_dir.exists():
            return {}
        
        perspectives = {}
        
        for perspective_file in perspective_dir.glob("*.md"):
            try:
                # Parse filename to get Claude ID and topic
                filename = perspective_file.name
                claude_id = filename.split("_")[0]
                
                # Read the file to extract metadata
                with open(perspective_file, "r") as f:
                    content = f.read()
                
                # Extract topic line
                topic_line = None
                timestamp_line = None
                for line in content.split("\n"):
                    if line.startswith("Topic: "):
                        topic_line = line[7:]
                    elif line.startswith("Timestamp: "):
                        timestamp_line = line[11:]
                
                if claude_id not in perspectives:
                    perspectives[claude_id] = []
                
                perspectives[claude_id].append({
                    "file": str(perspective_file),
                    "topic": topic_line or "Unknown",
                    "timestamp": timestamp_line or "Unknown",
                    "size": perspective_file.stat().st_size
                })
                
            except Exception as e:
                logger.error(f"Error parsing perspective file {perspective_file}: {e}")
        
        return perspectives

if __name__ == "__main__":
    # Simple command-line interface for testing
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "save" and len(sys.argv) > 4:
                claude_id = sys.argv[2]
                topic = sys.argv[3]
                perspective = sys.argv[4]
                
                report_gen = MultiClaudeReport([claude_id])
                result = report_gen.save_perspective(claude_id, topic, perspective)
                print(json.dumps(result, indent=2))
                
            elif command == "list":
                report_gen = MultiClaudeReport([])
                perspectives = report_gen.list_available_perspectives()
                print(json.dumps(perspectives, indent=2))
                
            elif command == "generate" and len(sys.argv) > 3:
                title = sys.argv[2]
                introduction = sys.argv[3]
                
                # Get Claude IDs from available perspectives
                report_gen = MultiClaudeReport([])
                perspectives = report_gen.list_available_perspectives()
                claude_ids = list(perspectives.keys())
                
                report_gen = MultiClaudeReport(claude_ids)
                
                # Load saved perspectives
                for claude_id, persp_list in perspectives.items():
                    for persp_info in persp_list:
                        with open(persp_info["file"], "r") as f:
                            content = f.read()
                            report_gen.perspectives[claude_id] = content
                
                report = await report_gen.generate_report(title, introduction)
                print(f"Report generated. First 500 characters:\n\n{report[:500]}...")
                
            else:
                print(f"Unknown command: {command}")
                print("Available commands: save, list, generate")
        else:
            print("Available commands: save, list, generate")
    
    asyncio.run(main())