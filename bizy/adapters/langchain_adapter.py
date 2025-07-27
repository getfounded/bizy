"""
LangChain Adapter: Integration with LangChain framework.

This module provides the adapter for executing business rules through
LangChain's chain and agent capabilities.
"""

from typing import Any, Dict, List, Optional
import logging
import asyncio

from langchain.chains import LLMChain
from langchain.agents import Tool, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import FakeListLLM

from ..core.framework_adapter import BaseFrameworkAdapter
from ..core.business_rule import BusinessRule, RuleAction

logger = logging.getLogger(__name__)


class LangChainAdapter(BaseFrameworkAdapter):
    """
    Adapter for integrating LangChain with the Business Logic Orchestrator.
    
    Provides capabilities for:
    - Chain execution
    - Agent orchestration
    - Tool integration
    - Memory management
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("langchain", config)
        self.capabilities = [
            "chain_execution",
            "agent_orchestration",
            "tool_integration",
            "memory_management",
            "document_analysis",
            "llm_interaction"
        ]
        self.chains: Dict[str, LLMChain] = {}
        self.agents: Dict[str, AgentExecutor] = {}
        self.tools: Dict[str, Tool] = {}
        self.memory_stores: Dict[str, ConversationBufferMemory] = {}
        
    async def connect(self) -> None:
        """Establish connection to LangChain components."""
        try:
            # Initialize default LLM (using FakeListLLM for testing)
            # In production, this would be replaced with actual LLM
            self.llm = FakeListLLM(responses=["Test response"])
            
            # Initialize default memory
            self.default_memory = ConversationBufferMemory()
            
            # Register built-in tools
            await self._register_builtin_tools()
            
            self.is_connected = True
            logger.info("LangChain adapter connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect LangChain adapter: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from LangChain components."""
        try:
            # Clear all registered components
            self.chains.clear()
            self.agents.clear()
            self.tools.clear()
            self.memory_stores.clear()
            
            self.is_connected = False
            logger.info("LangChain adapter disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting LangChain adapter: {e}")
            
    async def _execute_action(self, action: RuleAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific action using LangChain.
        
        Supported actions:
        - run_chain: Execute a LangChain chain
        - run_agent: Execute a LangChain agent
        - analyze_document: Analyze document content
        - query_memory: Query conversation memory
        """
        action_type = action.action
        params = action.parameters
        
        try:
            if action_type == "run_chain":
                return await self._run_chain(params, context)
            elif action_type == "run_agent":
                return await self._run_agent(params, context)
            elif action_type == "analyze_document":
                return await self._analyze_document(params, context)
            elif action_type == "query_memory":
                return await self._query_memory(params, context)
            else:
                raise ValueError(f"Unsupported action type: {action_type}")
                
        except Exception as e:
            logger.error(f"Error executing LangChain action {action_type}: {e}")
            raise
            
    async def _run_chain(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a LangChain chain."""
        chain_name = params.get("chain_name", "default")
        prompt = params.get("prompt", "")
        input_variables = params.get("input_variables", {})
        
        # Merge context into input variables
        merged_inputs = {**context, **input_variables}
        
        # Get or create chain
        chain = self.chains.get(chain_name)
        if not chain:
            # Create a simple chain for demonstration
            # In production, this would load predefined chains
            from langchain.prompts import PromptTemplate
            prompt_template = PromptTemplate(
                input_variables=list(merged_inputs.keys()),
                template=prompt
            )
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            self.chains[chain_name] = chain
            
        # Execute chain
        result = await asyncio.get_event_loop().run_in_executor(
            None, chain.run, merged_inputs
        )
        
        return {
            "chain_name": chain_name,
            "result": result,
            "inputs": merged_inputs
        }
        
    async def _run_agent(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a LangChain agent."""
        agent_name = params.get("agent_name", "default")
        task = params.get("task", "")
        tools = params.get("tools", [])
        
        # Get or create agent
        agent = self.agents.get(agent_name)
        if not agent:
            # Create agent with specified tools
            agent_tools = [self.tools[t] for t in tools if t in self.tools]
            
            # Create a simple agent for demonstration
            # In production, this would use more sophisticated agent types
            from langchain.agents import initialize_agent, AgentType
            agent = initialize_agent(
                agent_tools,
                self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )
            self.agents[agent_name] = agent
            
        # Execute agent
        result = await asyncio.get_event_loop().run_in_executor(
            None, agent.run, task
        )
        
        return {
            "agent_name": agent_name,
            "task": task,
            "result": result
        }
        
    async def _analyze_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document content using LangChain."""
        document_content = params.get("content", "")
        analysis_type = params.get("analysis_type", "summary")
        
        # Create analysis chain
        from langchain.prompts import PromptTemplate
        
        analysis_prompts = {
            "summary": "Summarize the following document: {document}",
            "entities": "Extract entities from the following document: {document}",
            "sentiment": "Analyze the sentiment of the following document: {document}",
            "topics": "Extract main topics from the following document: {document}"
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["summary"])
        
        prompt_template = PromptTemplate(
            input_variables=["document"],
            template=prompt
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        
        # Run analysis
        result = await asyncio.get_event_loop().run_in_executor(
            None, chain.run, document_content
        )
        
        return {
            "analysis_type": analysis_type,
            "result": result,
            "document_length": len(document_content)
        }
        
    async def _query_memory(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Query conversation memory."""
        memory_name = params.get("memory_name", "default")
        query = params.get("query", "")
        
        # Get memory store
        memory = self.memory_stores.get(memory_name, self.default_memory)
        
        # For demonstration, return memory buffer
        # In production, this would support more sophisticated queries
        memory_content = memory.buffer
        
        return {
            "memory_name": memory_name,
            "query": query,
            "result": memory_content,
            "message_count": len(memory.chat_memory.messages)
        }
        
    async def _register_builtin_tools(self) -> None:
        """Register built-in tools for agent use."""
        # Calculator tool
        def calculator(expression: str) -> str:
            try:
                return str(eval(expression))
            except:
                return "Error: Invalid expression"
                
        self.tools["calculator"] = Tool(
            name="Calculator",
            func=calculator,
            description="Useful for mathematical calculations"
        )
        
        # Text length tool
        def text_length(text: str) -> str:
            return f"The text has {len(text)} characters"
            
        self.tools["text_length"] = Tool(
            name="TextLength",
            func=text_length,
            description="Get the length of a text"
        )
        
    def register_chain(self, name: str, chain: LLMChain) -> None:
        """Register a custom chain."""
        self.chains[name] = chain
        logger.info(f"Registered chain: {name}")
        
    def register_agent(self, name: str, agent: AgentExecutor) -> None:
        """Register a custom agent."""
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")
        
    def register_tool(self, name: str, tool: Tool) -> None:
        """Register a custom tool."""
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on LangChain adapter."""
        health_status = await super().health_check()
        
        # Add LangChain-specific metrics
        health_status.update({
            "chains_registered": len(self.chains),
            "agents_registered": len(self.agents),
            "tools_registered": len(self.tools),
            "memory_stores": len(self.memory_stores),
            "llm_type": type(self.llm).__name__
        })
        
        return health_status