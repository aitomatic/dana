// Default Dana agent code examples and templates

export const DEFAULT_DANA_AGENT_CODE = `"""A simple assistant agent that can help with various tasks."""

# Agent Card declaration
agent AssistantAgent:
    name : str = "General Assistant Agent"
    description : str = "A helpful assistant that can answer questions and provide guidance"
    resources : list = []

# Agent's problem solver
def solve(assistant_agent : AssistantAgent, problem : str):
    """Solve problems using AI reasoning."""
    return reason(f"I'm here to help! Let me assist you with: {problem}")`;

export const DANA_AGENT_PLACEHOLDER = `# Dana Agent Examples

# Example 1: Simple Assistant Agent
"""A helpful assistant that can answer questions."""

agent AssistantAgent:
    name : str = "General Assistant Agent"
    description : str = "A helpful assistant that can answer questions and provide guidance"
    resources : list = []

def solve(assistant_agent : AssistantAgent, problem : str):
    return reason(f"I'm here to help! Let me assist you with: {problem}")

# Example 2: Weather Agent with Resources
"""A weather agent that provides weather information."""

# Agent resources for weather data
weather_data = use("rag", sources=["weather_guide.md", "climate_data.pdf"])

agent WeatherAgent:
    name : str = "Weather Information Agent"
    description : str = "Provides weather information and forecasts"
    resources : list = [weather_data]

def solve(weather_agent : WeatherAgent, problem : str):
    return reason(f"Get weather information for: {problem}", resources=weather_agent.resources)

# Example 3: Data Analysis Agent
"""An agent that analyzes data and provides insights."""

agent DataAgent:
    name : str = "Data Analysis Agent"
    description : str = "Analyzes data and provides insights"
    resources : list = []

def solve(data_agent : DataAgent, problem : str):
    return reason(f"Analyze this data and provide insights: {problem}")`;

// Additional agent templates for different use cases
export const AGENT_TEMPLATES = {
  SIMPLE_ASSISTANT: `"""A simple assistant agent that can help with various tasks."""

agent AssistantAgent:
    name : str = "General Assistant Agent"
    description : str = "A helpful assistant that can answer questions and provide guidance"
    resources : list = []

def solve(assistant_agent : AssistantAgent, problem : str):
    return reason(f"I'm here to help! Let me assist you with: {problem}")`,

  WEATHER_AGENT: `"""A weather agent that provides weather information."""

# Agent resources for weather data
weather_data = use("rag", sources=["weather_guide.md", "climate_data.pdf"])

agent WeatherAgent:
    name : str = "Weather Information Agent"
    description : str = "Provides weather information and forecasts"
    resources : list = [weather_data]

def solve(weather_agent : WeatherAgent, problem : str):
    return reason(f"Get weather information for: {problem}", resources=weather_agent.resources)`,

  DATA_ANALYSIS: `"""An agent that analyzes data and provides insights."""

agent DataAgent:
    name : str = "Data Analysis Agent"
    description : str = "Analyzes data and provides insights"
    resources : list = []

def solve(data_agent : DataAgent, problem : str):
    return reason(f"Analyze this data and provide insights: {problem}")`,

  CUSTOMER_SUPPORT: `"""A customer support agent that helps with inquiries."""

agent SupportAgent:
    name : str = "Customer Support Agent"
    description : str = "Helps customers with inquiries and provides support"
    resources : list = []

def solve(support_agent : SupportAgent, problem : str):
    return reason(f"Provide customer support for: {problem}")`,

  RESEARCH_AGENT: `"""A research agent that finds and analyzes information."""

# Agent resources for research
research_data = use("rag", sources=["research_papers.pdf", "industry_reports.pdf"])

agent ResearchAgent:
    name : str = "Research Agent"
    description : str = "Conducts research and provides detailed analysis"
    resources : list = [research_data]

def solve(research_agent : ResearchAgent, problem : str):
    return reason(f"Conduct research on: {problem}", resources=research_agent.resources)`,
} as const;
