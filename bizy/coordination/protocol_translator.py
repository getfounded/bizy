"""
Protocol Translator: Converts between different framework communication protocols.

This module handles the translation of messages, data formats, and communication
patterns between different AI frameworks.
"""

from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
import json
import logging
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)


class MessageFormat(str, Enum):
    """Supported message formats for inter-framework communication."""
    JSON = "json"
    PROTOBUF = "protobuf"
    MSGPACK = "msgpack"
    XML = "xml"
    YAML = "yaml"
    BINARY = "binary"


class ProtocolType(str, Enum):
    """Types of communication protocols."""
    REST = "rest"
    GRPC = "grpc"
    WEBSOCKET = "websocket"
    MQTT = "mqtt"
    AMQP = "amqp"
    NATIVE = "native"


class MessageTranslator(ABC):
    """Abstract base class for message format translators."""
    
    @abstractmethod
    async def translate(self, data: Any, from_format: MessageFormat, to_format: MessageFormat) -> Any:
        """Translate data between formats."""
        pass
        
    @abstractmethod
    def supports_format(self, format: MessageFormat) -> bool:
        """Check if translator supports a format."""
        pass


class ProtocolTranslator:
    """
    Translates messages and protocols between different AI frameworks.
    
    Handles:
    - Message format conversion
    - Protocol adaptation
    - Data structure mapping
    - Error format standardization
    """
    
    def __init__(self):
        self.format_translators: Dict[str, MessageTranslator] = {}
        self.protocol_adapters: Dict[str, Any] = {}
        self.schema_mappings: Dict[str, Dict[str, Any]] = {}
        self._initialize_translators()
        
    def _initialize_translators(self):
        """Initialize built-in format translators."""
        # JSON translator (default)
        self.format_translators["json"] = JSONTranslator()
        
        # Register protocol adapters
        self.protocol_adapters = {
            ProtocolType.REST: RESTAdapter(),
            ProtocolType.GRPC: GRPCAdapter(),
            ProtocolType.WEBSOCKET: WebSocketAdapter(),
            ProtocolType.NATIVE: NativeAdapter()
        }
        
    async def translate_message(
        self,
        message: Any,
        source_framework: str,
        target_framework: str,
        source_format: MessageFormat = MessageFormat.JSON,
        target_format: MessageFormat = MessageFormat.JSON
    ) -> Any:
        """
        Translate a message between frameworks.
        
        Args:
            message: The message to translate
            source_framework: Source framework name
            target_framework: Target framework name
            source_format: Source message format
            target_format: Target message format
            
        Returns:
            Translated message
        """
        # First, normalize to common format
        normalized = await self._normalize_message(message, source_framework, source_format)
        
        # Apply schema mapping if available
        if self._has_schema_mapping(source_framework, target_framework):
            normalized = await self._apply_schema_mapping(
                normalized, source_framework, target_framework
            )
            
        # Convert to target format
        translated = await self._denormalize_message(normalized, target_framework, target_format)
        
        return translated
        
    async def _normalize_message(self, message: Any, framework: str, format: MessageFormat) -> Dict[str, Any]:
        """Normalize message to common internal format."""
        # Convert to dict if necessary
        if format != MessageFormat.JSON:
            translator = self.format_translators.get(format.value)
            if translator:
                message = await translator.translate(message, format, MessageFormat.JSON)
                
        # Apply framework-specific normalization
        normalized = {
            "metadata": {
                "source_framework": framework,
                "timestamp": asyncio.get_event_loop().time(),
                "message_id": self._generate_message_id()
            },
            "payload": message
        }
        
        # Framework-specific normalization
        if framework == "langchain":
            normalized = self._normalize_langchain_message(normalized)
        elif framework == "temporal":
            normalized = self._normalize_temporal_message(normalized)
        elif framework == "mcp":
            normalized = self._normalize_mcp_message(normalized)
            
        return normalized
        
    async def _denormalize_message(self, message: Dict[str, Any], framework: str, format: MessageFormat) -> Any:
        """Convert from common format to framework-specific format."""
        # Apply framework-specific denormalization
        if framework == "langchain":
            denormalized = self._denormalize_langchain_message(message)
        elif framework == "temporal":
            denormalized = self._denormalize_temporal_message(message)
        elif framework == "mcp":
            denormalized = self._denormalize_mcp_message(message)
        else:
            denormalized = message.get("payload", message)
            
        # Convert to target format
        if format != MessageFormat.JSON:
            translator = self.format_translators.get(format.value)
            if translator:
                denormalized = await translator.translate(
                    denormalized, MessageFormat.JSON, format
                )
                
        return denormalized
        
    def _normalize_langchain_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize LangChain-specific message format."""
        payload = message.get("payload", {})
        
        # Extract LangChain-specific fields
        if isinstance(payload, dict):
            if "messages" in payload:
                # Chat message format
                message["type"] = "chat"
                message["content"] = payload["messages"]
            elif "input" in payload:
                # Chain input format
                message["type"] = "chain"
                message["content"] = payload["input"]
            elif "tool_calls" in payload:
                # Tool call format
                message["type"] = "tool_call"
                message["content"] = payload["tool_calls"]
                
        return message
        
    def _denormalize_langchain_message(self, message: Dict[str, Any]) -> Any:
        """Convert to LangChain-specific format."""
        msg_type = message.get("type", "generic")
        content = message.get("content", message.get("payload"))
        
        if msg_type == "chat":
            return {"messages": content}
        elif msg_type == "chain":
            return {"input": content}
        elif msg_type == "tool_call":
            return {"tool_calls": content}
        else:
            return content
            
    def _normalize_temporal_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Temporal-specific message format."""
        payload = message.get("payload", {})
        
        if isinstance(payload, dict):
            if "workflowId" in payload:
                message["type"] = "workflow"
                message["workflow_id"] = payload["workflowId"]
            elif "activityId" in payload:
                message["type"] = "activity"
                message["activity_id"] = payload["activityId"]
            elif "signal" in payload:
                message["type"] = "signal"
                message["signal_name"] = payload["signal"]
                
        return message
        
    def _denormalize_temporal_message(self, message: Dict[str, Any]) -> Any:
        """Convert to Temporal-specific format."""
        msg_type = message.get("type", "generic")
        
        if msg_type == "workflow":
            return {
                "workflowId": message.get("workflow_id"),
                "parameters": message.get("payload", {})
            }
        elif msg_type == "signal":
            return {
                "signal": message.get("signal_name"),
                "data": message.get("payload", {})
            }
        else:
            return message.get("payload", {})
            
    def _normalize_mcp_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MCP-specific message format."""
        payload = message.get("payload", {})
        
        if isinstance(payload, dict):
            if "tool" in payload:
                message["type"] = "tool_execution"
                message["tool_name"] = payload["tool"]
            elif "resource" in payload:
                message["type"] = "resource_access"
                message["resource_name"] = payload["resource"]
                
        return message
        
    def _denormalize_mcp_message(self, message: Dict[str, Any]) -> Any:
        """Convert to MCP-specific format."""
        msg_type = message.get("type", "generic")
        
        if msg_type == "tool_execution":
            return {
                "tool": message.get("tool_name"),
                "parameters": message.get("payload", {})
            }
        elif msg_type == "resource_access":
            return {
                "resource": message.get("resource_name"),
                "operation": message.get("payload", {})
            }
        else:
            return message.get("payload", {})
            
    async def translate_protocol(
        self,
        request: Any,
        source_protocol: ProtocolType,
        target_protocol: ProtocolType
    ) -> Any:
        """
        Translate between different communication protocols.
        
        Args:
            request: The request to translate
            source_protocol: Source protocol type
            target_protocol: Target protocol type
            
        Returns:
            Translated request
        """
        # Get protocol adapters
        source_adapter = self.protocol_adapters.get(source_protocol)
        target_adapter = self.protocol_adapters.get(target_protocol)
        
        if not source_adapter or not target_adapter:
            raise ValueError(f"Unsupported protocol translation: {source_protocol} -> {target_protocol}")
            
        # Extract data from source protocol
        data = await source_adapter.extract(request)
        
        # Convert to target protocol
        translated = await target_adapter.construct(data)
        
        return translated
        
    def register_schema_mapping(
        self,
        source_framework: str,
        target_framework: str,
        mapping: Dict[str, Any]
    ):
        """Register a schema mapping between frameworks."""
        key = f"{source_framework}->{target_framework}"
        self.schema_mappings[key] = mapping
        
    def _has_schema_mapping(self, source: str, target: str) -> bool:
        """Check if schema mapping exists."""
        key = f"{source}->{target}"
        return key in self.schema_mappings
        
    async def _apply_schema_mapping(
        self,
        data: Dict[str, Any],
        source: str,
        target: str
    ) -> Dict[str, Any]:
        """Apply schema mapping to data."""
        key = f"{source}->{target}"
        mapping = self.schema_mappings.get(key, {})
        
        # Apply field mappings
        mapped_data = {}
        for source_field, target_field in mapping.get("fields", {}).items():
            if source_field in data:
                mapped_data[target_field] = data[source_field]
                
        # Apply transformations
        for transform in mapping.get("transformations", []):
            field = transform.get("field")
            func = transform.get("function")
            if field in mapped_data and callable(func):
                mapped_data[field] = func(mapped_data[field])
                
        return mapped_data
        
    def _generate_message_id(self) -> str:
        """Generate unique message ID."""
        import uuid
        return str(uuid.uuid4())
        
    async def translate_error(
        self,
        error: Any,
        source_framework: str,
        target_framework: str
    ) -> Any:
        """Translate error formats between frameworks."""
        # Normalize error to common format
        normalized_error = {
            "error": True,
            "source": source_framework,
            "type": type(error).__name__,
            "message": str(error),
            "details": {}
        }
        
        # Extract framework-specific error details
        if source_framework == "langchain" and hasattr(error, "llm_output"):
            normalized_error["details"]["llm_output"] = error.llm_output
        elif source_framework == "temporal" and hasattr(error, "workflow_id"):
            normalized_error["details"]["workflow_id"] = error.workflow_id
            
        # Convert to target framework error format
        if target_framework == "langchain":
            from langchain.schema import OutputParserException
            return OutputParserException(normalized_error["message"])
        elif target_framework == "temporal":
            from temporalio.exceptions import WorkflowException
            return WorkflowException(normalized_error["message"])
        else:
            return Exception(normalized_error["message"])


class JSONTranslator(MessageTranslator):
    """Translator for JSON message format."""
    
    async def translate(self, data: Any, from_format: MessageFormat, to_format: MessageFormat) -> Any:
        """Translate between JSON and other formats."""
        if from_format == MessageFormat.JSON and to_format == MessageFormat.JSON:
            return data
            
        if from_format == MessageFormat.JSON:
            # Convert from JSON to other format
            if to_format == MessageFormat.YAML:
                import yaml
                return yaml.dump(data)
            elif to_format == MessageFormat.XML:
                # Simple XML conversion
                return self._dict_to_xml(data)
        else:
            # Convert from other format to JSON
            if from_format == MessageFormat.YAML:
                import yaml
                return yaml.safe_load(data)
            elif from_format == MessageFormat.XML:
                # Simple XML parsing
                return self._xml_to_dict(data)
                
        return data
        
    def supports_format(self, format: MessageFormat) -> bool:
        """Check if format is supported."""
        return format in [MessageFormat.JSON, MessageFormat.YAML, MessageFormat.XML]
        
    def _dict_to_xml(self, data: Dict[str, Any], root: str = "root") -> str:
        """Convert dictionary to XML string."""
        # Simplified XML conversion
        xml = f"<{root}>"
        for key, value in data.items():
            if isinstance(value, dict):
                xml += self._dict_to_xml(value, key)
            else:
                xml += f"<{key}>{value}</{key}>"
        xml += f"</{root}>"
        return xml
        
    def _xml_to_dict(self, xml_string: str) -> Dict[str, Any]:
        """Convert XML string to dictionary."""
        # Simplified XML parsing - would use proper XML parser in production
        return {"xml_data": xml_string}


class ProtocolAdapter(ABC):
    """Abstract base class for protocol adapters."""
    
    @abstractmethod
    async def extract(self, request: Any) -> Dict[str, Any]:
        """Extract data from protocol-specific request."""
        pass
        
    @abstractmethod
    async def construct(self, data: Dict[str, Any]) -> Any:
        """Construct protocol-specific request from data."""
        pass


class RESTAdapter(ProtocolAdapter):
    """Adapter for REST protocol."""
    
    async def extract(self, request: Any) -> Dict[str, Any]:
        """Extract data from REST request."""
        return {
            "method": request.get("method", "POST"),
            "path": request.get("path", "/"),
            "headers": request.get("headers", {}),
            "body": request.get("body", {})
        }
        
    async def construct(self, data: Dict[str, Any]) -> Any:
        """Construct REST request from data."""
        return {
            "method": data.get("method", "POST"),
            "path": data.get("path", "/"),
            "headers": data.get("headers", {}),
            "body": data.get("body", {})
        }


class GRPCAdapter(ProtocolAdapter):
    """Adapter for gRPC protocol."""
    
    async def extract(self, request: Any) -> Dict[str, Any]:
        """Extract data from gRPC request."""
        return {
            "service": request.get("service"),
            "method": request.get("method"),
            "message": request.get("message", {})
        }
        
    async def construct(self, data: Dict[str, Any]) -> Any:
        """Construct gRPC request from data."""
        return {
            "service": data.get("service"),
            "method": data.get("method"),
            "message": data.get("message", {})
        }


class WebSocketAdapter(ProtocolAdapter):
    """Adapter for WebSocket protocol."""
    
    async def extract(self, request: Any) -> Dict[str, Any]:
        """Extract data from WebSocket message."""
        return {
            "type": request.get("type", "message"),
            "data": request.get("data", {})
        }
        
    async def construct(self, data: Dict[str, Any]) -> Any:
        """Construct WebSocket message from data."""
        return {
            "type": data.get("type", "message"),
            "data": data.get("data", {})
        }


class NativeAdapter(ProtocolAdapter):
    """Adapter for native Python protocol."""
    
    async def extract(self, request: Any) -> Dict[str, Any]:
        """Extract data from native request."""
        return {"data": request}
        
    async def construct(self, data: Dict[str, Any]) -> Any:
        """Construct native request from data."""
        return data.get("data", data)