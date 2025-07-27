---
sidebar_position: 1
---

# Installation

Get Bizy up and running in your environment.

## Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)
- Redis (for event bus)
- Git

## Install with Poetry

```bash
# Clone the repository
git clone https://github.com/getfounded/bizy.git
cd bizy

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

## Install with pip

```bash
pip install bizy
```

## Verify Installation

```python
import bizy
print(bizy.__version__)
# Output: 0.1.0
```

## Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# LangChain Configuration
LANGCHAIN_API_KEY=your-api-key
LANGCHAIN_MODEL=gpt-4

# Temporal Configuration
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Next Steps

- Follow the [Quick Start](./quick-start) guide
- Create your [First Workflow](./first-workflow)