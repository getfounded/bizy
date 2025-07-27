# Bizy Community Packages

This directory contains ecosystem contributions that extend Bizy's capabilities to work seamlessly with popular AI frameworks and tools.

## Overview

Bizy follows an "ecosystem contribution" strategy, providing business logic coordination that transforms individual framework capabilities into sophisticated enterprise solutions. Each package here is designed to be contributed back to its respective community.

## Available Packages

### 🔗 LangChain Integration
- **Directory**: `langchain/`
- **Purpose**: Provides LangChain-compatible components for business rule integration
- **Features**:
  - Custom chains for business rule evaluation
  - LangGraph nodes for cross-framework coordination
  - Example notebooks demonstrating business logic patterns

### ⚙️ Temporal Workflows
- **Directory**: `temporal/`
- **Purpose**: Temporal activities and workflows for business process automation
- **Features**:
  - Activities for business rule execution
  - Workflow patterns for AI agent coordination
  - Error handling patterns for framework failures

### 🚀 FastMCP Extensions
- **Directory**: `fastmcp/`
- **Purpose**: Enhancements for FastMCP with business context awareness
- **Features**:
  - Business context metadata extensions
  - Tool transformation patterns
  - Performance optimization examples

### 🥒 Behave AI Orchestration
- **Directory**: `behave-ai-orchestration/`
- **Purpose**: BDD testing framework for AI orchestration scenarios
- **Features**:
  - Step definitions for AI framework testing
  - Multi-framework coordination scenarios
  - Business-readable test specifications

### 🥒 Cucumber AI Orchestration
- **Directory**: `cucumber-ai-orchestration/`
- **Purpose**: Cucumber.js implementation for AI orchestration testing
- **Features**:
  - JavaScript/TypeScript step definitions
  - Cross-framework test scenarios
  - Enterprise integration patterns

## Contributing

Each package follows the contribution guidelines of its target community:

1. **Code Style**: Follow the target framework's coding standards
2. **Documentation**: Include comprehensive examples and API documentation
3. **Testing**: Provide thorough test coverage
4. **Examples**: Include practical business scenarios

## Installation

Individual packages can be installed separately:

```bash
# For LangChain integration
cd community_packages/langchain
pip install -e .

# For Temporal workflows
cd community_packages/temporal
pip install -e .

# For Behave AI Orchestration
cd community_packages/behave-ai-orchestration
pip install -e .
```

## Business Value

These packages demonstrate how Bizy enables:
- 🔄 Seamless coordination between different AI frameworks
- 📋 Business rule execution across technology boundaries
- 🛡️ Enterprise-grade error handling and recovery
- 📊 Unified monitoring and observability
- 🚀 Improved development velocity through reusable patterns

## License

All community packages are released under the MIT License to ensure maximum compatibility with their target ecosystems.