"""
Smart HVAC Demo - FastAPI Backend

Side-by-side comparison of:
- Basic HVAC (SENSE + ACT)
- POET-enhanced HVAC (SENSE + THINK + ACT)

Demonstrates POET's learning and optimization capabilities.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from hvac_systems import (
    ComfortBasedController,
    basic_hvac_control,
    calculate_comfort_score,
    smart_hvac_control,
)
from llm_integration import get_llm_manager, initialize_llm_for_demo
from pydantic import BaseModel
from room_simulator import RoomSimulator

# ============================================================
# DATA MODELS
# ============================================================


class SystemState(BaseModel):
    """Current state of an HVAC system."""

    system_id: str
    current_temp: float
    target_temp: float
    outside_temp: float
    occupancy: bool
    mode: str
    heating_output: float
    cooling_output: float
    fan_speed: float
    energy_usage: float
    comfort_score: float
    total_energy: float


class UserInput(BaseModel):
    """User input for system control."""

    system_id: str
    action: str  # "set_temp", "too_hot", "too_cold", "comfortable"
    value: float = None  # For set_temp


class SystemMetrics(BaseModel):
    """Historical metrics for visualization."""

    timestamps: list[str]
    temperatures: list[float]
    energy_usage: list[float]
    comfort_scores: list[float]
    target_temps: list[float]


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(title="Smart HVAC Demo", version="1.0.0")

# Serve static files
import os

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ============================================================
# GLOBAL STATE
# ============================================================


def extract_hvac_command(result):
    """Extract HVAC command from POET result wrapper."""
    if isinstance(result, dict) and "result" in result:
        return result["result"]
    else:
        return result


class HVACDemoManager:
    """Manages both HVAC systems and their simulations."""

    def __init__(self):
        # Room simulators
        self.basic_room = RoomSimulator(initial_temp=72.0)
        self.smart_room = RoomSimulator(initial_temp=72.0)

        # Control systems
        self.comfort_controller = ComfortBasedController()

        # System states
        self.basic_target = 72.0
        self.smart_target = 72.0

        # Metrics storage
        self.metrics = {
            "basic": {"timestamps": [], "temperatures": [], "energy_usage": [], "comfort_scores": [], "target_temps": []},
            "smart": {"timestamps": [], "energy_usage": [], "temperatures": [], "comfort_scores": [], "target_temps": []},
        }

        # Simulation control
        self.running = False
        self.update_interval = 2.0  # seconds

        # Connected WebSocket clients
        self.clients = []

    async def start_simulation(self):
        """Start the simulation loop."""
        self.running = True
        while self.running:
            await self.update_systems()
            await asyncio.sleep(self.update_interval)

    async def update_systems(self):
        """Update both HVAC systems and broadcast state."""
        timestamp = datetime.now().isoformat()

        # Update weather ONCE for both systems
        from room_simulator import _weather_service

        _weather_service.update_weather()

        # Update basic HVAC system
        basic_command = basic_hvac_control(
            current_temp=self.basic_room.state.temperature,
            target_temp=self.basic_target,
            outdoor_temp=self.basic_room.state.outside_temp,
            occupancy=self.basic_room.state.occupancy,
        )

        basic_state = self.basic_room.step(basic_command)
        basic_comfort = calculate_comfort_score(
            current_temp=basic_state["temperature"], target_temp=self.basic_target, temp_history=self.basic_room.get_recent_temps()
        )

        # Update smart HVAC system
        smart_result = smart_hvac_control(
            current_temp=self.smart_room.state.temperature,
            target_temp=self.smart_target,
            outdoor_temp=self.smart_room.state.outside_temp,
            occupancy=self.smart_room.state.occupancy,
        )
        smart_command = extract_hvac_command(smart_result)

        smart_state = self.smart_room.step(smart_command)
        smart_comfort = calculate_comfort_score(
            current_temp=smart_state["temperature"], target_temp=self.smart_target, temp_history=self.smart_room.get_recent_temps()
        )

        # Store metrics
        self._store_metrics("basic", timestamp, basic_state, basic_comfort, self.basic_target)
        self._store_metrics("smart", timestamp, smart_state, smart_comfort, self.smart_target)

        # Broadcast to WebSocket clients
        await self._broadcast_state()

    def _store_metrics(self, system: str, timestamp: str, state: dict, comfort: float, target: float):
        """Store metrics for a system."""
        metrics = self.metrics[system]

        metrics["timestamps"].append(timestamp)
        metrics["temperatures"].append(state["temperature"])
        metrics["energy_usage"].append(state["energy_usage"])
        metrics["comfort_scores"].append(comfort)
        metrics["target_temps"].append(target)

        # Keep only recent data (last 100 points)
        max_points = 100
        for key in metrics:
            if len(metrics[key]) > max_points:
                metrics[key] = metrics[key][-max_points:]

    async def _broadcast_state(self):
        """Broadcast current state to all WebSocket clients."""
        if not self.clients:
            return

        # Get POET learning status
        poet_status = {}
        try:
            if hasattr(smart_hvac_control, "_poet_executor"):
                executor = smart_hvac_control._poet_executor
                learning_status = executor.get_learning_status()
                recommendations = executor.get_learning_recommendations()
                metrics = executor.get_metrics()

                poet_status = {
                    "learning_algorithm": learning_status.get("learning_algorithm", "statistical"),
                    "recommendations": recommendations,
                    "poe_metrics": metrics,
                }
        except Exception as e:
            print(f"Error getting POET status for WebSocket: {e}")
            pass

        message = {
            "type": "state_update",
            "timestamp": datetime.now().isoformat(),
            "systems": {"basic": self._get_system_state("basic"), "smart": self._get_system_state("smart")},
            "poet_status": poet_status,
            "metrics": {"basic": self._get_recent_metrics("basic"), "smart": self._get_recent_metrics("smart")},
        }

        # Send to all clients
        disconnected = []
        for client in self.clients:
            try:
                await client.send_text(json.dumps(message))
            except:
                disconnected.append(client)

        # Remove disconnected clients
        for client in disconnected:
            self.clients.remove(client)

    def _get_system_state(self, system: str) -> dict[str, Any]:
        """Get current state for a system."""
        room = self.basic_room if system == "basic" else self.smart_room
        target = self.basic_target if system == "basic" else self.smart_target

        # Get most recent HVAC command
        recent_command = room.metrics.hvac_commands[-1] if room.metrics.hvac_commands else None

        comfort = calculate_comfort_score(current_temp=room.state.temperature, target_temp=target, temp_history=room.get_recent_temps())

        return {
            "system_id": system,
            "current_temp": round(room.state.temperature, 1),
            "target_temp": round(target, 1),
            "outside_temp": round(room.state.outside_temp, 1),
            "occupancy": room.state.occupancy,
            "mode": recent_command.mode if recent_command else "idle",
            "heating_output": recent_command.heating_output if recent_command else 0,
            "cooling_output": recent_command.cooling_output if recent_command else 0,
            "fan_speed": recent_command.fan_speed if recent_command else 0,
            "energy_usage": room.get_avg_energy_rate(),
            "comfort_score": round(comfort, 1),
            "total_energy": round(room.get_total_energy(), 3),
        }

    def _get_recent_metrics(self, system: str, count: int = 20) -> dict:
        """Get recent metrics for visualization."""
        metrics = self.metrics[system]

        return {
            "timestamps": metrics["timestamps"][-count:],
            "temperatures": metrics["temperatures"][-count:],
            "energy_usage": metrics["energy_usage"][-count:],
            "comfort_scores": metrics["comfort_scores"][-count:],
            "target_temps": metrics["target_temps"][-count:],
        }

    def handle_user_input(self, user_input: UserInput):
        """Handle user input for system control."""
        if user_input.system_id == "basic":
            if user_input.action == "set_temp" and user_input.value:
                self.basic_target = max(60, min(85, user_input.value))

        elif user_input.system_id == "smart":
            if user_input.action in ["too_hot", "too_cold", "comfortable"]:
                # Use comfort-based controller
                current_temp = self.smart_room.state.temperature
                self.smart_target = self.comfort_controller.process_feedback(feedback=user_input.action, current_temp=current_temp)

                # Use LLM for intelligent comfort reasoning if available
                asyncio.create_task(self._handle_smart_feedback(user_input.action, current_temp))

                # Provide feedback to POET for learning
                try:
                    if hasattr(smart_hvac_control, "_poet_executor"):
                        {"too_hot": 0.3, "too_cold": 0.3, "comfortable": 1.0}.get(user_input.action, 0.5)

                        # Future: implement feedback mechanism
                        pass
                except:
                    pass

    async def _handle_smart_feedback(self, feedback: str, current_temp: float):
        """Handle intelligent feedback processing with LLM."""
        try:
            llm_manager = get_llm_manager()
            if llm_manager.initialized:
                # Get LLM reasoning about comfort
                comfort_analysis = await llm_manager.reason_about_comfort(
                    current_temp=current_temp,
                    target_temp=self.smart_target,
                    user_feedback=feedback,
                    comfort_history=self.comfort_controller.comfort_history,
                )

                # Apply LLM suggestions if confidence is high enough
                if comfort_analysis.get("confidence", 0) > 0.7:
                    suggested_adjustment = comfort_analysis.get("suggested_adjustment", 0)
                    if abs(suggested_adjustment) > 0.5:  # Only apply significant adjustments
                        new_target = self.smart_target + suggested_adjustment
                        self.smart_target = max(65, min(80, new_target))
                        print(f"🤖 LLM suggested target adjustment: {suggested_adjustment:.1f}°F -> {self.smart_target:.1f}°F")
                        print(f"   Reasoning: {comfort_analysis.get('reasoning', 'No reasoning provided')}")

        except Exception as e:
            print(f"Error in smart feedback handling: {e}")


# Global demo manager
demo_manager = HVACDemoManager()


# ============================================================
# API ENDPOINTS
# ============================================================


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main demo page."""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    try:
        with open(html_path) as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Demo files not found</h1><p>Please run from the demos/smart_hvac directory</p>")


