from dotenv import load_dotenv

load_dotenv()

# from dana.core.knowledge.prompts.codecs import NativeToolsCodec
# # from dana.common.llm.llm import LLM, LLMMessage
# # import asyncio

# # # llm = LLM(provider="azure", model="gpt-4o")
# # llm = LLM(provider="openai", model="gpt-4o")

# # response = asyncio.run(llm.chat(messages=[LLMMessage(role="user", content="Hello, how are you?")]))

# # print(response)


# from dana.core.agent.builtin_agents.explore import ExploreAgent
# from dana.core.knowledge.prompts.prompt_api import LocalPromptAPI

# agent = ExploreAgent(agent_id="explore-test-123", agent_type="explore_agent", llm_provider="openai", model="gpt-4o")

# prompt_api = agent._runtime._get_prompt_api(agent)

# print(prompt_api.system_prompt)


# from dana.core.runtime.codec.codec_without_native_tool_use import CodecRuntimeWithoutNativeToolUse
# from dana.common.llm.types import LLMResponse

# data = """
# <thinking>
# The user reaffirmed to proceed without interruptions. I must complete both phases. Phase 1 extraction was invoked earlier, but I need to verify the generated extraction markdown exists and contains equipment data, then immediately proceed to Phase 2 to create ontology instances. Plan: use file search to locate the extraction file (likely p1_b11b52a9bc1f042e_extraction.md), read/verify it has equipment entries, then invoke the ontology skill with that file. Manage todos: mark verification in progress, then completed, then ontology in progress, then completed. If the extraction file is missing, report and attempt recovery. Proceed with tool calls now.</thinking>
# <function_call>
#   <invoke name="Glob">
#     <parameter name="pattern">**/*p1_b11b52a9bc1f042e*_extraction.md</parameter>
#   </invoke>
# </function_call>
# """


# codec_runtime = CodecRuntimeWithoutNativeToolUse()
# response = codec_runtime.parse_response(LLMResponse(content=data, model="gpt-5"))
# print(response)


# from dana.common.llm.providers.openai import OpenAIProvider
# from dana.common.llm.types import LLMMessage
# import asyncio

# provider = OpenAIProvider(model="gpt-5-thinking")
# messages = [LLMMessage(role="user", content="Hello, how are you?")]
# response = asyncio.run(provider.chat(messages))
# print(response)

# THINKING USING RESPONSES API
import openai

client = openai.OpenAI()
messages = [{"role": "user", "content": "Hello, how are you?"}]
response = client.responses.create(model="gpt-5", input=messages, reasoning={"effort": "medium", "summary": "auto"})
print("RESPONSE API")
print(type(response))
print(response.model_dump_json(indent=4))

output = response.output
output.append({"role": "user", "content": "Can you help me with a math problem?"})
response = client.responses.create(model="gpt-5", input=output, reasoning={"effort": "medium", "summary": "auto"})
print("RESPONSE API")
print(response.model_dump_json(indent=4))

# THINKING USING COMPLETION API
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-5",  # or o3, gpt-5, etc.
    messages=[{"role": "user", "content": "Solve: If a train travels 60 km in 90 minutes, what is its speed in km/h?"}],
    reasoning_effort="high",  # low, medium, high
    max_completion_tokens=5000,  # required for reasoning models (not max_tokens)
)
print("COMPLETION API")
print(response)


# # TOOL CALLS
# from openai import OpenAI

# client = OpenAI()

# tools = [
#     {
#         "type": "function",
#         "name": "get_weather",
#         "description": "Get current temperature for a given location.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "location": {
#                     "type": "string",
#                     "description": "City and country e.g. Bogotá, Colombia",
#                 }
#             },
#             "required": ["location"],
#             "additionalProperties": False,
#         },
#         "strict": True,
#     },
# ]

# # Step 1: Call model with tools
# response = client.responses.create(
#     model="gpt-4.1-nano",
#     input=[{"role": "user", "content": "What is the weather like in Paris today?"}],
#     tools=tools,
#     store=True,
#     # include=["reasoning.encrypted_content"]
# )

# print(response.model_dump_json(indent=4))
