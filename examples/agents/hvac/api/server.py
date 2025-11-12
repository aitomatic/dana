#!/usr/bin/env python3
"""
FastAPI server for HVAC Agent demonstration UI with learning support.

IMPORTANT: This script requires dependencies from the uv-managed virtual environment.
Do NOT run with: python3 server.py (will fail with ModuleNotFoundError)

CORRECT ways to run:
  1. Using uv run (recommended):
     cd /path/to/dana-internal
     uv run python3 examples/agents/hvac/api/server.py

  2. After activating venv manually:
     source .venv/bin/activate
     python3 server.py

The server will run on http://localhost:8081
"""

import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
import traceback
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Get the hvac directory (parent of api/)
AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Calculate PROJECT_ROOT: api -> hvac -> agents -> examples -> dana-internal (4 levels up from AGENT_DIR)
PROJECT_ROOT = Path(AGENT_DIR).parent.parent.parent
DANA_AGENT_DIR = os.path.join(PROJECT_ROOT, "dana_agent")
ENVIRONMENTS_DIR = os.path.join(AGENT_DIR, "environment")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Load .env from project root
    env_file = Path(PROJECT_ROOT) / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print(f"✅ Loaded .env file from: {env_file}")
        # Verify API key is loaded
        if os.getenv("OPENAI_API_KEY"):
            print(f"✅ OPENAI_API_KEY loaded (length: {len(os.getenv('OPENAI_API_KEY'))} chars)")
        else:
            print("⚠️  Warning: OPENAI_API_KEY not found in .env file")
    else:
        print(f"⚠️  Warning: .env file not found at: {env_file}")
except ImportError:
    # dotenv not available, try to load from environment
    print("⚠️  Warning: python-dotenv not available, using environment variables only")
except Exception as e:
    print(f"⚠️  Warning: Could not load .env file: {e}")

# Add paths in correct order
# Add parent directory to path so we can import environment as a package
sys.path.insert(0, AGENT_DIR)  # For importing environment package
sys.path.insert(0, os.path.normpath(os.path.join(AGENT_DIR, "leaners")))  # For WilliamLearner
sys.path.insert(0, os.path.normpath(os.path.join(AGENT_DIR, "agent")))  # For HVACAgent
sys.path.insert(0, DANA_AGENT_DIR)  # For dana imports

# Import after paths are set up
from agent.hvac_agent import HVACAgent
from dana.config.storage_config import FileStorageConfig
from environment.hvac_api import get_env_status, get_feedback
from leaners.william_learner_demo import WilliamLearner_demo as WilliamLearner


# Constants
DEFAULT_SESSION_ID = "hvac-agent-session-001"


# Request models
class PlanRequest(BaseModel):
    environment: Dict[str, Any]
    session_id: Optional[str] = DEFAULT_SESSION_ID
    with_learner: bool = True

class ValidatePlanRequest(BaseModel):
    environment: dict[str, Any]
    plan: dict[str, Any]
    session_id: Optional[str] = DEFAULT_SESSION_ID
    with_learner: bool = True


class SessionRequest(BaseModel):
    session_id: str | None = None


class FeedbackRequest(BaseModel):
    feedback: str
    session_id: str | None = DEFAULT_SESSION_ID


app = FastAPI(title="HVAC Agent API with Learning")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance (will be initialized per request with session)
_agent_cache: dict[str, Any] = {}


def get_agent_with_session(session_id: str = DEFAULT_SESSION_ID, with_learner: bool = True):
    """Get or create agent instance for a session."""
    cache_key = f"agent_{session_id}_{with_learner}"
    if True:
    # if cache_key not in _agent_cache:
        agent = HVACAgent(
            agent_id="hvac-agent-001",
            # model="openai/gpt-4.1",
            llm_provider="openai",
            model="gpt-4.1",
        )
        agent.enable_notifications(verbose=False)
        agent.set_session_id(session_id)
        if with_learner:
            agent._learner = WilliamLearner(agent=agent)
        _agent_cache[cache_key] = agent
    return _agent_cache[cache_key]


