"""
Smart Customer Support Demo - FastAPI Backend

Side-by-side comparison of:
- Basic Customer Support (Generic responses)
- POET-Enhanced Support (Intelligent, context-aware responses)

Demonstrates sophisticated prompt optimization for customer support scenarios.
"""

import json
import os
import time
from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from smart_support_agent import POET_AVAILABLE, SmartSupportAgent
from support_systems import (
    ConversationContext,
    CustomerProfile,
    CustomerTier,
    IssueType,
    SentimentLevel,
    SupportTicket,
    basic_customer_support,
    calculate_efficiency_metrics,
    calculate_satisfaction_score,
    generate_demo_customers,
    generate_demo_tickets,
)

# ============================================================
# DATA MODELS
# ============================================================


class TicketRequest(BaseModel):
    """Request to process a support ticket."""

    ticket_index: int  # Index into demo tickets


class CustomTicketRequest(BaseModel):
    """Request to create and process a custom support ticket."""

    customer_name: str
    customer_tier: str  # "basic", "premium", "enterprise"
    issue_type: str  # "billing", "technical", "account", "feature_request", "complaint"
    subject: str
    description: str
    sentiment: str  # "very_angry", "frustrated", "neutral", "satisfied", "happy"
    urgency: str  # "low", "medium", "high", "critical"
    previous_contacts: int
    technical_skill: str  # "beginner", "intermediate", "advanced"


class SystemMetrics(BaseModel):
    """Metrics for support system performance."""

    system_name: str
    total_tickets: int
    avg_satisfaction: float
    escalation_rate: float
    avg_resolution_time: float
    first_contact_resolution: float


class FollowUpRequest(BaseModel):
    """Request to send follow-up message in conversation."""

    conversation_id: str
    follow_up_text: str


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(title="Smart Customer Support Demo", version="1.0.0")

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ============================================================
# GLOBAL STATE
# ============================================================


