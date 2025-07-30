[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/getfounded-bizy-badge.png)](https://mseep.ai/app/getfounded-bizy)

# Bizy
The business logic orchestration layer for AI agents. Works with MCP, A2A, Temporal, Langchain, Mem0, Crew AI, Semantic Kernel, Graphiti, Zep AI, and Fast MCP 2.0.

## Why Bizy?

Bizy takes out the busy work for both developers and business stakeholders. Start somewhere rather than nowhere. 

Bizy recognizes that many developers and engineers have now become implementers alongside consultants. Bizy empowers both the developers and the implementors to focus on their stakeholders. Bizy handle >80% of the initial business rules and logic required for developing any business/enterprise level AI agent or application. 

## Strategic Approach

This project follows an "ecosystem contribution" strategy, enhancing existing AI frameworks rather than competing with them. The orchestration layer provides business logic coordination that transforms individual framework capabilities into sophisticated enterprise solutions.

## Quick Start

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Start development server
poetry run python -m bizy.main
```

## Architecture

Bizy consists of several key components:

- **Meta-Orchestrator**: Core coordination engine that translates business rules across frameworks
- **Framework Adapters**: Integration adapters for each supported framework
- **Event System**: Cross-framework communication and coordination
- **Business Rules Engine**: Domain-specific language for business logic definition

## Supported Frameworks

- **LangChain**: Chain-based AI workflows and LangGraph orchestration
- **Semantic Kernel**: Microsoft's agent communication and process frameworks
- **Anthropic MCP**: Model Context Protocol for tool and resource coordination
- **Temporal**: Reliable workflow orchestration and process automation
- **FastMCP**: High-performance MCP implementations and tool coordination
- **Zep AI**: Memory systems and temporal knowledge graphs

## Contributing

We welcome contributions that enhance cross-framework business logic coordination. Please see our contribution guidelines in `/docs/community/contributing.md`.

## Documentation

📚 Visit [docs.bizy.work](https://docs.bizy.work) for comprehensive documentation.

## Resources

- 🌐 **Website**: [bizy.work](https://bizy.work)
- 📖 **Documentation**: [docs.bizy.work](https://docs.bizy.work)
- 💻 **GitHub**: [github.com/getfounded/bizy](https://github.com/getfounded/bizy)
- 🐦 **Twitter**: [@bizywork](https://twitter.com/bizywork)

## License

MIT License - see [LICENSE](LICENSE) for details.
