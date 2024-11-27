# DXA Prototype

A prototype implementation of DXA (Domain-Expert Agents) - an AI-powered system for domain-specific expert agents.

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
- For any issues, please check the troubleshooting section or create an issue

## About DXA

Domain-Expert Agents (DXA) is a system designed to create and manage AI agents that specialize in specific domains or areas of expertise. These agents can provide domain-specific knowledge, answer questions, and assist with tasks within their area of specialization.