@app.get("/simple", response_class=HTMLResponse)
async def get_simple():
    """Serve the simplified demo page."""
    html_path = os.path.join(os.path.dirname(__file__), "static", "simple.html")
    try:
        with open(html_path) as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Simple demo not found</h1>")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    demo_manager.clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "user_input":
                user_input = UserInput(**message["data"])
                demo_manager.handle_user_input(user_input)

    except WebSocketDisconnect:
        demo_manager.clients.remove(websocket)


@app.post("/api/start")
async def start_demo():
    """Start the HVAC simulation."""
    if not demo_manager.running:
        asyncio.create_task(demo_manager.start_simulation())
    return {"status": "started"}


@app.post("/api/stop")
async def stop_demo():
    """Stop the HVAC simulation."""
    demo_manager.running = False
    return {"status": "stopped"}


@app.post("/api/reset")
async def reset_demo():
    """Reset the simulation to initial state."""
    demo_manager.basic_room.reset()
    demo_manager.smart_room.reset()
    demo_manager.comfort_controller = ComfortBasedController()
    demo_manager.basic_target = 72.0
    demo_manager.smart_target = 72.0

    # Clear metrics
    for system in ["basic", "smart"]:
        for key in demo_manager.metrics[system]:
            demo_manager.metrics[system][key].clear()

    return {"status": "reset"}


