#!/usr/bin/env python3
"""
PromptEngineer Web App

A web-based interface for the PromptEngineer interactive example.
Run this script and open http://localhost:8080 in your browser.
"""

import sys
from pathlib import Path

# Add the dana package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dana.frameworks.prteng import PromptEngineer
from dana.core.resource.builtins.llm_resource_type import LLMResourceType
from dana.common.types import BaseRequest

from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = "prompt_engineer_secret_key"

# Global variables for the session
engineer = None
llm_resource = None
current_prompt = None
last_response = None


def create_llm_resource():
    """Create and initialize a real LLM resource instance."""
    try:
        llm_resource = LLMResourceType.create_instance_from_values(
            {
                "name": "prompt_engineer_llm",
                "model": "auto",
                "temperature": 0.7,
                "max_tokens": 2048,
            }
        )
        return llm_resource, "Real LLM resource initialized successfully"
    except Exception as e:
        return None, f"Failed to initialize real LLM resource: {e}"


def generate_llm_response(llm_resource, prompt_text: str) -> str:
    """Generate a response using a real LLM resource or fallback to mock."""
    if llm_resource is None:
        return "This is a mock response for testing purposes. The LLM resource is not available."

    try:
        request_obj = BaseRequest(
            arguments={
                "messages": [{"role": "user", "content": prompt_text}],
                "temperature": 0.7,
                "max_tokens": 2048,
            }
        )

        response = llm_resource.query_sync(request_obj)

        if response.success:
            if hasattr(response, "content") and response.content:
                if isinstance(response.content, str):
                    return response.content
                elif isinstance(response.content, dict):
                    if "choices" in response.content and response.content["choices"]:
                        choice = response.content["choices"][0]
                        if "message" in choice and "content" in choice["message"]:
                            return choice["message"]["content"]
                    elif "text" in response.content:
                        return response.content["text"]
                    elif "content" in response.content:
                        return response.content["content"]
                    else:
                        return str(response.content)
                else:
                    return str(response.content)
            else:
                return "No content in response"
        else:
            return f"LLM call failed: {response.error}"

    except Exception as e:
        return f"Error calling LLM: {e}"

    # Fallback return (should never be reached, but satisfies type checker)
    return "Unexpected error in LLM response generation"


@app.route("/")
def index():
    """Main page."""
    return render_template("index.html")


@app.route("/api/init", methods=["POST"])
def init_session():
    """Initialize a new session."""
    global engineer, llm_resource, current_prompt

    # Initialize LLM resource first
    llm_resource, message = create_llm_resource()

    # Initialize the engineer with the LLM resource
    engineer = PromptEngineer(base_dir="~/.dana/prteng_webapp", llm_resource=llm_resource)

    # Use existing session ID or generate a new one
    if "session_id" not in session:
        # For testing, use a fixed ID so we can see prompt evolution
        session_id = "test-session-12345"
        session["session_id"] = session_id
    else:
        session_id = session["session_id"]

    return jsonify({"success": True, "message": message, "session_id": session_id})


