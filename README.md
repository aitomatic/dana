<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Prototype

A prototype implementation of DXA (Domain-Expert Agents) - an AI-powered system for domain-specific expert agents.

For detailed architecture documentation (Product-Engineering perspective), see [DXA Architecture](dxa/README.md). For usage examples (AI Solution Engineering perspective), check out our [Examples](examples/README.md).

## Prerequisites

- Python 3.x
- bash shell (for Unix-based systems) or Git Bash (for Windows)

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd dxa-prototype
   ```

2. Set up the virtual environment:
   ```bash
   bash setup_env.sh
   source venv/bin/activate  # On Windows: source venv/Scripts/activate
   ```

3. Configure the environment:
   - Copy `.env.example` to `.env` (if not already done)
   - Update the values in `.env` with your configuration

4. Run the application:
   ```bash
   python dxa-poc.py
   ```

## Configuration

The application requires the following configuration:
- Environment variables in `.env` file
- API key configuration in the main Python file

## Notes

- Make sure all dependencies are properly installed before running the application
- For any issues, please check the troubleshooting section or contact the development team

## About DXA

Domain-Expert Agents (DXA) is a system designed to create and manage AI agents that specialize in specific domains or areas of expertise. These agents can provide domain-specific knowledge, answer questions, and assist with tasks within their area of specialization.

## Contributing

DXA is proprietary software developed by Aitomatic, Inc. Contributions are limited to authorized Aitomatic employees and contractors. If you're an authorized contributor:

1. Please ensure you have signed the necessary Confidentiality and IP agreements
2. Follow the internal development guidelines
3. Submit your changes through the company's approved development workflow
4. Contact the project maintainers for access to the internal Contributing Guide

For external users or organizations interested in collaborating with Aitomatic on DXA development, please contact our business development team.

## License

This software is proprietary and confidential. Copyright © 2024 Aitomatic, Inc. All rights reserved.

Unauthorized copying, transfer, or reproduction of this software, via any medium, is strictly prohibited. This software is protected by copyright law and international treaties.