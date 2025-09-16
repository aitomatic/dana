#!/usr/bin/env python3
"""
Use Case 07: FastAPI Server

Real FastAPI server with Dana modules as **intelligent microservices**.

Business Value: AI microservice architecture
- Dana-powered API endpoints
- Clean separation of AI logic and infrastructure concerns

To run this server:
    pip install fastapi uvicorn
    python 05_intelligent_api_server.py

To test endpoints:
    python 05_intelligent_api_client.py

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import time
from typing import Any

from pydantic import BaseModel

from dana.dana import dana

# FastAPI imports
try:
    import uvicorn
    from fastapi import FastAPI, HTTPException

except ImportError:
    print("❌ FastAPI not installed. Install with: pip install fastapi uvicorn")
    exit(1)

# ============================================================================
# FastAPI Models (Request/Response schemas)
# ============================================================================


class SensorData(BaseModel):
    """Request model for sensor data"""

    temperature: float
    pressure: float
    vibration: float
    equipment_id: str
    location: str


class DiagnosisResponse(BaseModel):
    """Response model for diagnosis endpoint"""

    diagnosis: str
    recommendations: list[str]
    confidence_score: float
    severity: str
    estimated_fix_time: str
    equipment_id: str
    timestamp: float
    api_version: str


class BatchRequest(BaseModel):
    """Request model for batch processing"""

    equipment_list: list[dict[str, Any]]


class BatchResponse(BaseModel):
    """Response model for batch processing"""

    batch_size: int
    individual_results: list[dict[str, Any]]
    facility_overview: str
    processing_time: float


# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(title="Dana Intelligent Microservice", description="AI-powered microservice using Dana modules", version="1.0.0")

# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Dana Intelligent Microservice",
        "status": "running",
        "version": "1.0.0",
        "endpoints": ["/diagnose", "/batch-diagnose"],
    }


@app.post("/api/v1/diagnose", response_model=DiagnosisResponse)
async def diagnose_equipment(sensor_data: SensorData):
    """
    Intelligent equipment diagnosis endpoint

    Uses Dana AI to analyze sensor data and provide intelligent diagnosis
    with recommendations and confidence scoring.
    """
    try:
        print(f"🔍 Processing diagnosis for {sensor_data.equipment_id}")

        # Input validation
        if sensor_data.temperature < -50 or sensor_data.temperature > 300:
            raise HTTPException(status_code=400, detail="Temperature out of valid range")

        # Convert Pydantic model to dict for Dana processing
        sensor_dict = sensor_data.model_dump()

        # Dana handles the intelligent diagnosis
        print("🤖 Calling Dana AI for equipment analysis...")
        dana.enable_module_imports()

        try:
            import quality_agent  # Dana module for intelligent diagnosis

            # Dana's AI capabilities
            diagnosis = str(quality_agent.diagnose_equipment_issue(sensor_dict))
            print(f"🤖 Diagnosis: {diagnosis}")
            recommendations = quality_agent.recommend_maintenance_actions(diagnosis)
            confidence = quality_agent.calculate_confidence_score(diagnosis, sensor_dict)
            severity = quality_agent.assess_severity(diagnosis)
            estimated_fix_time = quality_agent.estimate_repair_time(diagnosis)

            print(f"   ✅ Diagnosis complete: {diagnosis}")

            # Build response
            response = DiagnosisResponse(
                diagnosis=diagnosis,
                recommendations=recommendations,
                confidence_score=confidence,
                severity=severity,
                estimated_fix_time=estimated_fix_time,
                equipment_id=sensor_data.equipment_id,
                timestamp=time.time(),
                api_version="v1",
            )

            return response

        finally:
            dana.disable_module_imports()

    except Exception as e:
        print(f"❌ Error processing diagnosis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


@app.post("/api/v1/batch-diagnose", response_model=BatchResponse)
async def batch_diagnose_equipment(batch_request: BatchRequest):
    """
    Batch processing endpoint for multiple equipment diagnosis

    Demonstrates scaling Dana intelligence across multiple requests
    with facility-wide analysis capabilities.
    """
    try:
        equipment_list = batch_request.equipment_list
        print(f"📊 Processing batch diagnosis for {len(equipment_list)} equipment units")

        if len(equipment_list) > 100:
            raise HTTPException(status_code=400, detail="Batch size too large (max 100)")

        dana.enable_module_imports()

        try:
            import quality_agent

            batch_results = []

            # Process each equipment unit
            for equipment in equipment_list:
                # Validate required fields
                required_fields = ["equipment_id", "temperature", "pressure", "vibration"]
                for field in required_fields:
                    if field not in equipment:
                        raise HTTPException(status_code=400, detail=f"Missing field: {field}")

                # Dana handles each diagnosis intelligently
                diagnosis = str(quality_agent.diagnose_equipment_issue(equipment))
                priority = str(quality_agent.prioritize_maintenance(diagnosis, equipment))

                batch_results.append(
                    {"equipment_id": equipment["equipment_id"], "diagnosis": diagnosis, "priority": priority, "processed_at": time.time()}
                )

            # Dana aggregates insights across the batch
            facility_overview = str(quality_agent.analyze_facility_health(batch_results))

            response = BatchResponse(
                batch_size=len(equipment_list),
                individual_results=batch_results,
                facility_overview=facility_overview,
                processing_time=time.time(),
            )

            print(f"   ✅ Batch processing complete: {len(batch_results)} results")
            return response

        finally:
            dana.disable_module_imports()

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


# ============================================================================
# Server Startup
# ============================================================================


def main():
    """Start the FastAPI server"""
    print("🎯 Use Case 07: Scalable Microservice Architecture")
    print("=" * 60)
    print("🚀 Starting FastAPI server with Dana intelligence...")
    print("📡 Available endpoints:")
    print("   GET  / - Service info")
    print("   POST /api/v1/diagnose - Equipment diagnosis")
    print("   POST /api/v1/batch-diagnose - Batch processing")
    print()
    print("🌐 Server will start at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")
    print("🔄 To test: python 07_microservice_client.py")
    print()

    # Start the server
    uvicorn.run("05_intelligent_api_server:app", host="127.0.0.1", port=8000, reload=True, log_level="info")


if __name__ == "__main__":
    main()
