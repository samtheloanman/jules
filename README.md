# Jules

A proactive AI automation layer mapping GitHub events to the Jules API.

## Overview
Jules bridges the reactive gap between standard GitHub repositories and the native intelligence of the Jules REST API. Instead of relying on manual reviews or complex pipelines, this project utilizes a custom serverless edge proxy (deployed on Cloudflare Workers) that listens to GitHub repository Webhooks and instantly queues relevant Pull Requests for an AI audit.

## Features
- **Serverless Automation**: Written natively for Cloudflare Workers, ensuring cost-efficient (or zero-cost) scaling across thousands of payload runs.
- **Deduplication Checkers**: Prevent cyclic API waste; the codebase checks existing GitHub check runs and commit statuses before executing any Jules prompts. 
- **Targeted Operations**: Natively utilizes `jules:test`, `jules:doc` and `jules:review` Github Labels to narrow context windows avoiding hallucination loops.
- **Python Companion**: Integrated Python wrappers (`dispatcher.py`, `jules_helper.py`) intended to orchestrate the internal logic for fetching history or debugging sessions securely.

## Docs
See the full set of documentation to dig deeper:
- [Architecture](docs/ARCHITECTURE.md)
- [Getting Started](docs/GETTING-STARTED.md)
- [Development](docs/DEVELOPMENT.md)
- [Testing](docs/TESTING.md)
- [Configuration](docs/CONFIGURATION.md)