@app.get("/api/metrics/{system_id}")
async def get_metrics(system_id: str):
    """Get historical metrics for a system."""
    if system_id not in ["basic", "smart"]:
        return {"error": "Invalid system_id"}

    return demo_manager.metrics[system_id]


@app.get("/api/poet_status")
async def get_poet_status():
    """Get POET learning status and recommendations."""
    try:
        if hasattr(smart_hvac_control, "_poet_executor"):
            executor = smart_hvac_control._poet_executor
            learning_status = executor.get_learning_status()
            recommendations = executor.get_learning_recommendations()
            metrics = executor.get_metrics()

            return {
                "learning_algorithm": learning_status.get("learning_algorithm", "statistical"),
                "recommendations": recommendations,
                "poe_metrics": metrics,  # Note: frontend expects 'poe_metrics' not 'metrics'
            }
    except Exception as e:
        print(f"Error getting POET status: {e}")
        return {"error": str(e)}

    return {"status": "POET not available"}


# ============================================================
# STARTUP
# ============================================================


@app.on_event("startup")
async def startup_event():
    """Initialize the demo on startup."""
    print("🏠 Smart HVAC Demo starting...")
    print("🌐 Visit http://localhost:8000 to see the demo")

    # Initialize LLM for enhanced POET functionality
    print("🤖 Initializing LLM integration...")
    llm_success = await initialize_llm_for_demo()
    if llm_success:
        print("✅ LLM integration ready - POET will use real AI reasoning")
    else:
        print("⚠️ Running without LLM - POET features will be limited")

    # Auto-start simulation
    asyncio.create_task(demo_manager.start_simulation())


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Smart HVAC Demo Server...")
    print("🌐 Open http://localhost:8000 in your browser")
    print("⏹️ Press Ctrl+C to stop")

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
    except KeyboardInterrupt:
        print("\n👋 Demo stopped. Thanks for trying POET!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback

        traceback.print_exc()
