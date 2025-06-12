"""
Smart Greenhouse Demo - FastAPI Backend

Side-by-side comparison of:
- Basic Greenhouse (SENSE + ACT)
- POET-enhanced Greenhouse (SENSE + THINK + ACT)

Demonstrates POET's learning and optimization capabilities for agriculture.
"""

import asyncio
import json
import time
from typing import Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from greenhouse_systems import (
    basic_greenhouse_control,
    smart_greenhouse_control,
    PlantGrowthController,
    calculate_plant_health,
    calculate_resource_efficiency,
    POET_AVAILABLE,
)
from plant_simulator import GreenhouseSimulator


# ============================================================
# DATA MODELS
# ============================================================


class GreenhouseState(BaseModel):
    """Current state of a greenhouse system."""

    system_id: str
    plant_health: float
    growth_stage: str
    size: float
    soil_moisture: float
    temperature: float
    humidity: float
    light_level: float
    water_usage: float
    energy_usage: float
    stress_level: float
    total_yield: float


class UserInput(BaseModel):
    """User input for system control."""

    system_id: str
    action: str  # "growth_feedback", "weather_change", "nutrient_boost"
    value: str = None  # For growth_feedback: "thriving", "healthy", "stressed", "wilting"


class SystemMetrics(BaseModel):
    """Historical metrics for visualization."""

    timestamps: List[str]
    health_scores: List[float]
    growth_rates: List[float]
    water_usage: List[float]
    energy_usage: List[float]
    yields: List[float]


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(title="Smart Greenhouse Demo", version="1.0.0")

# Serve static files
import os

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ============================================================
# GLOBAL STATE
# ============================================================


def extract_greenhouse_command(result):
    """Extract greenhouse command from POET result wrapper."""
    if isinstance(result, dict) and "result" in result:
        return result["result"]
    else:
        return result


