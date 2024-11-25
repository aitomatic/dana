import openai
import time
from anthropic import AnthropicBedrock, AsyncAnthropicBedrock
import os
from dotenv import load_dotenv  # Import load_dotenv from dotenv
import json
# ... existing code ...

# Load environment variables from .env file
load_dotenv()  # Add this line

# Set your OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

aClient = openai.AsyncOpenAI(api_key=api_key, base_url="https://api.openai.com/v1")
aModel = "gpt-4o"

# Initialize the AnthropicBedrock and AsyncAnthropicBedrock clients
aws_region = "us-east-1"
bedrock_client = AnthropicBedrock(aws_region=aws_region)
async_bedrock_client = AsyncAnthropicBedrock(aws_region=aws_region)


# following prompt practically combines Orient & Decide steps into 1 single LM request for efficiency
ORIENT_PROMPT_TEMPLATE: str = \
"""Assuming that the following question/problem/task is posed

```
{question}
```

and you have observed various answers/solutions from different informational resources as detailed below,
please evaluate whether you can answer/solve the posed question/problem/task confidently with concrete results.
If the question/problem/task mentions any RIGOROUS BASES/CRITERIA/DEFINITIONS for judgement,
the concrete results MUST RESPOND TO SUCH BASES/CRITERIA/DEFINITIONS for the answer/solution to be considered confident.
If the question/problem/task involves any NUMERICAL QUANTITIES (e.g., MULTIPLES or RATIOS) to be retrieved or calculated,
the concrete results MUST CONTAIN SPECIFIC VALUES for such quantities for the answer/solution to be considered confident.

Return your best-effort answer/solution of up to {n_words:,} words, covering reasoning flows and supporting details,
PREPENDING such answer/solution with the header "[CONFIDENT]" if you can answer/solve confidently with concrete results,
and with the header "[UNCONFIDENT]" otherwise.

```
{observations}
```
"""  # noqa: E122

# Function to interact with the tLLM (Anthropic Bedrock Claude)
async def interact_with_tLLM(prompt):
    # Create the messages list as required by the API
    prompt = f"{tLLM_system_instrcutions}. {prompt}"
    messages = [{"role": "user", "content": prompt}]
    response = await async_bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",  # Replace with the actual model ID for Claude if different
        messages=messages,  # Added messages argument
        temperature=0.0,
        max_tokens=2000  # Adjust the number of tokens as needed
    )
    if len(response.content) > 0:
        return response.content[0].text
    return ""