class SupportDemoManager:
    """Manages both support systems and their performance tracking."""

    def __init__(self):
        # Demo data
        self.customers = generate_demo_customers()
        self.demo_tickets = generate_demo_tickets(self.customers)

        # Initialize POET agent
        self.smart_agent = SmartSupportAgent()

        # Performance tracking
        self.basic_responses = []
        self.smart_responses = []
        self.basic_tickets = []
        self.smart_tickets = []
        self.basic_satisfaction_scores = []
        self.smart_satisfaction_scores = []

        # Conversation tracking
        self.active_conversations: dict[str, ConversationContext] = {}
        self.conversation_counter = 0

        # WebSocket clients
        self.clients = []

        # Demo state
        self.current_ticket_index = 0

    def process_ticket(self, ticket: SupportTicket, use_poet: bool = False) -> dict[str, Any]:
        """Process a support ticket with either basic or POET-enhanced system."""

        start_time = time.time()

        # Create conversation context for new ticket
        self.conversation_counter += 1
        conversation_id = f"CONV_{self.conversation_counter}_{int(time.time())}"

        conversation_context = ConversationContext(
            conversation_id=conversation_id,
            ticket=ticket,
            messages=[],
            sentiment_history=[ticket.sentiment],
            satisfaction_trend=[],
            resolution_status="ongoing",
        )

        self.active_conversations[conversation_id] = conversation_context

        if use_poet:
            # POET-enhanced support
            smart_result = self.smart_agent.generate_support_response(ticket, conversation_context)

            # Handle POET result wrapper (mock decorator returns dict wrapper)
            if isinstance(smart_result, dict) and "result" in smart_result:
                response = smart_result["result"]
            else:
                response = smart_result

            execution_time = time.time() - start_time

            # Calculate satisfaction score
            satisfaction = calculate_satisfaction_score(response, ticket)

            # Store for metrics
            self.smart_responses.append(response)
            self.smart_tickets.append(ticket)
            self.smart_satisfaction_scores.append(satisfaction)

            # Add to conversation
            conversation_context.messages.append(
                {
                    "type": "agent",
                    "text": response.response_text,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "tone": response.tone,
                    "escalation": response.escalation_recommended,
                }
            )
            conversation_context.satisfaction_trend.append(satisfaction)

            return {
                "response": response,
                "satisfaction_score": satisfaction,
                "execution_time": execution_time,
                "system": "smart",
                "poet_enhanced": True,
                "conversation_id": conversation_id,
            }
        else:
            # Basic support
            response = basic_customer_support(ticket, conversation_context)
            execution_time = time.time() - start_time

            # Calculate satisfaction score
            satisfaction = calculate_satisfaction_score(response, ticket)

            # Store for metrics
            self.basic_responses.append(response)
            self.basic_tickets.append(ticket)
            self.basic_satisfaction_scores.append(satisfaction)

            # Add to conversation
            conversation_context.messages.append(
                {
                    "type": "agent",
                    "text": response.response_text,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "tone": response.tone,
                    "escalation": response.escalation_recommended,
                }
            )
            conversation_context.satisfaction_trend.append(satisfaction)

            return {
                "response": response,
                "satisfaction_score": satisfaction,
                "execution_time": execution_time,
                "system": "basic",
                "poet_enhanced": False,
                "conversation_id": conversation_id,
            }

    def get_system_metrics(self, system_type: str) -> dict[str, Any]:
        """Get performance metrics for a support system."""

        if system_type == "basic":
            responses = self.basic_responses
            tickets = self.basic_tickets
            satisfaction_scores = self.basic_satisfaction_scores
        else:
            responses = self.smart_responses
            tickets = self.smart_tickets
            satisfaction_scores = self.smart_satisfaction_scores

        if not responses:
            return {
                "total_tickets": 0,
                "avg_satisfaction": 0.0,
                "escalation_rate": 0.0,
                "avg_resolution_time": 0.0,
                "first_contact_resolution": 0.0,
            }

        metrics = calculate_efficiency_metrics(responses, tickets)

        return {
            "total_tickets": len(responses),
            "avg_satisfaction": sum(satisfaction_scores) / len(satisfaction_scores),
            "escalation_rate": metrics["escalation_rate"],
            "avg_resolution_time": metrics["avg_resolution_time_hours"],
            "first_contact_resolution": metrics["first_contact_resolution"],
        }

    def get_poet_status(self) -> dict[str, Any]:
        """Get POET learning status for smart support system."""
        try:
            if hasattr(self.smart_agent.generate_support_response, "_poet_executor"):
                executor = self.smart_agent.generate_support_response._poet_executor
                learning_status = executor.get_learning_status()

                return {
                    "learning_algorithm": learning_status.get("learning_algorithm", "customer_support_optimization"),
                    "status": learning_status.get("status", "Learning..."),
                    "executions": learning_status.get("executions", 0),
                    "escalation_rate": learning_status.get("escalation_rate", 0.25),
                    "context_accuracy": learning_status.get("context_accuracy", 0.6),
                    "tone_matching": learning_status.get("tone_matching", 0.5),
                }
        except Exception as e:
            print(f"Error getting POET status: {e}")

        return {"status": "POET not available"}

    def create_custom_ticket(self, request: CustomTicketRequest) -> SupportTicket:
        """Create a custom support ticket from user input."""

        # Create customer profile
        customer = CustomerProfile(
            customer_id=f"CUSTOM_{int(time.time())}",
            name=request.customer_name,
            tier=CustomerTier(request.customer_tier),
            account_age_months=12,  # Default
            previous_contacts=request.previous_contacts,
            last_satisfaction_score=3.5,  # Default
            preferred_contact_method="email",  # Default
            technical_skill_level=request.technical_skill,
        )

        # Create support ticket
        ticket = SupportTicket(
            ticket_id=f"CUSTOM_{int(time.time() * 1000)}",
            customer=customer,
            issue_type=IssueType(request.issue_type),
            subject=request.subject,
            description=request.description,
            sentiment=SentimentLevel(request.sentiment),
            urgency=request.urgency,
            channel="web",
            attachments=[],
            related_tickets=[],
        )

        return ticket

    def process_follow_up(self, conversation_id: str, follow_up_text: str) -> dict[str, Any]:
        """Process customer follow-up in existing conversation."""

        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation_context = self.active_conversations[conversation_id]
        start_time = time.time()

        # For now, just create simple follow-up responses
        # This could be enhanced to handle real follow-ups with the agent
        basic_response = basic_customer_support(conversation_context.ticket, conversation_context)
        smart_result = self.smart_agent.generate_support_response(conversation_context.ticket, conversation_context)

        # Handle POET result wrapper
        if isinstance(smart_result, dict) and "result" in smart_result:
            smart_response = smart_result["result"]
        else:
            smart_response = smart_result

        execution_time = time.time() - start_time

        # Calculate satisfaction scores
        basic_satisfaction = calculate_satisfaction_score(basic_response, conversation_context.ticket)
        smart_satisfaction = calculate_satisfaction_score(smart_response, conversation_context.ticket)

        # Store for metrics
        self.basic_responses.append(basic_response)
        self.smart_responses.append(smart_response)
        self.basic_satisfaction_scores.append(basic_satisfaction)
        self.smart_satisfaction_scores.append(smart_satisfaction)

        # Update conversation satisfaction trend
        conversation_context.satisfaction_trend.extend([basic_satisfaction, smart_satisfaction])

        return {
            "basic_result": {
                "response_text": basic_response.response_text,
                "tone": basic_response.tone,
                "escalation_recommended": basic_response.escalation_recommended,
                "estimated_resolution_time": basic_response.estimated_resolution_time,
                "confidence_score": basic_response.confidence_score,
                "satisfaction_score": basic_satisfaction,
                "reasoning": basic_response.reasoning,
            },
            "smart_result": {
                "response_text": smart_response.response_text,
                "tone": smart_response.tone,
                "escalation_recommended": smart_response.escalation_recommended,
                "estimated_resolution_time": smart_response.estimated_resolution_time,
                "confidence_score": smart_response.confidence_score,
                "satisfaction_score": smart_satisfaction,
                "reasoning": smart_response.reasoning,
            },
            "conversation_context": {
                "conversation_id": conversation_id,
                "message_count": len(conversation_context.messages),
                "current_sentiment": (
                    conversation_context.sentiment_history[-1].value if conversation_context.sentiment_history else "neutral"
                ),
                "resolution_status": conversation_context.resolution_status,
            },
            "execution_time": execution_time,
        }

    async def broadcast_metrics(self):
        """Broadcast current metrics to all WebSocket clients."""
        if not self.clients:
            return

        message = {
            "type": "metrics_update",
            "timestamp": datetime.now().isoformat(),
            "basic_metrics": self.get_system_metrics("basic"),
            "smart_metrics": self.get_system_metrics("smart"),
            "poet_status": self.get_poet_status(),
        }

        # Send to all clients
        disconnected = []
        for client in self.clients:
            try:
                await client.send_text(json.dumps(message))
            except Exception:
                disconnected.append(client)

        # Remove disconnected clients
        for client in disconnected:
            self.clients.remove(client)


