"""
Semantic Kernel Adapter: Integration with Microsoft Semantic Kernel.

This module provides the adapter for executing business rules through
Semantic Kernel's agent and skill capabilities.
"""

from typing import Any, Dict, List, Optional
import logging
import asyncio

import semantic_kernel as sk
from semantic_kernel.planning import ActionPlanner, SequentialPlanner
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

from ..core.framework_adapter import BaseFrameworkAdapter
from ..core.business_rule import BusinessRule, RuleAction

logger = logging.getLogger(__name__)


class SemanticKernelAdapter(BaseFrameworkAdapter):
    """
    Adapter for integrating Semantic Kernel with the Business Logic Orchestrator.
    
    Provides capabilities for:
    - Skill orchestration
    - Agent communication
    - Planning and execution
    - Memory and context management
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("semantic_kernel", config)
        self.capabilities = [
            "skill_orchestration",
            "agent_communication",
            "planning",
            "context_management",
            "semantic_functions",
            "native_functions"
        ]
        self.kernel: Optional[sk.Kernel] = None
        self.planners: Dict[str, Any] = {}
        self.skills: Dict[str, Any] = {}
        
    async def connect(self) -> None:
        """Initialize Semantic Kernel and components."""
        try:
            # Initialize kernel
            self.kernel = sk.Kernel()
            
            # Configure AI service (using mock for now)
            # In production, this would use actual AI service
            # self.kernel.add_text_completion_service(
            #     "completion",
            #     OpenAITextCompletion("text-davinci-003", api_key)
            # )
            
            # Initialize planners
            self.planners["action"] = ActionPlanner(self.kernel)
            self.planners["sequential"] = SequentialPlanner(self.kernel)
            
            # Register built-in skills
            await self._register_builtin_skills()
            
            self.is_connected = True
            logger.info("Semantic Kernel adapter connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect Semantic Kernel adapter: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from Semantic Kernel."""
        try:
            # Clear registered components
            self.planners.clear()
            self.skills.clear()
            self.kernel = None
            
            self.is_connected = False
            logger.info("Semantic Kernel adapter disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting Semantic Kernel adapter: {e}")
            
    async def _execute_action(self, action: RuleAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific action using Semantic Kernel.
        
        Supported actions:
        - run_skill: Execute a semantic skill
        - run_plan: Execute a plan
        - communicate_agent: Send message to agent
        - manage_context: Manage conversation context
        """
        action_type = action.action
        params = action.parameters
        
        try:
            if action_type == "run_skill":
                return await self._run_skill(params, context)
            elif action_type == "run_plan":
                return await self._run_plan(params, context)
            elif action_type == "communicate_agent":
                return await self._communicate_agent(params, context)
            elif action_type == "manage_context":
                return await self._manage_context(params, context)
            else:
                raise ValueError(f"Unsupported action type: {action_type}")
                
        except Exception as e:
            logger.error(f"Error executing Semantic Kernel action {action_type}: {e}")
            raise
            
    async def _run_skill(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a semantic skill."""
        skill_name = params.get("skill_name")
        function_name = params.get("function_name")
        input_text = params.get("input", "")
        
        # Get skill
        skill = self.skills.get(skill_name)
        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")
            
        # Get function
        if hasattr(skill, function_name):
            function = getattr(skill, function_name)
        else:
            raise ValueError(f"Function not found: {function_name}")
            
        # Create context
        sk_context = self.kernel.create_new_context()
        sk_context["input"] = input_text
        
        # Add business context
        for key, value in context.items():
            sk_context[key] = str(value)
            
        # Execute function
        result = await function.invoke_async(context=sk_context)
        
        return {
            "skill_name": skill_name,
            "function_name": function_name,
            "result": str(result),
            "context_variables": dict(sk_context.variables)
        }
        
    async def _run_plan(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plan using available skills."""
        planner_type = params.get("planner_type", "sequential")
        goal = params.get("goal", "")
        
        # Get planner
        planner = self.planners.get(planner_type)
        if not planner:
            raise ValueError(f"Planner not found: {planner_type}")
            
        # Create plan
        plan = await planner.create_plan_async(goal, self.kernel)
        
        # Execute plan
        sk_context = self.kernel.create_new_context()
        for key, value in context.items():
            sk_context[key] = str(value)
            
        result = await plan.invoke_async(context=sk_context)
        
        return {
            "planner_type": planner_type,
            "goal": goal,
            "plan_description": plan.description,
            "result": str(result),
            "steps_executed": len(plan.steps)
        }
        
    async def _communicate_agent(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent communication."""
        agent_id = params.get("agent_id")
        message = params.get("message", "")
        message_type = params.get("message_type", "request")
        
        # In a real implementation, this would handle actual agent communication
        # For now, we'll simulate the communication
        
        response = {
            "agent_id": agent_id,
            "message_sent": message,
            "message_type": message_type,
            "status": "sent",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Simulate different message types
        if message_type == "request":
            response["expected_response"] = "acknowledgment"
        elif message_type == "command":
            response["execution_status"] = "pending"
        elif message_type == "query":
            response["response"] = f"Mock response to query: {message}"
            
        return response
        
    async def _manage_context(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage conversation context and memory."""
        operation = params.get("operation", "get")
        context_key = params.get("key")
        context_value = params.get("value")
        
        # Create or get context
        sk_context = self.kernel.create_new_context()
        
        result = {}
        
        if operation == "set":
            sk_context[context_key] = context_value
            result["status"] = "set"
            result["key"] = context_key
            result["value"] = context_value
        elif operation == "get":
            value = sk_context.get(context_key, None)
            result["status"] = "retrieved"
            result["key"] = context_key
            result["value"] = value
        elif operation == "clear":
            sk_context.variables.clear()
            result["status"] = "cleared"
        elif operation == "list":
            result["status"] = "listed"
            result["variables"] = dict(sk_context.variables)
            
        return result
        
    async def _register_builtin_skills(self) -> None:
        """Register built-in semantic skills."""
        # Create a simple math skill
        math_skill = self.kernel.create_semantic_skill(
            "Math",
            {
                "Add": {
                    "description": "Add two numbers",
                    "prompt": "Add {{$number1}} and {{$number2}}",
                    "max_tokens": 10
                },
                "Multiply": {
                    "description": "Multiply two numbers",
                    "prompt": "Multiply {{$number1}} by {{$number2}}",
                    "max_tokens": 10
                }
            }
        )
        self.skills["Math"] = math_skill
        
        # Create a text processing skill
        text_skill = self.kernel.create_semantic_skill(
            "Text",
            {
                "Summarize": {
                    "description": "Summarize text",
                    "prompt": "Summarize the following text: {{$input}}",
                    "max_tokens": 100
                },
                "ExtractKeywords": {
                    "description": "Extract keywords from text",
                    "prompt": "Extract keywords from: {{$input}}",
                    "max_tokens": 50
                }
            }
        )
        self.skills["Text"] = text_skill
        
        # Register native function skill
        class BusinessLogicSkill:
            @sk_function(
                description="Process business data",
                name="ProcessData"
            )
            @sk_function_context_parameter(
                name="data",
                description="Data to process"
            )
            async def process_data(self, context: sk.SKContext) -> str:
                data = context.get("data", "")
                # Simple processing for demonstration
                return f"Processed: {data.upper()}"
                
        business_skill = BusinessLogicSkill()
        self.kernel.import_skill(business_skill, "BusinessLogic")
        self.skills["BusinessLogic"] = business_skill
        
    def register_skill(self, skill_name: str, skill: Any) -> None:
        """Register a custom skill."""
        self.kernel.import_skill(skill, skill_name)
        self.skills[skill_name] = skill
        logger.info(f"Registered skill: {skill_name}")
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Semantic Kernel adapter."""
        health_status = await super().health_check()
        
        # Add Semantic Kernel-specific metrics
        health_status.update({
            "kernel_initialized": self.kernel is not None,
            "skills_registered": len(self.skills),
            "planners_available": list(self.planners.keys()),
            "memory_stores": 0  # Would be actual count in production
        })
        
        return health_status