def get_learner_storage_path(agent, session_id: str) -> Path:
    """Get the storage path for learnings."""
    storage_config = FileStorageConfig()
    base_path = Path(storage_config.workspace_folder)

    # Get relative path from learner
    learner = agent._learner
    relative_path = learner.get_relative_path()

    return base_path / relative_path


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/hvac/environment")
async def generate_environment():
    """Generate random environment"""
    try:
        while True:
            env_status = get_env_status()
            if env_status.get("meeting_plan"):
                break
            await asyncio.sleep(0.01)

        return env_status
    except Exception as e:
        print(f"Error in generate_environment: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate environment: {str(e)}")


@app.post("/api/hvac/plan")
async def create_plan(request: PlanRequest):
    """Get agent plan from environment"""
    result = None
    try:
        env = request.environment
        session_id = request.session_id or DEFAULT_SESSION_ID

        agent_prompt = f"""
CURRENT ENVIRONMENT:
{json.dumps(env, indent=2)}
"""
        if env.get("meeting_plan"):
            agent_prompt += "\nUpcoming meetings:\n"
            for meeting in env["meeting_plan"]:
                agent_prompt += f"  - {meeting['start_time']} to {meeting['end_time']}\n"

        print(f"Creating HVAC agent for session {session_id}...")
        agent = get_agent_with_session(session_id, with_learner=request.with_learner)
        print(f"Querying agent with prompt...")
        
        # Run synchronous query in thread pool to avoid event loop conflict
        result = await asyncio.to_thread(agent.query, caller_message=agent_prompt, session_id=session_id)

        if not result:
            error_msg = "Agent returned None response"
            print(f"Agent error: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        if "response" not in result:
            error = result.get("error")
            if isinstance(error, Exception):
                error_msg = str(error)
            else:
                error_msg = result.get("error", "Agent did not respond")
            print(f"Agent error: {error_msg}")
            print(f"Full result: {result}")
            raise HTTPException(status_code=500, detail=error_msg)

        # Parse JSON from response
        response_text = result["response"]
        print(f"Agent response (first 500 chars): {response_text[:500]}")

        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            plan = json.loads(json_match.group())
        else:
            plan = json.loads(response_text)

        # Trigger acquisitive learning manually (as shown in hvac_agent.py)
        if agent._learner:
            acquisitive_input = result.copy()
            acquisitive_input.setdefault("caller_message", agent_prompt)
            acquisitive_input.setdefault("tool_calls", [])
            acquisitive_input.setdefault("tool_results", [])
            await asyncio.to_thread(agent._learner._reflect_acquisitive, acquisitive_input)

        return plan
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        if result and "response" in result:
            print(f"Response text: {result['response'][:500]}")
        else:
            print("No response available in result")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to parse agent response as JSON: {str(e)}")
    except RuntimeError as e:
        error_msg = str(e)
        if "event loop" in error_msg.lower():
            error_msg = "Agent query failed due to async event loop conflict. This should not happen."
        print(f"RuntimeError in create_plan: {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in create_plan: {e}")
        print(f"Exception type: {type(e).__name__}")
        traceback.print_exc()
        error_msg = str(e) if isinstance(e, Exception) else repr(e)
        raise HTTPException(status_code=500, detail=f"Failed to create plan: {error_msg}")


@app.post("/api/hvac/validate")
async def validate_plan(request: ValidatePlanRequest):
    """Validate plan and get feedback"""
    try:
        env = request.environment
        plan = request.plan
        session_id = request.session_id or DEFAULT_SESSION_ID
        with_learner = request.with_learner

        # Normalize target_temps
        target_temps = plan["target_temps"]
        if isinstance(target_temps, (int, float)):
            target_temps = [target_temps] * len(plan["plan"])

        feedback = get_feedback(
            current_indoor_temp=env["indoor_temp"],
            outdoor_temp=env["outdoor_temp"],
            current_time=env["current_time"],
            plan=plan["plan"],
            target_temps=target_temps,
            mode=plan["mode"],
            meeting_plan=env.get("meeting_plan"),
        )

        # Automatically trigger episodic learning if learning is enabled
        # if with_learner:
        #     try:
        #         agent = get_agent_with_session(session_id, with_learner=True)
        #         if agent._learner:
        #             # Run episodic learning
        #             trace_learning = await asyncio.to_thread(agent._learner._reflect_episodic, {})
        #             learning_content = trace_learning.get("trace_learning", {}).get("simple_summary", "")
        #             await asyncio.to_thread(agent._learner._store_episodic_learning, learning_content)
        #             print(f"Auto-triggered episodic learning for session {session_id}")
        #     except Exception as e:
        #         # Don't fail validation if episodic learning fails
        #         print(f"Error auto-triggering episodic learning in validate_plan: {e}")
        #         traceback.print_exc()

        return feedback
    except KeyError as e:
        print(f"Missing key in validate_plan: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Missing required field: {str(e)}")
    except Exception as e:
        print(f"Error in validate_plan: {e}")
        print(f"Exception type: {type(e).__name__}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to validate plan: {str(e)}")


@app.post("/api/hvac/sessions")
async def create_session(request: SessionRequest):
    """Create or get session"""
    try:
        session_id = request.session_id or f"hvac-agent-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Initialize agent for this session
        agent = get_agent_with_session(session_id)

        # Count learnings
        learnings_count = 0
        try:
            acquisitive_learnings = await asyncio.to_thread(agent._learner._load_acquisitive)
            learnings_count = len(acquisitive_learnings) if acquisitive_learnings else 0
        except:
            pass

        return {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "learnings_count": learnings_count,
            "executions_count": learnings_count,  # Approximate
        }
    except Exception as e:
        print(f"Error in create_session: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.get("/api/hvac/sessions")
async def list_sessions():
    """List available sessions (simplified - returns default session)"""
    try:
        default_session = DEFAULT_SESSION_ID
        agent = get_agent_with_session(default_session)

        learnings_count = 0
        try:
            acquisitive_learnings = await asyncio.to_thread(agent._learner._load_acquisitive)
            learnings_count = len(acquisitive_learnings) if acquisitive_learnings else 0
        except:
            pass

        return {
            "sessions": [
                {
                    "session_id": default_session,
                    "created_at": datetime.now().isoformat(),
                    "learnings_count": learnings_count,
                    "executions_count": learnings_count,
                }
            ]
        }
    except Exception as e:
        print(f"Error in list_sessions: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@app.get("/api/hvac/learnings/acquisitive")
async def get_acquisitive_learnings(session_id: str = DEFAULT_SESSION_ID):
    """Get all acquisitive learnings for a session"""
    try:
        agent = get_agent_with_session(session_id, with_learner=True)
        
        # Load acquisitive learnings
        acquisitive_learnings = await asyncio.to_thread(agent._learner._load_acquisitive)

        if not acquisitive_learnings:
            return {"learnings": [], "count": 0}

        # Load full loop data from JSON files
        storage_path = agent._learner._get_acquisitive_storage_path()
        loop_files = sorted(storage_path.glob("loop_*.json"), reverse=True)  # Newest first

        learnings = []
        for loop_file in loop_files:
            try:
                loop_data = json.loads(loop_file.read_text())
                learnings.append(
                    {
                        "loop_id": loop_data.get("loop_id", ""),
                        "timestamp": loop_data.get("timestamp", ""),
                        "session_id": loop_data.get("session_id", session_id),
                        "learning_note": loop_data.get("learning_note", ""),
                        "context": {
                            "caller_message": loop_data.get("caller_message", ""),
                            "response": loop_data.get("response", ""),
                            "reasoning": loop_data.get("reasoning", ""),
                        },
                        "execution_data": {
                            "timeline_context": loop_data.get("timeline_context", []),
                            "tool_calls": loop_data.get("tool_calls", []),
                            "tool_results": loop_data.get("tool_results", []),
                        },
                    }
                )
            except Exception as e:
                print(f"Error loading loop file {loop_file}: {e}")
                continue

        return {"learnings": learnings, "count": len(learnings)}
    except Exception as e:
        print(f"Error in get_acquisitive_learnings: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get acquisitive learnings: {str(e)}")

@app.delete("/api/hvac/learnings/acquisitive/{loop_id}")
async def delete_acquisitive_learning(loop_id: str, session_id: str = DEFAULT_SESSION_ID):
    """Delete a specific acquisitive learning by loop_id"""
    try:
        agent = get_agent_with_session(session_id)
        
        # Get storage path
        storage_path = agent._learner._get_acquisitive_storage_path()
        
        # Find the file matching the loop_id
        loop_files = list(storage_path.glob("loop_*.json"))
        target_file = None
        
        for loop_file in loop_files:
            try:
                loop_data = json.loads(loop_file.read_text())
                if loop_data.get("loop_id") == loop_id:
                    target_file = loop_file
                    break
            except Exception as e:
                print(f"Error reading loop file {loop_file}: {e}")
                continue
        
        if not target_file:
            raise HTTPException(status_code=404, detail=f"Learning with loop_id {loop_id} not found")
        
        # Delete the file
        target_file.unlink()
        
        return {"success": True, "message": f"Learning {loop_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_acquisitive_learning: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete acquisitive learning: {str(e)}")

@app.get("/api/hvac/learnings/episodic")
async def get_episodic_learning(session_id: str = DEFAULT_SESSION_ID):
    """Get episodic learning for a session"""
    try:
        agent = get_agent_with_session(session_id)

        # Load episodic learning
        episodic_content = await asyncio.to_thread(agent._learner._load_episodic)

        if not episodic_content:
            return {"content": "", "timestamp": None, "session_id": session_id}

        # Try to get timestamp from file
        storage_path = agent._learner._get_episodic_storage_path()
        learnings_file = storage_path / "learnings.md"
        timestamp = None
        if learnings_file.exists():
            timestamp = datetime.fromtimestamp(learnings_file.stat().st_mtime).isoformat()

        return {"content": episodic_content, "timestamp": timestamp or datetime.now().isoformat(), "session_id": session_id}
    except Exception as e:
        print(f"Error in get_episodic_learning: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get episodic learning: {str(e)}")


@app.post("/api/hvac/learnings/episodic")
async def trigger_episodic_learning(session_id: str = DEFAULT_SESSION_ID):
    """Trigger episodic learning for a session"""
    try:
        agent = get_agent_with_session(session_id)

        # Run episodic learning
        trace_learning = await asyncio.to_thread(agent._learner._reflect_episodic, {})
        learning_content = trace_learning.get("trace_learning", {}).get("simple_summary", "")
        await asyncio.to_thread(agent._learner._store_episodic_learning, learning_content)
        
        return {
            "success": True,
            "content": learning_content,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
    except Exception as e:
        print(f"Error in trigger_episodic_learning: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to trigger episodic learning: {str(e)}")


@app.get("/api/hvac/feedback")
async def get_stored_feedback(session_id: str = DEFAULT_SESSION_ID):
    """Get stored feedback for a session"""
    try:
        agent = get_agent_with_session(session_id)

        # Load feedback
        feedback_content = await asyncio.to_thread(agent._learner._load_feedback)

        if not feedback_content:
            return {"content": "", "timestamp": None, "session_id": session_id}

        # Try to get timestamp from file
        storage_path = agent._learner._get_feedback_storage_path()
        feedback_file = storage_path / "feedback.md"
        timestamp = None
        if feedback_file.exists():
            timestamp = datetime.fromtimestamp(feedback_file.stat().st_mtime).isoformat()

        return {"content": feedback_content, "timestamp": timestamp or datetime.now().isoformat(), "session_id": session_id}
    except Exception as e:
        print(f"Error in get_stored_feedback: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")


@app.post("/api/hvac/feedback")
async def save_feedback(request: FeedbackRequest):
    """Save feedback for a session"""
    try:
        session_id = request.session_id or DEFAULT_SESSION_ID
        feedback_content = request.feedback

        agent = get_agent_with_session(session_id)

        # Save feedback
        await asyncio.to_thread(agent._learner.save_feedback, feedback_content)

        return {"success": True, "timestamp": datetime.now().isoformat(), "session_id": session_id}
    except Exception as e:
        print(f"Error in save_feedback: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")


@app.get("/api/hvac/learnings/metrics")
async def get_learning_metrics(session_id: str = DEFAULT_SESSION_ID):
    """Get learning metrics for a session"""
    try:
        agent = get_agent_with_session(session_id)

        # Load learnings
        acquisitive_learnings = await asyncio.to_thread(agent._learner._load_acquisitive)
        total_learnings = len(acquisitive_learnings) if acquisitive_learnings else 0

        # Simple metrics (can be enhanced)
        return {
            "total_learnings": total_learnings,
            "efficiency_improvement": 0.0,  # Would need to calculate from feedback
            "success_rate_improvement": 0.0,  # Would need to calculate from feedback
            "session_id": session_id,
        }
    except Exception as e:
        print(f"Error in get_learning_metrics: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get learning metrics: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
