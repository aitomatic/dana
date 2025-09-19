# Dana Studio User Guide

Welcome to Dana Studio - your comprehensive platform for building, training, and deploying intelligent AI agents. This guide will walk you through everything you need to know to get started and make the most of Dana Studio's powerful features.

## Getting Started

### Prerequisites
- Python 3.7 or higher installed on your system
- Basic familiarity with command-line operations

### Installation & Setup

1. **Navigate to your desired directory**
   ```bash
   cd /path/to/your/preferred/location
   ```

2. **Set up a virtual environment (recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dana Studio**
   ```bash
   pip install dana
   ```

4. **Configure API providers**
   ```bash
   dana config
   ```
   - Select at least one AI provider (OpenAI, Anthropic, etc.)
   - Provide the corresponding API key when prompted
   - Your API keys are stored securely and locally

5. **Launch Dana Studio**
   ```bash
   dana start
   ```
   Open your browser and navigate to `http://127.0.0.1:8080/`

## Training Your Agent

Dana Studio offers multiple pathways to create powerful, specialized AI agents tailored to your needs.

### Pre-trained Agents

Dana Studio comes with 4 ready-to-use pre-trained agents, each equipped with specialized knowledge and workflows:

- Browse the available pre-trained agents in the main dashboard
- Click "Save to my agents and use" to add an agent to your collection
- Each agent is designed for specific domains and can be used immediately

### Custom Agent Training

#### Starting from a Pre-trained Agent

1. **Select a base agent**: Choose a pre-trained agent that closely matches your intended use case
2. **Click "Train from this agent"**: This creates a customizable copy you can modify
3. **Example**: Try training Jordan, the Financial Analysis Expert, for your specific financial analysis needs

#### Working with Dana (Agent Builder Assistant)

Dana is your AI-powered assistant that helps gather and organize knowledge for your target agent:

1. **Start a conversation with Dana**: Describe your intended agent's purpose
2. **Provide specifics**: Share details about:
   - Domain expertise needed
   - Specific topics to cover
   - Tasks the agent should excel at
   - Job descriptions or role requirements
3. **Iterative refinement**: Dana will ask clarifying questions to better understand your needs

#### Understanding the Knowledge Graph

The Knowledge Graph is a visual representation of your agent's knowledge structure:

- **Real-time updates**: Watch the graph evolve as Dana builds knowledge
- **Interactive exploration**: Click any node to view detailed content
- **Knowledge connections**: See how different concepts relate to each other
- **Quality assurance**: Review and validate the knowledge structure before finalizing

#### Document Management

Enhance your agent's capabilities by providing relevant documents:

1. **Access Resources**: Navigate to your agent's Resources section
2. **Add documents**: Use "Add file from library" to select relevant files
3. **Library integration**: All documents must first be processed in the Library

**Important**: For optimal results, use the "Deep Extract" feature in the Library before adding documents to your agent. This feature is only available in the Library section and provides enhanced information extraction for better retrieval accuracy.

#### Agent Code Customization

For advanced users, Dana Studio allows direct code modification:

- Access your agent's underlying code
- Customize behavior, responses, and workflows
- Implement specific business logic or integrations
- Test changes in real-time

## Using Your Agent

### Activation Modes

**Option 1: Direct Use Mode**
- Select "Use mode" from your agent's dashboard
- Immediate access to chat interface

**Option 2: Agent List**
- Navigate to "My Agents"
- Click "Use agent" next to your desired agent

### Chat Interface

The chat window is your primary interaction point with your agent:

- **Natural conversation**: Ask questions in plain language
- **Task assignment**: Give your agent specific tasks to complete
- **Document attachment**: Upload files directly to the chat for context-aware responses
- **Multi-turn conversations**: Build complex discussions over multiple exchanges

### Best Practices for Agent Interaction

- Be specific in your requests
- Provide context when needed
- Use document attachments for reference-heavy tasks
- Take advantage of your agent's specialized knowledge domain

## Library: Your Knowledge Repository

The Library serves as the central hub for all document management in Dana Studio.

### Document Processing

**Standard Extract (Default)**
- Automatic processing when documents are uploaded
- Suitable for general use cases
- Faster processing time

**Deep Extract (Recommended for Precision)**
- Enhanced information extraction
- Improved retrieval accuracy
- Longer processing time
- **Available only in Library** - must be activated before adding documents to agents

### Library Management

1. **Upload documents**: Add files to your central repository
2. **Choose extraction mode**: Select Standard or Deep Extract based on your needs
3. **Monitor processing**: Track extraction progress
4. **Organize content**: Manage your document collection efficiently

## Tips for Success

### Agent Training Best Practices

- Start with clear objectives for your agent's role
- Provide comprehensive domain information to Dana
- Review the Knowledge Graph regularly during training
- Test your agent frequently during the development process

### Document Optimization

- Use Deep Extract for critical business documents
- Organize files logically in your Library
- Regularly update your document collection
- Remove outdated or irrelevant materials

### Performance Optimization

- Keep your Knowledge Graph focused and relevant
- Avoid information overload - quality over quantity
- Regular agent testing and refinement
- Monitor chat performance and user feedback

## Troubleshooting

### Common Issues

**Installation Problems**
- Ensure Python 3.7+ is installed
- Check your internet connection during pip install
- Verify virtual environment activation

**Configuration Issues**
- Double-check API key validity
- Ensure at least one provider is selected
- Restart Dana Studio after configuration changes

**Agent Performance**
- Review Knowledge Graph for accuracy
- Check document processing status in Library
- Consider using Deep Extract for better results

### Getting Help

- Check the in-app help documentation
- Review error messages carefully
- Ensure all prerequisites are met
- Contact support for persistent issues

## Next Steps

Now that you understand the basics of Dana Studio, you're ready to:

1. Create your first custom agent
2. Upload and process your business documents
3. Train agents for specific use cases
4. Deploy agents for your team or organization

Welcome to the future of intelligent AI assistance with Dana Studio!