# Global demo manager
demo_manager = SupportDemoManager()


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
        return HTMLResponse("<h1>Demo files not found</h1><p>Please run from the demos/smart_support directory</p>")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    demo_manager.clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "process_ticket":
                # Process ticket with both systems
                ticket_index = message["ticket_index"]
                ticket = demo_manager.demo_tickets[ticket_index]

                # Process with both systems
                basic_result = demo_manager.process_ticket(ticket, use_poet=False)
                smart_result = demo_manager.process_ticket(ticket, use_poet=True)

                # Send results
                response = {
                    "type": "ticket_processed",
                    "ticket": {
                        "ticket_id": ticket.ticket_id,
                        "customer_name": ticket.customer.name,
                        "customer_tier": ticket.customer.tier.value,
                        "issue_type": ticket.issue_type.value,
                        "subject": ticket.subject,
                        "description": ticket.description,
                        "sentiment": ticket.sentiment.value,
                        "urgency": ticket.urgency,
                        "previous_contacts": ticket.customer.previous_contacts,
                    },
                    "basic_result": {
                        "response_text": basic_result["response"].response_text,
                        "tone": basic_result["response"].tone,
                        "escalation_recommended": basic_result["response"].escalation_recommended,
                        "estimated_resolution_time": basic_result["response"].estimated_resolution_time,
                        "confidence_score": basic_result["response"].confidence_score,
                        "satisfaction_score": basic_result["satisfaction_score"],
                        "reasoning": basic_result["response"].reasoning,
                    },
                    "smart_result": {
                        "response_text": smart_result["response"].response_text,
                        "tone": smart_result["response"].tone,
                        "escalation_recommended": smart_result["response"].escalation_recommended,
                        "estimated_resolution_time": smart_result["response"].estimated_resolution_time,
                        "confidence_score": smart_result["response"].confidence_score,
                        "satisfaction_score": smart_result["satisfaction_score"],
                        "reasoning": smart_result["response"].reasoning,
                    },
                    "conversation_ids": {"basic": basic_result.get("conversation_id"), "smart": smart_result.get("conversation_id")},
                }

                await websocket.send_text(json.dumps(response))
                await demo_manager.broadcast_metrics()

            elif message["type"] == "send_follow_up":
                # Process follow-up message
                conversation_id = message["conversation_id"]
                follow_up_text = message["follow_up_text"]

                try:
                    follow_up_result = demo_manager.process_follow_up(conversation_id, follow_up_text)

                    response = {
                        "type": "follow_up_processed",
                        "conversation_id": conversation_id,
                        "customer_message": follow_up_text,
                        "basic_result": follow_up_result["basic_result"],
                        "smart_result": follow_up_result["smart_result"],
                        "conversation_context": follow_up_result["conversation_context"],
                    }

                    await websocket.send_text(json.dumps(response))
                    await demo_manager.broadcast_metrics()

                except Exception as e:
                    error_response = {"type": "error", "message": f"Error processing follow-up: {str(e)}"}
                    await websocket.send_text(json.dumps(error_response))

            elif message["type"] == "process_custom_ticket":
                # Process custom ticket
                ticket_data = message["ticket_data"]
                custom_request = CustomTicketRequest(**ticket_data)
                ticket = demo_manager.create_custom_ticket(custom_request)

                # Process with both systems
                basic_result = demo_manager.process_ticket(ticket, use_poet=False)
                smart_result = demo_manager.process_ticket(ticket, use_poet=True)

                # Send results (same format as above)
                response = {
                    "type": "ticket_processed",
                    "ticket": {
                        "ticket_id": ticket.ticket_id,
                        "customer_name": ticket.customer.name,
                        "customer_tier": ticket.customer.tier.value,
                        "issue_type": ticket.issue_type.value,
                        "subject": ticket.subject,
                        "description": ticket.description,
                        "sentiment": ticket.sentiment.value,
                        "urgency": ticket.urgency,
                        "previous_contacts": ticket.customer.previous_contacts,
                    },
                    "basic_result": {
                        "response_text": basic_result["response"].response_text,
                        "tone": basic_result["response"].tone,
                        "escalation_recommended": basic_result["response"].escalation_recommended,
                        "estimated_resolution_time": basic_result["response"].estimated_resolution_time,
                        "confidence_score": basic_result["response"].confidence_score,
                        "satisfaction_score": basic_result["satisfaction_score"],
                        "reasoning": basic_result["response"].reasoning,
                    },
                    "smart_result": {
                        "response_text": smart_result["response"].response_text,
                        "tone": smart_result["response"].tone,
                        "escalation_recommended": smart_result["response"].escalation_recommended,
                        "estimated_resolution_time": smart_result["response"].estimated_resolution_time,
                        "confidence_score": smart_result["response"].confidence_score,
                        "satisfaction_score": smart_result["satisfaction_score"],
                        "reasoning": smart_result["response"].reasoning,
                    },
                    "conversation_ids": {"basic": basic_result.get("conversation_id"), "smart": smart_result.get("conversation_id")},
                }

                await websocket.send_text(json.dumps(response))
                await demo_manager.broadcast_metrics()

    except WebSocketDisconnect:
        demo_manager.clients.remove(websocket)


