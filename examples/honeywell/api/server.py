#!/usr/bin/env python3
"""
FastAPI server for HVAC Agent demonstration UI.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import sys
import os
import json
import re
import traceback
import asyncio

# Get the honeywell directory (parent of api/)
HONEYWELL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(HONEYWELL_DIR))
DANA_AGENT_DIR = os.path.join(PROJECT_ROOT, "dana_agent")
ENVIRONMENTS_DIR = os.path.join(HONEYWELL_DIR, "environments")

# Add paths in correct order
sys.path.insert(0, ENVIRONMENTS_DIR)  # Must be first for hvac_api imports
sys.path.insert(0, HONEYWELL_DIR)  # For importing hvac_agent
sys.path.insert(0, DANA_AGENT_DIR)  # For dana imports

# Import after paths are set up
from hvac_api import get_env_status, get_feedback
from hvac_agent import HVACAgent

# Request models
class PlanRequest(BaseModel):
    environment: Dict[str, Any]

class ValidatePlanRequest(BaseModel):
    environment: Dict[str, Any]
    plan: Dict[str, Any]

app = FastAPI(title="HVAC Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/hvac/environment")
async def generate_environment():
    """Generate random environment"""
    try:
        return get_env_status()
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
        
        agent_prompt = f"""
CURRENT ENVIRONMENT:
{json.dumps(env, indent=2)}
"""
        if env.get('meeting_plan'):
            agent_prompt += "\nUpcoming meetings:\n"
            for meeting in env['meeting_plan']:
                agent_prompt += f"  - {meeting['start_time']} to {meeting['end_time']}\n"
        
        print(f"Creating HVAC agent...")
        agent = HVACAgent()
        print(f"Querying agent with prompt...")
        # Run synchronous query in thread pool to avoid event loop conflict
        result = await asyncio.to_thread(agent.query, caller_message=agent_prompt)
        
        if not result:
            error_msg = "Agent returned None response"
            print(f"Agent error: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        if "response" not in result:
            error = result.get("error")
            # Handle RuntimeError and other exceptions properly
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
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            plan = json.loads(json_match.group())
        else:
            plan = json.loads(response_text)
        
        return plan
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        if result and "response" in result:
            print(f"Response text: {result['response'][:500]}")
        else:
            print(f"No response available in result")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to parse agent response as JSON: {str(e)}")
    except RuntimeError as e:
        # Handle asyncio event loop conflicts
        error_msg = str(e)
        if "event loop" in error_msg.lower():
            error_msg = "Agent query failed due to async event loop conflict. This should not happen."
        print(f"RuntimeError in create_plan: {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error in create_plan: {e}")
        print(f"Exception type: {type(e).__name__}")
        traceback.print_exc()
        # Ensure error message is JSON serializable
        error_msg = str(e) if isinstance(e, Exception) else repr(e)
        raise HTTPException(status_code=500, detail=f"Failed to create plan: {error_msg}")

@app.post("/api/hvac/validate")
async def validate_plan(request: ValidatePlanRequest):
    """Validate plan and get feedback"""
    try:
        env = request.environment
        plan = request.plan
        
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
            meeting_plan=env.get("meeting_plan")
        )
        
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

@app.get("/api/hvac/policies")
async def get_policies():
    """Get current policies from HVACAgent.xml"""
    try:
        prompt_path = os.path.join(HONEYWELL_DIR, "prompts", "HVACAgent.xml")
        
        if not os.path.exists(prompt_path):
            raise HTTPException(status_code=404, detail=f"Prompt file not found: {prompt_path}")
        
        with open(prompt_path, 'r') as f:
            content = f.read()
        
        # Extract policies
        policies = []
        lines = content.split('\n')
        in_rules = False
        for line in lines:
            if 'YOU MUST FOLLOW THESE RULES:' in line:
                in_rules = True
                continue
            if in_rules:
                if line.strip().startswith('- '):
                    policies.append(line.strip()[2:])  # Remove '- ' prefix
                elif line.strip() and not line.strip().startswith('- '):
                    break
        
        return {"policies": policies, "count": len(policies)}
    except Exception as e:
        print(f"Error in get_policies: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)