class GreenhouseDemoManager:
    """Manages both greenhouse systems and their simulations."""

    def __init__(self):
        # Plant simulators
        self.basic_greenhouse = GreenhouseSimulator(plant_type="tomato")
        self.smart_greenhouse = GreenhouseSimulator(plant_type="tomato")

        # Growth controllers
        self.growth_controller = PlantGrowthController()

        # Metrics storage
        self.metrics = {
            "basic": {"timestamps": [], "health_scores": [], "growth_rates": [], "water_usage": [], "energy_usage": [], "yields": []},
            "smart": {"timestamps": [], "health_scores": [], "growth_rates": [], "water_usage": [], "energy_usage": [], "yields": []},
        }

        # Simulation control
        self.running = False
        self.update_interval = 3.0  # seconds (accelerated time)
        self.simulation_speed = 2.0  # hours per update

        # Connected WebSocket clients
        self.clients = []

    async def start_simulation(self):
        """Start the simulation loop."""
        self.running = True
        while self.running:
            await self.update_systems()
            await asyncio.sleep(self.update_interval)

    async def update_systems(self):
        """Update both greenhouse systems and broadcast state."""
        timestamp = datetime.now().isoformat()

        # Get current conditions (shared environment)
        current_time = self.basic_greenhouse.environment.time_of_day

        # Update basic greenhouse system
        basic_command = basic_greenhouse_control(
            soil_moisture=self.basic_greenhouse.plant_state.soil_moisture,
            light_level=self.basic_greenhouse.environment.light_level,
            temperature=self.basic_greenhouse.environment.temperature,
            humidity=self.basic_greenhouse.environment.humidity,
            plant_stage=self.basic_greenhouse.plant_state.growth_stage,
            time_of_day=current_time,
        )

        # Apply watering and nutrients
        if basic_command.watering_duration > 0:
            self.basic_greenhouse.apply_watering(basic_command.watering_duration)
        if basic_command.nutrient_dose > 0:
            self.basic_greenhouse.apply_nutrients(basic_command.nutrient_dose)

        basic_state = self.basic_greenhouse.step(basic_command, self.simulation_speed)

        # Update smart greenhouse system
        smart_result = smart_greenhouse_control(
            soil_moisture=self.smart_greenhouse.plant_state.soil_moisture,
            light_level=self.smart_greenhouse.environment.light_level,
            temperature=self.smart_greenhouse.environment.temperature,
            humidity=self.smart_greenhouse.environment.humidity,
            plant_stage=self.smart_greenhouse.plant_state.growth_stage,
            time_of_day=current_time,
        )
        smart_command = extract_greenhouse_command(smart_result)

        # Apply watering and nutrients
        if smart_command.watering_duration > 0:
            self.smart_greenhouse.apply_watering(smart_command.watering_duration)
        if smart_command.nutrient_dose > 0:
            self.smart_greenhouse.apply_nutrients(smart_command.nutrient_dose)

        smart_state = self.smart_greenhouse.step(smart_command, self.simulation_speed)

        # Store metrics
        self._store_metrics("basic", timestamp, basic_state)
        self._store_metrics("smart", timestamp, smart_state)

        # Broadcast to WebSocket clients
        await self._broadcast_state()

    def _store_metrics(self, system: str, timestamp: str, state: Dict):
        """Store metrics for a system."""
        metrics = self.metrics[system]

        metrics["timestamps"].append(timestamp)
        metrics["health_scores"].append(state["plant_health"])
        metrics["growth_rates"].append(state["size"])
        metrics["water_usage"].append(state["water_usage"])
        metrics["energy_usage"].append(state["energy_usage"])
        metrics["yields"].append(state["total_yield"])

        # Keep only recent data (last 100 points)
        max_points = 100
        for key in metrics:
            if len(metrics[key]) > max_points:
                metrics[key] = metrics[key][-max_points:]

    async def _broadcast_state(self):
        """Broadcast current state to all WebSocket clients."""
        if not self.clients:
            return

        # Get POET status
        poet_status = {}
        try:
            if hasattr(smart_greenhouse_control, "_poet_executor"):
                executor = smart_greenhouse_control._poet_executor
                learning_status = executor.get_learning_status()
                recommendations = executor.get_learning_recommendations()
                metrics = executor.get_metrics()

                poet_status = {
                    "learning_algorithm": learning_status.get("learning_algorithm", "botanical_optimization"),
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

    def _get_system_state(self, system: str) -> Dict[str, Any]:
        """Get current state for a system."""
        greenhouse = self.basic_greenhouse if system == "basic" else self.smart_greenhouse

        return {
            "system_id": system,
            "plant_health": round(greenhouse.plant_state.health_score, 1),
            "growth_stage": greenhouse.plant_state.growth_stage,
            "size": round(greenhouse.plant_state.size, 2),
            "soil_moisture": round(greenhouse.plant_state.soil_moisture, 1),
            "temperature": round(greenhouse.environment.temperature, 1),
            "humidity": round(greenhouse.environment.humidity, 1),
            "light_level": round(greenhouse.environment.light_level, 1),
            "stress_level": round(greenhouse.plant_state.stress_level, 1),
            "total_yield": round(greenhouse.plant_state.total_yield, 2),
            "nutrient_level": round(greenhouse.plant_state.nutrient_level, 1),
            "stage_progress": round(greenhouse.get_growth_stage_progress(), 1),
        }

    def _get_recent_metrics(self, system: str, count: int = 20) -> Dict:
        """Get recent metrics for visualization."""
        metrics = self.metrics[system]

        return {
            "timestamps": metrics["timestamps"][-count:],
            "health_scores": metrics["health_scores"][-count:],
            "growth_rates": metrics["growth_rates"][-count:],
            "water_usage": metrics["water_usage"][-count:],
            "energy_usage": metrics["energy_usage"][-count:],
            "yields": metrics["yields"][-count:],
        }

    def handle_user_input(self, user_input: UserInput):
        """Handle user input for system control."""
        if user_input.system_id == "smart":
            if user_input.action == "growth_feedback" and user_input.value:
                # Process plant growth feedback for POET learning
                current_conditions = {
                    "soil_moisture": self.smart_greenhouse.plant_state.soil_moisture,
                    "temperature": self.smart_greenhouse.environment.temperature,
                    "humidity": self.smart_greenhouse.environment.humidity,
                    "light_level": self.smart_greenhouse.environment.light_level,
                }

                self.growth_controller.process_growth_feedback(feedback=user_input.value, current_conditions=current_conditions)

                # Future: provide feedback to POET for learning
                try:
                    if hasattr(smart_greenhouse_control, "_poet_executor"):
                        feedback_score = {"wilting": 0.2, "stressed": 0.4, "healthy": 0.8, "thriving": 1.0}.get(user_input.value, 0.5)

                        # Future: implement feedback mechanism
                        pass
                except:
                    pass


# Global demo manager
demo_manager = GreenhouseDemoManager()


# ============================================================
# API ENDPOINTS
# ============================================================


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main demo page."""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    try:
        with open(html_path, "r") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Demo files not found</h1><p>Please run from the demos/smart_greenhouse directory</p>")


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
        if websocket in demo_manager.clients:
            demo_manager.clients.remove(websocket)


@app.post("/api/start")
async def start_demo():
    """Start the greenhouse simulation."""
    if not demo_manager.running:
        asyncio.create_task(demo_manager.start_simulation())
    return {"status": "started"}


@app.post("/api/stop")
async def stop_demo():
    """Stop the greenhouse simulation."""
    demo_manager.running = False
    return {"status": "stopped"}


@app.post("/api/reset")
async def reset_demo():
    """Reset the simulation to initial state."""
    demo_manager.basic_greenhouse.reset()
    demo_manager.smart_greenhouse.reset()
    demo_manager.growth_controller = PlantGrowthController()

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
        if hasattr(smart_greenhouse_control, "_poet_executor"):
            executor = smart_greenhouse_control._poet_executor
            learning_status = executor.get_learning_status()
            recommendations = executor.get_learning_recommendations()
            metrics = executor.get_metrics()

            return {
                "learning_algorithm": learning_status.get("learning_algorithm", "botanical_optimization"),
                "recommendations": recommendations,
                "poe_metrics": metrics,
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
    print("🌱 Smart Greenhouse Demo starting...")
    print("🌐 Visit http://localhost:8001 to see the demo")

    # Auto-start simulation
    asyncio.create_task(demo_manager.start_simulation())


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Smart Greenhouse Demo Server...")
    print("🌐 Open http://localhost:8001 in your browser")
    print("⏹️ Press Ctrl+C to stop")

    try:
        uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
    except KeyboardInterrupt:
        print("\n👋 Demo stopped. Thanks for trying POET!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback

        traceback.print_exc()
