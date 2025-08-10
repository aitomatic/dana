"""
Smart Customer Support Systems - Basic vs POET-Enhanced

This module demonstrates sophisticated prompt optimization for customer support:
- Tone adaptation based on customer sentiment
- Context synthesis from customer history
- Escalation intelligence and prioritization
- Solution ordering by success probability

Shows the evolution from generic responses to intelligent, context-aware support.

Note: The POET-enhanced agent has been moved to smart_support_agent.py
"""

import asyncio
import concurrent.futures
import os
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Try to import LLMResource for basic agent
try:
    from dana.common.sys_resource.llm_resource import LLMRequest, LLMResource

    # Initialize LLM resource for basic agent
    basic_llm_resource = LLMResource()
    LLM_AVAILABLE = True
    print("✅ LLM resource loaded for basic agent")

except ImportError as e:
    print(f"⚠️ Could not load LLM resource: {e}")
    print("🔄 Basic agent will use template fallback")
    LLM_AVAILABLE = False


class CustomerTier(Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class IssueType(Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    FEATURE_REQUEST = "feature_request"
    COMPLAINT = "complaint"


class SentimentLevel(Enum):
    VERY_ANGRY = "very_angry"
    FRUSTRATED = "frustrated"
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"
    HAPPY = "happy"


@dataclass
class CustomerProfile:
    """Customer profile with context for personalized support."""

    customer_id: str
    name: str
    tier: CustomerTier
    account_age_months: int
    previous_contacts: int
    last_satisfaction_score: float
    preferred_contact_method: str
    technical_skill_level: str  # "beginner", "intermediate", "advanced"


@dataclass
class SupportTicket:
    """Support ticket with rich context for intelligent routing."""

    ticket_id: str
    customer: CustomerProfile
    issue_type: IssueType
    subject: str
    description: str
    sentiment: SentimentLevel
    urgency: str  # "low", "medium", "high", "critical"
    channel: str  # "chat", "email", "phone"
    attachments: list[str]
    related_tickets: list[str]


@dataclass
class SupportResponse:
    """Generated support response with metadata."""

    response_text: str
    tone: str
    escalation_recommended: bool
    estimated_resolution_time: str
    follow_up_required: bool
    confidence_score: float
    reasoning: str
    conversation_id: str = ""
    response_id: str = ""


@dataclass
class ConversationContext:
    """Track conversation history and context."""

    conversation_id: str
    ticket: SupportTicket
    messages: list[dict[str, Any]]  # List of {type: "agent"|"customer", text: str, timestamp: str}
    sentiment_history: list[SentimentLevel]
    satisfaction_trend: list[float]
    resolution_status: str = "ongoing"  # "ongoing", "resolved", "escalated"


# ============================================================
# BASIC CUSTOMER SUPPORT (No POET) - Generic Responses
# ============================================================


def basic_customer_support(ticket: SupportTicket, conversation_context: ConversationContext | None = None) -> SupportResponse:
    """
    Basic customer support using LLM with static prompts.

    Uses the same LLM as POET agent, but with fixed, non-learning prompts.
    Shows the baseline performance before POET optimization.
    """

    # Create a basic, static prompt
    basic_prompt = f"""
You are a professional customer support representative. Please respond to this customer support ticket.

Customer: {ticket.customer.name}
Issue Type: {ticket.issue_type.value}
Subject: {ticket.subject}
Description: {ticket.description}
Customer Sentiment: {ticket.sentiment.value}
Urgency: {ticket.urgency}

Please provide a helpful, professional response to address the customer's concern.
"""

    # Try to use LLM if available
    if LLM_AVAILABLE:
        response_text = _call_basic_llm(basic_prompt, ticket)
    else:
        # Fallback to templates if no LLM
        response_text = _generate_template_fallback(ticket)

    # Basic escalation logic - only for "critical" urgency
    escalation_recommended = ticket.urgency == "critical"

    # Analyze response for basic metadata
    tone = "professional"
    if ticket.sentiment in [SentimentLevel.VERY_ANGRY, SentimentLevel.FRUSTRATED]:
        tone = "empathetic"

    return SupportResponse(
        response_text=response_text,
        tone=tone,
        escalation_recommended=escalation_recommended,
        estimated_resolution_time="24-48 hours",
        follow_up_required=True,
        confidence_score=0.6,
        reasoning="Basic LLM with static prompt" if LLM_AVAILABLE else "Template fallback",
    )


def _call_basic_llm(prompt: str, ticket: SupportTicket) -> str:
    """Call LLM with basic static prompt."""
    try:
        # Check for API keys
        has_api_key = any(
            [os.getenv("OPENAI_API_KEY"), os.getenv("ANTHROPIC_API_KEY"), os.getenv("GROQ_API_KEY"), os.getenv("DEEPSEEK_API_KEY")]
        )

        if has_api_key:
            # Create LLM request
            request = LLMRequest(content=prompt)

            # Use async LLM in sync context
            def run_llm_query():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(basic_llm_resource.query(request))
                finally:
                    loop.close()

            # Run in thread to avoid event loop conflicts
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_llm_query)
                llm_response = future.result(timeout=15)  # 15 second timeout

            # Extract response text
            if hasattr(llm_response, "success") and llm_response.success:
                if hasattr(llm_response, "content"):
                    response_text = str(llm_response.content).strip()
                    if response_text:
                        print("✅ Basic LLM response generated")
                        return response_text

            print("⚠️ Basic LLM response was empty, using template fallback")
        else:
            print("⚠️ No LLM API keys found, using template fallback")

    except Exception as e:
        print(f"⚠️ Basic LLM query failed: {e}, using template fallback")

    # Fallback to template
    return _generate_template_fallback(ticket)


def _generate_template_fallback(ticket: SupportTicket) -> str:
    """Generate template-based response as fallback."""
    # Generic responses by issue type (same as before)
    if ticket.issue_type == IssueType.BILLING:
        response = "Thank you for contacting support regarding your billing inquiry. I understand you have questions about your account. Let me help you resolve this issue. Please provide your account details and I'll look into this for you."

    elif ticket.issue_type == IssueType.TECHNICAL:
        response = "Thank you for reaching out about this technical issue. I'm here to help you resolve this problem. Please try the following troubleshooting steps: 1) Restart the application 2) Clear your browser cache 3) Check your internet connection. If these steps don't work, please let me know."

    elif ticket.issue_type == IssueType.ACCOUNT:
        response = "Thank you for contacting us about your account. I'm happy to assist you with any account-related questions or issues. Please provide more details about what specific help you need with your account."

    elif ticket.issue_type == IssueType.FEATURE_REQUEST:
        response = "Thank you for your feature request. We appreciate your feedback and suggestions for improving our product. I'll forward your request to our product team for consideration."

    else:  # COMPLAINT
        response = "Thank you for bringing this to our attention. I understand you have concerns and I want to help resolve this issue for you. Please provide more details so I can better assist you."

    return response


# ============================================================
# DEMO DATA GENERATION
# ============================================================


def generate_demo_customers() -> list[CustomerProfile]:
    """Generate realistic customer profiles for demo."""
    return [
        CustomerProfile(
            customer_id="CUST001",
            name="Sarah Johnson",
            tier=CustomerTier.ENTERPRISE,
            account_age_months=24,
            previous_contacts=1,
            last_satisfaction_score=4.2,
            preferred_contact_method="email",
            technical_skill_level="intermediate",
        ),
        CustomerProfile(
            customer_id="CUST002",
            name="Mike Chen",
            tier=CustomerTier.PREMIUM,
            account_age_months=8,
            previous_contacts=4,
            last_satisfaction_score=2.8,
            preferred_contact_method="chat",
            technical_skill_level="advanced",
        ),
        CustomerProfile(
            customer_id="CUST003",
            name="Jennifer Williams",
            tier=CustomerTier.BASIC,
            account_age_months=3,
            previous_contacts=0,
            last_satisfaction_score=5.0,
            preferred_contact_method="phone",
            technical_skill_level="beginner",
        ),
        CustomerProfile(
            customer_id="CUST004",
            name="Robert Davis",
            tier=CustomerTier.ENTERPRISE,
            account_age_months=36,
            previous_contacts=6,
            last_satisfaction_score=3.1,
            preferred_contact_method="email",
            technical_skill_level="advanced",
        ),
    ]


def generate_demo_tickets(customers: list[CustomerProfile]) -> list[SupportTicket]:
    """Generate realistic support tickets for demo."""
    tickets = []

    # Billing issue - frustrated premium customer
    tickets.append(
        SupportTicket(
            ticket_id="TKT001",
            customer=customers[1],  # Mike Chen - Premium, multiple contacts
            issue_type=IssueType.BILLING,
            subject="Incorrect charges on my account AGAIN",
            description="This is the 4th time I've been charged incorrectly. My subscription is $49/month but you charged me $149. This needs to be fixed immediately.",
            sentiment=SentimentLevel.FRUSTRATED,
            urgency="high",
            channel="chat",
            attachments=["billing_screenshot.png"],
            related_tickets=["TKT987", "TKT845", "TKT723"],
        )
    )

    # Technical issue - beginner user
    tickets.append(
        SupportTicket(
            ticket_id="TKT002",
            customer=customers[2],  # Jennifer Williams - Basic, new user
            issue_type=IssueType.TECHNICAL,
            subject="App won't open on my phone",
            description="Hi, I just downloaded your app but when I try to open it, it just shows a white screen and then closes. I'm not very tech-savvy so I'm not sure what to do.",
            sentiment=SentimentLevel.NEUTRAL,
            urgency="medium",
            channel="email",
            attachments=[],
            related_tickets=[],
        )
    )

    # Complaint - enterprise customer
    tickets.append(
        SupportTicket(
            ticket_id="TKT003",
            customer=customers[3],  # Robert Davis - Enterprise, many contacts
            issue_type=IssueType.COMPLAINT,
            subject="Unacceptable service degradation",
            description="Over the past month, we've experienced multiple outages that have cost our company thousands in lost productivity. As an Enterprise customer paying $500/month, this level of service is completely unacceptable.",
            sentiment=SentimentLevel.VERY_ANGRY,
            urgency="critical",
            channel="phone",
            attachments=["outage_logs.txt", "impact_analysis.pdf"],
            related_tickets=["TKT556", "TKT445", "TKT334", "TKT223", "TKT112"],
        )
    )

    # Feature request - happy enterprise customer
    tickets.append(
        SupportTicket(
            ticket_id="TKT004",
            customer=customers[0],  # Sarah Johnson - Enterprise, good history
            issue_type=IssueType.FEATURE_REQUEST,
            subject="API integration for bulk user management",
            description="We'd love to have an API endpoint for bulk user management operations. This would help us automate our user onboarding process. Is this something on your roadmap?",
            sentiment=SentimentLevel.SATISFIED,
            urgency="low",
            channel="email",
            attachments=["integration_specs.pdf"],
            related_tickets=[],
        )
    )

    return tickets


# ============================================================
# UTILITY FUNCTIONS
# ============================================================


def calculate_satisfaction_score(response: SupportResponse, ticket: SupportTicket) -> float:
    """Simulate customer satisfaction based on response quality."""
    base_score = 3.0

    # Tone matching
    if ticket.sentiment in [SentimentLevel.VERY_ANGRY, SentimentLevel.FRUSTRATED]:
        if "sorry" in response.response_text.lower() or "apologize" in response.response_text.lower():
            base_score += 0.8
        if response.tone in ["empathetic_priority", "empathetic_urgent"]:
            base_score += 0.5

    # Personalization
    if ticket.customer.name in response.response_text:
        base_score += 0.3

    # Context awareness
    if ticket.customer.previous_contacts > 2 and "contacted us before" in response.response_text.lower():
        base_score += 0.4

    # Appropriate escalation
    if ticket.customer.tier == CustomerTier.ENTERPRISE and response.escalation_recommended:
        base_score += 0.3

    # Technical level matching
    if ticket.issue_type == IssueType.TECHNICAL:
        if ticket.customer.technical_skill_level == "beginner" and "step-by-step" in response.response_text.lower():
            base_score += 0.4
        elif ticket.customer.technical_skill_level == "advanced" and "advanced" in response.response_text.lower():
            base_score += 0.3

    return min(5.0, base_score + random.uniform(-0.2, 0.2))


def calculate_efficiency_metrics(responses: list[SupportResponse], tickets: list[SupportTicket]) -> dict[str, float]:
    """Calculate efficiency metrics for support responses."""
    escalation_rate = sum(1 for r in responses if r.escalation_recommended) / len(responses)
    avg_confidence = sum(r.confidence_score for r in responses) / len(responses)

    # Simulate resolution times (basic vs smart)
    total_resolution_hours = 0
    for response in responses:
        if "hour" in response.estimated_resolution_time:
            if "1 hour" in response.estimated_resolution_time:
                total_resolution_hours += 1
            elif "2" in response.estimated_resolution_time:
                total_resolution_hours += 3  # Average of 2-4
            elif "4-6" in response.estimated_resolution_time:
                total_resolution_hours += 5
            elif "24" in response.estimated_resolution_time:
                total_resolution_hours += 24
        else:
            total_resolution_hours += 12  # Default

    avg_resolution_time = total_resolution_hours / len(responses)

    return {
        "escalation_rate": escalation_rate,
        "avg_confidence": avg_confidence,
        "avg_resolution_time_hours": avg_resolution_time,
        "first_contact_resolution": 1 - escalation_rate,  # Inverse of escalation
    }


# ============================================================
# ADDITIONAL UTILITY FUNCTIONS
# ============================================================


def analyze_follow_up_sentiment(text: str) -> SentimentLevel:
    """Analyze sentiment of customer follow-up message."""
    text_lower = text.lower()

    # Very negative indicators
    very_negative = ["terrible", "awful", "horrible", "worst", "hate", "disgusting", "unacceptable", "ridiculous", "outrageous", "pathetic"]

    # Negative indicators
    negative = ["frustrated", "annoyed", "disappointed", "upset", "angry", "not working", "still broken", "doesn't help", "useless"]

    # Positive indicators
    positive = ["better", "working", "helpful", "thanks", "appreciate", "solved", "fixed", "great", "good", "excellent"]

    # Very positive indicators
    very_positive = ["perfect", "amazing", "fantastic", "love", "brilliant", "exactly what i needed", "problem solved", "thank you so much"]

    if any(phrase in text_lower for phrase in very_negative):
        return SentimentLevel.VERY_ANGRY
    elif any(phrase in text_lower for phrase in negative):
        return SentimentLevel.FRUSTRATED
    elif any(phrase in text_lower for phrase in very_positive):
        return SentimentLevel.HAPPY
    elif any(phrase in text_lower for phrase in positive):
        return SentimentLevel.SATISFIED
    else:
        return SentimentLevel.NEUTRAL
