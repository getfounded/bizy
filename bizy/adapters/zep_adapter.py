"""
Zep AI Adapter: Integration with Zep AI memory systems.

This module provides the adapter for executing business rules through
Zep AI's memory and temporal knowledge graph capabilities.
"""

from typing import Any, Dict, List, Optional, Tuple
import logging
import asyncio
from datetime import datetime, timedelta
import uuid

from ..core.framework_adapter import BaseFrameworkAdapter
from ..core.business_rule import BusinessRule, RuleAction

logger = logging.getLogger(__name__)


class ZepAdapter(BaseFrameworkAdapter):
    """
    Adapter for integrating Zep AI with the Business Logic Orchestrator.
    
    Provides capabilities for:
    - Memory persistence and retrieval
    - Temporal knowledge graphs
    - Context management
    - Session handling
    - Fact extraction and storage
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("zep", config)
        self.capabilities = [
            "memory_persistence",
            "temporal_knowledge",
            "context_management",
            "session_handling",
            "fact_extraction",
            "semantic_search"
        ]
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.memories: Dict[str, List[Dict[str, Any]]] = {}
        self.knowledge_graph: Dict[str, Any] = {"nodes": {}, "edges": []}
        self.api_url = config.get("api_url", "http://localhost:8000")
        self.api_key = config.get("api_key", "")
        
    async def connect(self) -> None:
        """Connect to Zep AI service and initialize memory systems."""
        try:
            # Initialize memory storage
            self.memories = {}
            self.sessions = {}
            
            # Initialize knowledge graph
            self.knowledge_graph = {
                "nodes": {},
                "edges": [],
                "temporal_index": {}
            }
            
            # Register built-in memory operations
            await self._register_memory_operations()
            
            self.is_connected = True
            logger.info("Zep AI adapter connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect Zep AI adapter: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from Zep AI service."""
        try:
            # Persist any pending memories
            await self._persist_pending_memories()
            
            # Clear local caches
            self.sessions.clear()
            self.memories.clear()
            self.knowledge_graph.clear()
            
            self.is_connected = False
            logger.info("Zep AI adapter disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting Zep AI adapter: {e}")
            
    async def _execute_action(self, action: RuleAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific action using Zep AI.
        
        Supported actions:
        - store_memory: Store memory with metadata
        - retrieve_memory: Retrieve relevant memories
        - manage_session: Create/update session
        - extract_facts: Extract facts from content
        - query_knowledge: Query knowledge graph
        - semantic_search: Perform semantic search
        """
        action_type = action.action
        params = action.parameters
        
        try:
            if action_type == "store_memory":
                return await self._store_memory(params, context)
            elif action_type == "retrieve_memory":
                return await self._retrieve_memory(params, context)
            elif action_type == "manage_session":
                return await self._manage_session(params, context)
            elif action_type == "extract_facts":
                return await self._extract_facts(params, context)
            elif action_type == "query_knowledge":
                return await self._query_knowledge_graph(params, context)
            elif action_type == "semantic_search":
                return await self._semantic_search(params, context)
            else:
                raise ValueError(f"Unsupported action type: {action_type}")
                
        except Exception as e:
            logger.error(f"Error executing Zep AI action {action_type}: {e}")
            raise
            
    async def _store_memory(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Store memory with temporal and contextual metadata."""
        session_id = params.get("session_id", "default")
        content = params.get("content", "")
        metadata = params.get("metadata", {})
        memory_type = params.get("type", "conversation")
        
        # Create memory entry
        memory_entry = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "content": content,
            "type": memory_type,
            "metadata": {**metadata, **context},
            "timestamp": datetime.utcnow().isoformat(),
            "embedding": None  # Would be generated in production
        }
        
        # Store in session memories
        if session_id not in self.memories:
            self.memories[session_id] = []
        self.memories[session_id].append(memory_entry)
        
        # Update knowledge graph if facts are present
        if memory_type == "fact":
            await self._update_knowledge_graph(memory_entry)
            
        # Update session
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = datetime.utcnow()
            self.sessions[session_id]["memory_count"] += 1
            
        return {
            "memory_id": memory_entry["id"],
            "session_id": session_id,
            "stored": True,
            "timestamp": memory_entry["timestamp"]
        }
        
    async def _retrieve_memory(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant memories based on query and filters."""
        session_id = params.get("session_id", "default")
        query = params.get("query", "")
        limit = params.get("limit", 10)
        time_range = params.get("time_range", None)
        memory_types = params.get("types", None)
        
        # Get session memories
        session_memories = self.memories.get(session_id, [])
        
        # Apply filters
        filtered_memories = []
        for memory in session_memories:
            # Type filter
            if memory_types and memory["type"] not in memory_types:
                continue
                
            # Time range filter
            if time_range:
                memory_time = datetime.fromisoformat(memory["timestamp"])
                if "start" in time_range:
                    start_time = datetime.fromisoformat(time_range["start"])
                    if memory_time < start_time:
                        continue
                if "end" in time_range:
                    end_time = datetime.fromisoformat(time_range["end"])
                    if memory_time > end_time:
                        continue
                        
            filtered_memories.append(memory)
            
        # In production, would use semantic search
        # For now, simple text matching
        if query:
            scored_memories = []
            for memory in filtered_memories:
                score = self._calculate_relevance_score(query, memory["content"])
                scored_memories.append((score, memory))
                
            # Sort by relevance
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            relevant_memories = [m[1] for m in scored_memories[:limit]]
        else:
            # Return most recent
            relevant_memories = sorted(
                filtered_memories,
                key=lambda x: x["timestamp"],
                reverse=True
            )[:limit]
            
        return {
            "session_id": session_id,
            "query": query,
            "memories": relevant_memories,
            "count": len(relevant_memories),
            "total_available": len(filtered_memories)
        }
        
    async def _manage_session(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a session."""
        session_id = params.get("session_id")
        operation = params.get("operation", "create")
        
        if operation == "create":
            if not session_id:
                session_id = str(uuid.uuid4())
                
            self.sessions[session_id] = {
                "id": session_id,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "metadata": params.get("metadata", {}),
                "memory_count": 0,
                "fact_count": 0
            }
            
            return {
                "session_id": session_id,
                "operation": "created",
                "status": "active"
            }
            
        elif operation == "update":
            if session_id not in self.sessions:
                raise ValueError(f"Session not found: {session_id}")
                
            session = self.sessions[session_id]
            session["last_activity"] = datetime.utcnow()
            
            if "metadata" in params:
                session["metadata"].update(params["metadata"])
                
            return {
                "session_id": session_id,
                "operation": "updated",
                "status": "active"
            }
            
        elif operation == "close":
            if session_id in self.sessions:
                self.sessions[session_id]["status"] = "closed"
                self.sessions[session_id]["closed_at"] = datetime.utcnow()
                
            return {
                "session_id": session_id,
                "operation": "closed",
                "status": "closed"
            }
            
    async def _extract_facts(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract facts from content and store in knowledge graph."""
        content = params.get("content", "")
        fact_type = params.get("fact_type", "general")
        confidence = params.get("confidence", 0.8)
        
        # Simulate fact extraction
        # In production, would use NLP/LLM for extraction
        extracted_facts = []
        
        # Simple extraction for demonstration
        sentences = content.split(".")
        for sentence in sentences:
            if len(sentence.strip()) > 10:
                fact = {
                    "id": str(uuid.uuid4()),
                    "content": sentence.strip(),
                    "type": fact_type,
                    "confidence": confidence,
                    "source": params.get("source", "user_input"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "entities": self._extract_entities(sentence),
                    "relationships": []
                }
                extracted_facts.append(fact)
                
                # Add to knowledge graph
                await self._add_fact_to_graph(fact)
                
        return {
            "facts_extracted": len(extracted_facts),
            "facts": extracted_facts,
            "content_length": len(content)
        }
        
    async def _query_knowledge_graph(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Query the temporal knowledge graph."""
        query_type = params.get("query_type", "nodes")
        entity = params.get("entity")
        relationship_type = params.get("relationship_type")
        time_range = params.get("time_range")
        
        results = []
        
        if query_type == "nodes":
            # Query nodes
            for node_id, node in self.knowledge_graph["nodes"].items():
                if entity and node.get("entity") != entity:
                    continue
                    
                # Check temporal filter
                if time_range and "timestamp" in node:
                    node_time = datetime.fromisoformat(node["timestamp"])
                    if not self._in_time_range(node_time, time_range):
                        continue
                        
                results.append(node)
                
        elif query_type == "edges":
            # Query relationships
            for edge in self.knowledge_graph["edges"]:
                if relationship_type and edge.get("type") != relationship_type:
                    continue
                    
                # Check temporal filter
                if time_range and "timestamp" in edge:
                    edge_time = datetime.fromisoformat(edge["timestamp"])
                    if not self._in_time_range(edge_time, time_range):
                        continue
                        
                results.append(edge)
                
        elif query_type == "path":
            # Find paths between entities
            start_entity = params.get("start_entity")
            end_entity = params.get("end_entity")
            
            if start_entity and end_entity:
                paths = self._find_paths(start_entity, end_entity)
                results = paths
                
        return {
            "query_type": query_type,
            "results": results,
            "count": len(results),
            "graph_stats": {
                "total_nodes": len(self.knowledge_graph["nodes"]),
                "total_edges": len(self.knowledge_graph["edges"])
            }
        }
        
    async def _semantic_search(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform semantic search across memories and facts."""
        query = params.get("query", "")
        search_scope = params.get("scope", ["memories", "facts"])
        limit = params.get("limit", 10)
        
        all_results = []
        
        # Search memories
        if "memories" in search_scope:
            for session_id, memories in self.memories.items():
                for memory in memories:
                    score = self._calculate_relevance_score(query, memory["content"])
                    if score > 0.5:  # Threshold
                        all_results.append({
                            "type": "memory",
                            "content": memory["content"],
                            "score": score,
                            "metadata": memory["metadata"],
                            "timestamp": memory["timestamp"]
                        })
                        
        # Search facts in knowledge graph
        if "facts" in search_scope:
            for node_id, node in self.knowledge_graph["nodes"].items():
                if "content" in node:
                    score = self._calculate_relevance_score(query, node["content"])
                    if score > 0.5:
                        all_results.append({
                            "type": "fact",
                            "content": node["content"],
                            "score": score,
                            "confidence": node.get("confidence", 1.0),
                            "timestamp": node.get("timestamp")
                        })
                        
        # Sort by relevance score
        all_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = all_results[:limit]
        
        return {
            "query": query,
            "results": top_results,
            "total_found": len(all_results),
            "returned": len(top_results),
            "search_scope": search_scope
        }
        
    async def _register_memory_operations(self) -> None:
        """Register built-in memory operations."""
        # Memory operations would be registered here
        pass
        
    async def _persist_pending_memories(self) -> None:
        """Persist any pending memories to storage."""
        # In production, would save to persistent storage
        logger.info(f"Persisting {sum(len(m) for m in self.memories.values())} memories")
        
    async def _update_knowledge_graph(self, memory_entry: Dict[str, Any]) -> None:
        """Update knowledge graph with new memory entry."""
        # Extract entities and relationships
        entities = self._extract_entities(memory_entry["content"])
        
        # Add nodes for entities
        for entity in entities:
            node_id = f"entity_{entity}"
            if node_id not in self.knowledge_graph["nodes"]:
                self.knowledge_graph["nodes"][node_id] = {
                    "id": node_id,
                    "entity": entity,
                    "type": "entity",
                    "first_seen": memory_entry["timestamp"],
                    "occurrences": 1
                }
            else:
                self.knowledge_graph["nodes"][node_id]["occurrences"] += 1
                
    async def _add_fact_to_graph(self, fact: Dict[str, Any]) -> None:
        """Add a fact to the knowledge graph."""
        node_id = fact["id"]
        self.knowledge_graph["nodes"][node_id] = {
            "id": node_id,
            "type": "fact",
            "content": fact["content"],
            "confidence": fact["confidence"],
            "timestamp": fact["timestamp"],
            "entities": fact["entities"]
        }
        
        # Create edges between entities in the fact
        entities = fact["entities"]
        for i in range(len(entities) - 1):
            edge = {
                "source": f"entity_{entities[i]}",
                "target": f"entity_{entities[i+1]}",
                "type": "related",
                "fact_id": node_id,
                "timestamp": fact["timestamp"]
            }
            self.knowledge_graph["edges"].append(edge)
            
    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """Calculate simple relevance score between query and content."""
        # Simple implementation - in production would use embeddings
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Exact match
        if query_lower in content_lower:
            return 1.0
            
        # Word overlap
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        
        if not query_words:
            return 0.0
            
        overlap = len(query_words & content_words)
        return overlap / len(query_words)
        
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text (simplified)."""
        # Simple implementation - in production would use NER
        entities = []
        
        # Extract capitalized words as potential entities
        words = text.split()
        for word in words:
            if word and word[0].isupper() and len(word) > 2:
                entities.append(word.strip(".,!?"))
                
        return entities
        
    def _in_time_range(self, timestamp: datetime, time_range: Dict[str, str]) -> bool:
        """Check if timestamp is within time range."""
        if "start" in time_range:
            start = datetime.fromisoformat(time_range["start"])
            if timestamp < start:
                return False
                
        if "end" in time_range:
            end = datetime.fromisoformat(time_range["end"])
            if timestamp > end:
                return False
                
        return True
        
    def _find_paths(self, start_entity: str, end_entity: str, max_depth: int = 5) -> List[List[str]]:
        """Find paths between entities in knowledge graph."""
        # Simple BFS implementation
        paths = []
        queue = [(f"entity_{start_entity}", [f"entity_{start_entity}"])]
        visited = set()
        
        while queue and len(paths) < 10:  # Limit results
            current, path = queue.pop(0)
            
            if current in visited:
                continue
                
            visited.add(current)
            
            if current == f"entity_{end_entity}":
                paths.append(path)
                continue
                
            if len(path) >= max_depth:
                continue
                
            # Find connected nodes
            for edge in self.knowledge_graph["edges"]:
                next_node = None
                if edge["source"] == current:
                    next_node = edge["target"]
                elif edge["target"] == current:
                    next_node = edge["source"]
                    
                if next_node and next_node not in visited:
                    queue.append((next_node, path + [next_node]))
                    
        return paths
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Zep AI adapter."""
        health_status = await super().health_check()
        
        # Add Zep-specific metrics
        total_memories = sum(len(m) for m in self.memories.values())
        
        health_status.update({
            "active_sessions": len(self.sessions),
            "total_memories": total_memories,
            "knowledge_graph_nodes": len(self.knowledge_graph["nodes"]),
            "knowledge_graph_edges": len(self.knowledge_graph["edges"]),
            "memory_sessions": list(self.memories.keys()),
            "api_url": self.api_url
        })
        
        return health_status