@app.route("/api/start", methods=["POST"])
def start_conversation():
    """Start a new conversation with a user query."""
    global engineer, current_prompt

    data = request.get_json()
    user_query = data.get("query", "").strip()
    custom_prompt_id = data.get("prompt_id", "").strip()

    if not user_query:
        return jsonify({"success": False, "error": "Please provide a query"})

    if not engineer:
        return jsonify({"success": False, "error": "Session not initialized"})

    try:
        # Use custom prompt_id if provided, otherwise use fixed session ID
        if custom_prompt_id:
            fixed_prompt_id = custom_prompt_id
            print(f"DEBUG: Using custom prompt_id: {fixed_prompt_id}")
        else:
            # Use the same fixed session ID that has the evolved prompt history
            fixed_prompt_id = "7d637072-cf78-4ccb-8a86-ef6a824930fd"
            print(f"DEBUG: Using fixed session prompt_id: {fixed_prompt_id}")

        # Check if there's existing history for this prompt ID
        existing_template = engineer.persistence.get_latest_template(fixed_prompt_id)
        print(f"DEBUG: Existing template: '{existing_template}'")

        if existing_template and existing_template.strip():
            # Use existing system prompt from history
            print("DEBUG: Using existing template from history")
            current_prompt = engineer.generate(user_query, prompt_id=fixed_prompt_id)
        else:
            # Start with a basic system template for new sessions
            print("DEBUG: Using new system template")
            system_template = "You are a helpful AI assistant. Please provide clear, accurate, and helpful responses to user queries."
            current_prompt = engineer.generate(user_query, prompt_id=fixed_prompt_id, system_template=system_template)

        print(f"DEBUG: Final system_message: '{current_prompt.system_message}'")
        print(f"DEBUG: system_message type: {type(current_prompt.system_message)}")
        print(f"DEBUG: system_message length: {len(current_prompt.system_message) if current_prompt.system_message else 'None'}")

        # Get the current version number
        template_versions = engineer.persistence.load_template_versions(fixed_prompt_id)
        if template_versions:
            current_version = max(version.version for version in template_versions)
        else:
            current_version = 1
        print(f"DEBUG: Current version: {current_version}")

        response_data = {
            "success": True,
            "prompt_id": current_prompt.id,
            "system_message": current_prompt.system_message or "(No system prompt)",
            "user_message": current_prompt.user_message,
            "version": current_version,
        }
        print(f"DEBUG: API response data: {response_data}")

        return jsonify(response_data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/generate", methods=["POST"])
def generate_response():
    """Generate an AI response."""
    global current_prompt, llm_resource, last_response

    if not current_prompt:
        return jsonify({"success": False, "error": "No active prompt"})

    try:
        response = generate_llm_response(llm_resource, current_prompt.text)
        last_response = response  # Store the response for feedback processing

        return jsonify(
            {
                "success": True,
                "response": response,
                "system_message": current_prompt.system_message or "(No system prompt)",
                "user_message": current_prompt.user_message,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/feedback", methods=["POST"])
def process_feedback():
    """Process user feedback and update the system prompt."""
    global engineer, current_prompt, llm_resource, last_response

    data = request.get_json()
    feedback = data.get("feedback", "").strip()
    use_llm_feedback = data.get("use_llm_feedback", False)
    prompt_id = data.get("prompt_id", "").strip()
    criteria = data.get("criteria", [])
    custom_objective = data.get("custom_objective", "").strip()

    if not feedback and not use_llm_feedback:
        return jsonify({"success": False, "error": "Please provide feedback"})

    if not engineer:
        return jsonify({"success": False, "error": "No active session"})

    if not last_response:
        return jsonify({"success": False, "error": "No response to evaluate. Please generate a response first."})

    # Use the provided prompt_id or fall back to current_prompt
    if prompt_id:
        print(f"DEBUG: Using custom prompt_id for feedback: {prompt_id}")
    elif not current_prompt:
        return jsonify({"success": False, "error": "No active prompt"})
    else:
        prompt_id = current_prompt.id

    try:
        # Generate evaluation using the new evaluate() method
        if use_llm_feedback:
            print(f"DEBUG FEEDBACK: criteria={criteria}")
            print(f"DEBUG FEEDBACK: custom_objective='{custom_objective}'")
            evaluation = engineer.evaluate(
                prompt_id=prompt_id, response=last_response, criteria=criteria, custom_objective=custom_objective, evaluation_type="llm"
            )
            feedback = "; ".join(evaluation.improvement_suggestions)
        else:
            feedback = feedback  # Use the manual feedback

        # Update the engineer with feedback
        engineer.update(last_response, prompt_id, feedback)

        # Check if template evolved
        current_template = engineer.persistence.get_latest_template(prompt_id)
        template_versions = engineer.persistence.load_template_versions(prompt_id)

        evolved = False
        if current_template and current_prompt and current_template != current_prompt.system_message:
            current_prompt.system_message = current_template
            evolved = True

        # Calculate current version number
        if template_versions:
            current_version = max(version.version for version in template_versions)
        else:
            current_version = 1

        return jsonify(
            {
                "success": True,
                "feedback": feedback,
                "evolved": evolved,
                "version": current_version,
                "new_system_message": current_template or "(No system prompt)",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/history", methods=["GET"])
def get_history():
    """Get the conversation history."""
    global engineer, current_prompt

    if not engineer or not current_prompt:
        return jsonify({"success": False, "error": "No active session"})

    try:
        history = engineer.get_history(current_prompt.id)
        template_versions = engineer.persistence.load_template_versions(current_prompt.id)

        history_data = []
        for interaction in history:
            history_data.append(
                {
                    "timestamp": interaction.timestamp.isoformat(),
                    "response": interaction.response,
                    "feedback": interaction.feedback,
                    "evaluation_score": interaction.evaluation.overall_score if interaction.evaluation else None,
                    "evaluation_suggestions": interaction.evaluation.improvement_suggestions if interaction.evaluation else [],
                }
            )

        return jsonify(
            {
                "success": True,
                "history": history_data,
                "template_versions": len(template_versions),
                "current_system_message": current_prompt.system_message or "(No system prompt)",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/prompt-ids", methods=["GET"])
def get_prompt_ids():
    """Get list of all existing prompt IDs."""
    global engineer

    if not engineer:
        return jsonify({"success": False, "error": "Session not initialized"})

    try:
        # Get all prompt IDs from persistence
        prompt_ids = engineer.persistence.list_prompt_ids()
        return jsonify({"success": True, "prompt_ids": prompt_ids})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    print("Starting PromptEngineer Web App...")
    print("Open your browser and go to: http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=True)
