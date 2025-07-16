"""
Utility functions for agent generation and related server logic.
"""


def generate_mock_agent_code(messages, current_code=""):
    """
    Generate mock Dana agent code based on user requirements for testing or mock mode.
    Args:
        messages: List of conversation messages
        current_code: Current Dana code to improve upon (default empty string)
    Returns:
        Mock Dana agent code as a string
    """
    # Extract requirements from messages
    all_content = ""
    for msg in messages:
        if msg.get("role") == "user":
            all_content = all_content + " " + msg.get("content", "")
    requirements_lower = all_content.lower()

    # Simple keyword-based agent generation
    if "weather" in requirements_lower:
        # Weather agents don't typically need RAG - they can use general knowledge
        return '''"""Weather information agent."""

# Agent Card declaration
agent WeatherAgent:
    name : str = "Weather Information Agent"
    description : str = "Provides weather information and recommendations"
    resources : list = []

# Agent's problem solver
def solve(weather_agent : WeatherAgent, problem : str):
    return reason(f"Get weather information for: {{problem}}")'''
    elif "help" in requirements_lower or "assistant" in requirements_lower:
        return '''"""General assistant agent."""

# Agent Card declaration
agent AssistantAgent:
    name : str = "General Assistant Agent"
    description : str = "A helpful assistant that can answer questions and provide guidance"
    resources : list = []

# Agent's problem solver
def solve(assistant_agent : AssistantAgent, problem : str):
    return reason(f"I'm here to help! Let me assist you with: {{problem}}")'''
    elif "data" in requirements_lower or "analysis" in requirements_lower:
        # Data analysis might need RAG for statistical methods and guides
        return '''"""Data analysis agent."""

# Agent resources for data analysis knowledge
data_knowledge = use("rag", sources=["data_analysis_guide.md", "statistical_methods.pdf"])

# Agent Card declaration
agent DataAgent:
    name : str = "Data Analysis Agent"
    description : str = "Analyzes data and provides insights using knowledge base"
    resources : list = [data_knowledge]

# Agent's problem solver
def solve(data_agent : DataAgent, problem : str):
    return reason(f"Analyze this data and provide insights: {{problem}}", resources=data_agent.resources)'''
    elif "document" in requirements_lower or "file" in requirements_lower or "pdf" in requirements_lower:
        # Document processing definitely needs RAG
        return '''"""Document processing agent."""

# Agent resources for document processing
document_knowledge = use("rag", sources=["document_processing_guide.md", "file_formats.pdf"])

# Agent Card declaration
agent DocumentAgent:
    name : str = "Document Processing Agent"
    description : str = "Processes and analyzes documents and files"
    resources : list = [document_knowledge]

# Agent's problem solver
def solve(document_agent : DocumentAgent, problem : str):
    return reason(f"Help me process this document: {{problem}}", resources=document_agent.resources)'''
    elif "email" in requirements_lower:
        # Email agents need RAG for email templates and best practices
        return '''"""Email assistant agent."""

# Agent resources for email knowledge
email_knowledge = use("rag", sources=["email_templates.md", "communication_best_practices.pdf"])

# Agent Card declaration
agent EmailAgent:
    name : str = "Email Assistant Agent"
    description : str = "Assists with email composition and communication"
    resources : list = [email_knowledge]

# Agent's problem solver
def solve(email_agent : EmailAgent, problem : str):
    return reason(f"Help with email: {{problem}}", resources=email_agent.resources)'''
    elif "knowledge" in requirements_lower or "research" in requirements_lower or "information" in requirements_lower:
        # Knowledge/research agents need RAG
        return '''"""Knowledge and research agent."""

# Agent resources for knowledge base
knowledge_base = use("rag", sources=["general_knowledge.txt", "research_database.pdf"])

# Agent Card declaration
agent KnowledgeAgent:
    name : str = "Knowledge and Research Agent"
    description : str = "Provides information and research capabilities using knowledge base"
    resources : list = [knowledge_base]

# Agent's problem solver
def solve(knowledge_agent : KnowledgeAgent, problem : str):
    return reason(f"Research and provide information about: {{problem}}", resources=knowledge_agent.resources)'''
    else:
        return '''"""Custom assistant agent."""

# Agent Card declaration
agent CustomAgent:
    name : str = "Custom Assistant Agent"
    description : str = "An agent that can help with various tasks"
    resources : list = []

# Agent's problem solver
def solve(custom_agent : CustomAgent, problem : str):
    return reason(f"Help me with: {{problem}}")'''