@app.get("/api/demo_tickets")
async def get_demo_tickets():
    """Get list of demo tickets for selection."""
    tickets = []
    for i, ticket in enumerate(demo_manager.demo_tickets):
        tickets.append(
            {
                "index": i,
                "ticket_id": ticket.ticket_id,
                "customer_name": ticket.customer.name,
                "customer_tier": ticket.customer.tier.value,
                "issue_type": ticket.issue_type.value,
                "subject": ticket.subject,
                "sentiment": ticket.sentiment.value,
                "urgency": ticket.urgency,
                "description": ticket.description[:100] + "..." if len(ticket.description) > 100 else ticket.description,
            }
        )
    return {"tickets": tickets}


@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics."""
    return {
        "basic_metrics": demo_manager.get_system_metrics("basic"),
        "smart_metrics": demo_manager.get_system_metrics("smart"),
        "poet_status": demo_manager.get_poet_status(),
    }


@app.post("/api/reset")
async def reset_demo():
    """Reset the demo to initial state."""
    demo_manager.basic_responses.clear()
    demo_manager.smart_responses.clear()
    demo_manager.basic_tickets.clear()
    demo_manager.smart_tickets.clear()
    demo_manager.basic_satisfaction_scores.clear()
    demo_manager.smart_satisfaction_scores.clear()

    return {"status": "reset"}


# ============================================================
# STARTUP
# ============================================================


@app.on_event("startup")
async def startup_event():
    """Initialize the demo on startup."""
    print("🎧 Smart Customer Support Demo starting...")
    print("🌐 Visit http://localhost:8002 to see the demo")
    print(f"📊 POET Integration: {POET_AVAILABLE}")


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Smart Customer Support Demo Server...")
    print("🌐 Open http://localhost:8002 in your browser")
    print("⏹️ Press Ctrl+C to stop")

    try:
        uvicorn.run(app, host="0.0.0.0", port=8002, reload=False)
    except KeyboardInterrupt:
        print("\n👋 Demo stopped. Thanks for trying POET!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback

        traceback.print_exc()
