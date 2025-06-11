# product_ranking_langgraph.py
import os
from typing import Any, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from utils import search_vector_db

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Define the state
class State(TypedDict):
    product_id: str
    similar_products: str
    ranked_products: list[str]
    messages: list[Any]


# Define ranking function using LLM
def rank_products(state: State) -> State:
    llm = ChatOpenAI(temperature=0, api_key=openai_api_key)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            """
            You are a product ranking expert. Rank the following products 
            based on their use cases.
            Choose the top 3 products that most closely match the product ID: \
            {product_id}.
            Return the description of the top 3 in a numbered list format.
            """
        )),
        ("user", "{similar_products}")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "similar_products": state["similar_products"],
        "product_id": state["product_id"]
    })
    state["ranked_products"] = [response.content]
    state["messages"].append(
        AIMessage(
            content=f"Top ranked products: {response.content}"
        )
    )
    
    return state

# Process the initial input
def process_input(state: State) -> State:
    state["messages"].append(
        AIMessage(
            content=f"Processing request for product ID: {state['product_id']}"
        )
    )
    return state

def call_and_process_vector_db(state: State) -> State:
    """Node that calls the vector DB tool and processes the result"""
    print(f"Searching for product ID: {state['product_id']}...")
    tool_output = search_vector_db(state["product_id"])
    state["similar_products"] = tool_output

    print("Vector search completed. Matches found: ", tool_output)
    
    state["messages"].append(
        AIMessage(
            content="Vector search completed. Processing results..."
        )
    )
    return state

# Define the nodes in our graph
def build_graph():
    workflow = StateGraph(State)

    workflow.add_node("process_input", process_input)
    workflow.add_node("call_and_process_vector_db", call_and_process_vector_db)
    workflow.add_node("rank_products", rank_products)

    workflow.add_edge("process_input", "call_and_process_vector_db")
    workflow.add_edge("call_and_process_vector_db", "rank_products")
    workflow.add_edge("rank_products", END)

    workflow.set_entry_point("process_input")

    return workflow.compile()

# Main function to run the product ranker
def rank_similar_products(product_id: str) -> list[str]:
    graph = build_graph()
    
    # Initialize the state
    state = {
        "product_id": product_id,
        "similar_products": "",
        "ranked_products": [],
        "messages": []
    }
    
    # Run the graph
    result = graph.invoke(state)
    
    # Return the ranked products
    return result["ranked_products"]

# Example usage
if __name__ == "__main__":
    product_id = "CM-2501"
    print(f"Ranking similar products for {product_id}...")
    ranked_products = rank_similar_products(product_id)
    print("\nTop 3 ranked products:")
    for i, product in enumerate(ranked_products, 1):
        print(f"{i}. {product}")