# Function to interact with the tLLM (external model)
async def interact_with_tLLM_openAI(prompt):
    # prompt = f"Be a great AI/ML system can answer correct for a query. The given query: {prompt}. Please answer:"
    response = await aClient.chat.completions.create(
        model=aModel, 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()

# Function to interact with the aLLM (agent's internal model)
async def interact_with_aLLM(prompt):
    prompt = f"{aLLM_system_instructions}. {prompt}"
    response = await aClient.chat.completions.create(
        model=aModel, 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()

# OODA loop implementation
async def ooda_loop(problem_statement):
    context = {
        "problem": problem_statement,
        "steps": [],
        "aggregated_results": {
            "observations": [],
            "queries": [],
            "answers": [],
            "final_solution": ""
        }
    }

    async def observe(problem):
        prompt = f"Given the problem statement: '{problem}', what initial information should we gather to proceed?"
        observation = await interact_with_aLLM(prompt)
        print(f"----aLLM observations:{observation}")
        context["steps"].append({"step": "Observe", "response": observation})
        context["aggregated_results"]["observations"].append(observation)
        return observation

    async def orient(observation, extra_info=""):
        # prompt = f"Based on the observation: '{observation}', what a specific query should we send to an external model to gather more information? Only one query."
        # gen_query_prompt = "what a specific query should we send to an external model to gather more information? Only one query."
        gen_query_prompt = "what a specific query should we send to an external model to resolve problem? Only one query."
        if extra_info:
            prompt = f"Based on the observation: '{observation}' and the extra information from user:{extra_info}, {gen_query_prompt}"
        else:
            prompt = f"Based on the observation: '{observation}', {gen_query_prompt}"
        query = await interact_with_aLLM(prompt)
        print(f"----aLLM query:{query}")
        context["steps"].append({"step": "Orient", "response": query})
        context["aggregated_results"]["queries"].append(query)
        return query

    async def decide(query):
        response_from_tLLM = await interact_with_tLLM(query)
        print(f"----tLLM response----:{response_from_tLLM}\n\n")
        print(f"--------------\n")
        # response_from_aLLM = await interact_with_aLLM(query)
        # print(f"----aLLM response----:{response_from_aLLM}\n\n\n\n\n")
        print(f"----------------------------------------\n")
        context["steps"].append({"step": "Decide", "response": response_from_tLLM})
        # context["aggregated_results"]["answers"].append(response_from_aLLM)
        return response_from_tLLM

    def act(observation, response_from_tLLM):
        solution = f"Combining observation: '{observation}' with the tLLM's answer: '{response_from_tLLM}', the proposed solution is to take action based on these insights."
        context["steps"].append({"step": "Act", "response": solution})
        context["aggregated_results"]["final_solution"] = solution
        return solution

    def generate_report(context):
        report = f"Problem Statement: {context['problem']}\n\n"
        report += "Aggregated Results:\n"
        report += "\n1. Observations:\n"
        for obs in context["aggregated_results"]["observations"]:
            report += f"- {obs}\n"
        report += "\n2. Queries Sent to tLLM:\n"
        for query in context["aggregated_results"]["queries"]:
            report += f"- {query}\n"
        report += "\n3. Answers from tLLM:\n"
        for answer in context["aggregated_results"]["answers"]:
            report += f"- {answer}\n"
        report += "\n4. Final Solution:\n"
        report += f"- {context['aggregated_results']['final_solution']}\n"
        return report

    # Execute the OODA loop
    observation = await observe(problem_statement)
    print('\n--------------------------\n\n\n')
    query = await orient(observation)
    print('\n--------------------------\n\n\n')
    while query:
        response_from_tLLM = await decide(query)
        check_query_prompt = (
            "You are an AI reasoning expert. Please verify the query from user and the answer that need to more information from user. "
            f"\nQuery:{query}.\nAnswer:{response_from_tLLM}. PLease evaluate concise and responsein JSON format "
            "with field 'ask_more' is true or false and 'query' to ask user to get more information. Only one query:"
        )
        actions = await interact_with_aLLM(check_query_prompt)
        print(actions)

        # Remove any unwanted prefix or postfix
        actions = actions.strip()  # Remove leading/trailing whitespace
        if actions.startswith('```json') and actions.endswith('```'):
            actions = actions[7:-3].strip()  # Remove the '```json' prefix and '```' postfix

        extra_info = ""
        
        # Check if actions is a JSON string and parse it
        try:
            actions = json.loads(actions)  # Parse the JSON string into a dictionary
        except json.JSONDecodeError:
            print("Failed to decode JSON, received:", actions)
            return  # Exit or handle the error appropriately

        stop_loop = True
        # Ensure actions is a dictionary before accessing its keys
        if isinstance(actions, dict) and actions.get("ask_more"):  # Use .get() to safely access the key
            extra_info = input(actions.get("query", "Please provide more information: "))  # Provide a default message if 'query' is not found
            stop_loop = False

        # prompt = ORIENT_PROMPT_TEMPLATE.format(question=query, n_words=200, observations=response_from_tLLM)
        # res = await interact_with_tLLM(prompt=prompt)
        # print(f"Evaluate query and response to stop loop:{res}")
        # print(f"\n-------------------\n\n\n")
        # if '[CONFIDENT]' in res:
        #     break

        if stop_loop:
            break
        query = await orient(response_from_tLLM, extra_info)


# Example usage with a problem statement
problem_statement = "Fridge is running but not cool."
# problem_statement = "solve fermats last theorem."
aLLM_system_instructions = "You are an expert problem solver. You have access to an external domain expert LLM."
tLLM_system_instrcutions = "You are an expert in fridge."
import asyncio
asyncio.run(ooda_loop(problem_statement))
