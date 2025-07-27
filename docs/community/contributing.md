# Contributing to Business Logic Orchestrator

Thank you for your interest in contributing to the Business Logic Orchestrator project! This guide will help you get started with contributing code, documentation, and ideas.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](./code_of_conduct.md). Please read it to understand the standards we expect from our community.

## How Can You Contribute?

### 1. Framework Adapters
Create adapters for new AI frameworks:
- Implement the `FrameworkAdapter` interface
- Add connection management and health checking
- Write comprehensive tests
- Document the adapter's capabilities

### 2. Business Rule Patterns
Share reusable business rule patterns:
- Document common use cases
- Provide example YAML configurations
- Include test scenarios
- Explain best practices

### 3. Documentation
Improve our documentation:
- Fix typos and clarify explanations
- Add examples and tutorials
- Translate documentation
- Create video tutorials

### 4. Testing
Enhance our test coverage:
- Write unit tests for new features
- Add integration tests
- Create performance benchmarks
- Report bugs with reproducible examples

### 5. Community Support
Help other users:
- Answer questions on Discord
- Review pull requests
- Share your use cases
- Write blog posts

## Development Setup

### Prerequisites
- Python 3.12+
- Poetry for dependency management
- Redis for local testing
- Git for version control

### Setting Up Your Environment

1. Fork the repository on GitHub

2. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/business-logic-orchestrator.git
cd business-logic-orchestrator
```

3. Add upstream remote:
```bash
git remote add upstream https://github.com/business-logic-orchestrator/orchestrator.git
```

4. Install dependencies:
```bash
poetry install
```

5. Set up pre-commit hooks:
```bash
pre-commit install
```

6. Run tests to verify setup:
```bash
pytest
```

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Write clean, documented code
- Follow our coding standards
- Add tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks
```bash
# Format code
black .
isort .

# Type checking
mypy business_logic_orchestrator

# Run tests
pytest

# Check coverage
pytest --cov=business_logic_orchestrator
```

### 4. Commit Your Changes
```bash
git add .
git commit -m "feat: add support for new framework X"
```

Follow our commit message conventions:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `style:` Code style changes
- `perf:` Performance improvements

### 5. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Pull Request Guidelines

### Before Submitting
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] PR description explains changes

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## Coding Standards

### Python Style
We use Black and isort for code formatting:

```python
# Good
from typing import Any, Dict, List

from business_logic_orchestrator.core import MetaOrchestrator
from business_logic_orchestrator.adapters import FrameworkAdapter


class MyAdapter(FrameworkAdapter):
    """Adapter for integrating with MyFramework."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize adapter with configuration."""
        super().__init__(config)
        self.client = self._create_client()
    
    async def execute_action(
        self,
        action: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an action on the framework."""
        # Implementation
        pass
```

### Documentation
Use Google-style docstrings:

```python
def calculate_risk_score(
    transaction: Dict[str, Any],
    rules: List[BusinessRule]
) -> float:
    """Calculate risk score for a transaction.
    
    Args:
        transaction: Transaction data including amount, merchant, etc.
        rules: List of business rules to evaluate.
        
    Returns:
        Risk score between 0.0 and 1.0.
        
    Raises:
        ValueError: If transaction data is invalid.
    """
```

### Testing
Write comprehensive tests:

```python
import pytest
from business_logic_orchestrator import MetaOrchestrator


class TestOrchestrator:
    """Test cases for MetaOrchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return MetaOrchestrator()
    
    def test_rule_evaluation(self, orchestrator):
        """Test basic rule evaluation."""
        # Arrange
        rule = create_test_rule()
        context = {"value": 100}
        
        # Act
        result = orchestrator.evaluate_rule(rule, context)
        
        # Assert
        assert result["decision"] == "approve"
        assert result["confidence"] > 0.8
```

## Framework Adapter Development

### Adapter Interface
All adapters must implement:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict


class FrameworkAdapter(ABC):
    """Base class for framework adapters."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to framework."""
        pass
    
    @abstractmethod
    async def execute_action(
        self,
        action: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute action on framework."""
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """Check framework health status."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close framework connection."""
        pass
```

### Adapter Guidelines
1. Handle all framework-specific errors
2. Implement retry logic for transient failures
3. Provide meaningful error messages
4. Support async operations
5. Include comprehensive logging

## Release Process

### Version Numbering
We follow Semantic Versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Checklist
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite
4. Create release PR
5. Tag release after merge
6. Publish to PyPI

## Getting Help

### Resources
- [Discord Community](https://discord.gg/orchestrator)
- [GitHub Discussions](https://github.com/business-logic-orchestrator/orchestrator/discussions)
- [Documentation](https://docs.business-logic-orchestrator.io)

### Asking Questions
When asking for help:
1. Search existing issues/discussions first
2. Provide minimal reproducible example
3. Include error messages and logs
4. Describe expected vs actual behavior

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation
- Community spotlights

Thank you for contributing to Business Logic Orchestrator!