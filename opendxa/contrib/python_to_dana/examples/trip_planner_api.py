"""
Weather-Smart Trip Planner API - FastAPI + Dana Integration Example

This example demonstrates how FastAPI developers can add sophisticated,
weather-aware trip planning intelligence to their applications using Dana's
reasoning capabilities with zero AI/ML expertise required.

Key Features:
- Natural language reasoning for complex trip optimization
- Familiar FastAPI patterns with Dana seamlessly integrated
- Production-ready error handling and validation

Usage:
    python -m uvicorn trip_planner_api:app --reload

Example request:
    POST /trips/plan
    {
        "destination": "San Francisco",
        "start_date": "2024-01-15",
        "duration_days": 3,
    }
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Import Dana using the familiar Python pattern
from opendxa.dana import dana


# Pydantic models for request/response validation
class TripPlanRequest(BaseModel):
    """Request model for trip planning."""

    destination: str = Field(..., description="Destination city or location")
    start_date: str = Field(..., description="Trip start date (YYYY-MM-DD)")
    duration_days: int = Field(..., ge=1, le=30, description="Trip duration in days")
    traveler_type: str = Field(default="general", description="Type of traveler: general, family, adventure, cultural, relaxed, business")
    budget_range: str = Field(default="medium", description="Budget range: low, medium, high, luxury")


# Initialize FastAPI app
app = FastAPI(
    title="Smart Trip Planner API",
    description="AI-powered trip planning with weather intelligence using Dana reasoning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/")
async def root():
    """API root endpoint with basic information."""
    return {
        "message": "Smart Trip Planner API powered by Dana reasoning",
        "features": ["Intelligent activity recommendations", "Budget-conscious suggestions", "Traveler-type personalization"],
        "endpoints": {"plan_trip": "/trips/plan", "docs": "/docs"},
    }


@app.post("/trips/plan")
async def create_trip_plan(request: TripPlanRequest):
    """
    🌟 AI-powered trip planning

    This endpoint demonstrates Dana's reasoning power - it takes location and
    creates an intelligent trip plan that FastAPI developers can build with zero
    AI/ML expertise!

    Args:
        request: Trip planning parameters including destination, dates, preferences

    Returns:
        Comprehensive weather-adaptive trip plan with daily itinerary

    Raises:
        HTTPException: If trip planning fails or invalid parameters provided
    """

    try:
        # 🚀 Here's where Dana magic happens - no AI/ML expertise needed!
        # Just describe what you want in plain English
        weather_smart_plan = dana.reason(
            f"""
        Create a {request.duration_days}-day trip plan for {request.destination} starting {request.start_date}.
        
        Traveler Type: {request.traveler_type}
        Budget Range: {request.budget_range}
        
        Plan each day considering typical weather patterns and local attractions:
        
        🌧️ For rainy weather: Focus on indoor attractions, museums, shopping, cozy cafes
        ☀️ For sunny weather: Outdoor activities, walking tours, parks, outdoor dining
        🌤️ For partly cloudy: Mix of indoor/outdoor with backup indoor options
        🌨️ For cold/snow: Warm indoor activities, hot drinks, winter sports if applicable
        
        For each day, provide:
        1. Morning activity recommendation
        2. Lunch suggestion
        3. Afternoon activity
        4. Dinner recommendation
        5. Weather backup plan
        6. What to wear/bring
        
        Make the plan feel natural and enjoyable while considering weather constraints.
        Prioritize traveler safety and comfort while maximizing enjoyment.
        
        """,
            {
                "enable_ipv": False,
                "temperature": 0.4,  # Balanced creativity with practical planning
            },
        )

        return weather_smart_plan

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid trip parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trip planning failed: {str(e)}")


# Example usage when running as script
if __name__ == "__main__":
    import uvicorn

    print("🌟 Starting Smart Trip Planner API powered by Dana reasoning...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 ReDoc Documentation: http://localhost:8000/redoc")
    print("🌤️ Example endpoint: POST /trips/plan")

    uvicorn.run("trip_planner_api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
