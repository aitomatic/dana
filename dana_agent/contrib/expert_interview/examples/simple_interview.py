#!/usr/bin/env python3
"""
Simple Expert Interview CLI

A minimal command-line interface for conducting expert interviews using
Dana's conversation and analysis resources.

Usage:
    python simple_interview.py
    python simple_interview.py --expert-name "Dr. Smith" --domain "Crystallization"
"""

import argparse
import json
import logging
import os
from pathlib import Path
import sys
import threading
import time


# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Configure logging early (before importing Dana modules)
# Check if quiet mode requested via environment variable
if os.getenv("EXPERT_INTERVIEW_QUIET", "").lower() in ["1", "true", "yes"]:
    logging.basicConfig(level=logging.CRITICAL, force=True)
    os.environ["STRUCTLOG_LEVEL"] = "CRITICAL"

from contrib.expert_interview import ExpertInterviewWorkflow


class ProgressSpinner:
    """Simple progress spinner for long-running operations"""

    def __init__(self, message: str = "Processing"):
        self.message = message
        self.running = False
        self.thread = None

    def _spin(self):
        """Spinner animation"""
        spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        idx = 0
        while self.running:
            char = spinner_chars[idx % len(spinner_chars)]
            print(f"\r{char} {self.message}...", end="", flush=True)
            idx += 1
            time.sleep(0.1)

    def start(self):
        """Start the spinner"""
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the spinner"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        print("\r" + " " * (len(self.message) + 20), end="", flush=True)
        print("\r", end="", flush=True)


class InterviewSession:
    """Manages an expert interview session"""

    def __init__(self, expert_profile: dict | None = None, reference_materials: list | None = None):
        """
        Initialize interview session.

        Args:
            expert_profile: Expert information (name, role, etc.)
            reference_materials: Optional reference documents
        """
        self.workflow = ExpertInterviewWorkflow(expert_profile=expert_profile, reference_materials=reference_materials or [])
        self.conversation_history = []
        self.expert_profile = expert_profile or {}

    def start_interview(self):
        """Start the interview session"""
        print("\n" + "=" * 70)
        print("🎤 EXPERT INTERVIEW SESSION")
        print("=" * 70)

        if self.expert_profile:
            print(f"\nExpert: {self.expert_profile.get('name', 'Anonymous')}")
            if "role" in self.expert_profile:
                print(f"Role: {self.expert_profile['role']}")
            if "domain" in self.expert_profile:
                print(f"Domain: {self.expert_profile['domain']}")

        print("\nCommands:")
        print("  Type your answer to questions")
        print("  'quit' or 'exit' - End interview")
        print("  'summary' - View conversation summary")
        print("  'context' - View current interview context")
        print("=" * 70)

    def ask_question(self, question: str):
        """Ask a question to the expert"""
        print(f"\n🤔 Interviewer: {question}")

    def process_expert_response(self, response: str, show_spinner: bool = True) -> dict:
        """
        Process expert's response through the workflow.

        Args:
            response: Expert's message
            show_spinner: Whether to show progress spinner (default: True)

        Returns:
            Analysis results
        """
        spinner = None
        if show_spinner:
            spinner = ProgressSpinner("Analyzing response")
            spinner.start()

        try:
            # Update conversation history BEFORE processing (fixes depth counter)
            self.conversation_history.append({"role": "user", "content": response})

            result = self.workflow.execute(expert_message=response, conversation_history=self.conversation_history)

            return result["result"]
        finally:
            if spinner:
                spinner.stop()

    def display_analysis(self, analysis: dict):
        """Display analysis results"""
        print("\n📊 Analysis:")

        # Show topics
        topics = analysis.get("topics", {})
        if topics.get("current_focus"):
            print(f"   Current Focus: {topics['current_focus']}")
        if topics.get("terminology"):
            print(f"   Key Terms: {', '.join(topics['terminology'][:5])}")

        # Show insights
        insights = analysis.get("insights", {})
        expert_insights = insights.get("expert_insights_original", [])
        if expert_insights:
            print(f"   Insights Captured: {len(expert_insights)}")

        # Show gaps
        gaps = analysis.get("gaps", {})
        if gaps.get("gaps"):
            print(f"   Knowledge Gaps Identified: {len(gaps['gaps'])}")

        print(f"   Processing Time: {analysis.get('processing_time', 0):.2f}s")

    def show_summary(self):
        """Show conversation summary"""
        from dana.lib.workflows.conversation import SummarizeConversationWorkflow

        spinner = ProgressSpinner("Generating summary")
        spinner.start()

        try:
            summary_workflow = SummarizeConversationWorkflow()
            result = summary_workflow.execute(conversation_history=self.conversation_history)
            summary = result["result"]
        finally:
            spinner.stop()

        print("\n" + "=" * 70)
        print("CONVERSATION SUMMARY")
        print("=" * 70)
        print(f"\nTopics Discussed: {', '.join(summary['key_topics'])}")
        print(f"Technical Areas: {', '.join(summary['technical_areas'])}")
        print(f"Conversation Stage: {summary['conversation_stage']}")
        print(f"Expertise Level: {summary['expertise_level']}")
        print(f"\nSummary: {summary['conversation_summary']}")
        print("=" * 70)

    def show_context(self, analysis: dict):
        """Show current interview context"""
        context = analysis.get("instant_context", {})

        print("\n" + "=" * 70)
        print("CURRENT INTERVIEW CONTEXT")
        print("=" * 70)
        print(f"Focus: {context.get('current_focus', 'Unknown')}")
        print(f"Topics: {', '.join(context.get('active_topics', [])[:5])}")
        print(f"Insights Captured: {len(context.get('expert_insights', []))}")
        print(f"Conversation Depth: {context.get('conversation_depth', 0)} messages")
        print("=" * 70)

    def save_session(self, filename: str = "interview_session.json"):
        """Save interview session to file"""
        session_data = {
            "expert_profile": self.expert_profile,
            "conversation_history": self.conversation_history,
        }

        with open(filename, "w") as f:
            json.dump(session_data, f, indent=2)

        print(f"\n💾 Session saved to {filename}")


def main():
    """Run interactive interview"""
    parser = argparse.ArgumentParser(description="Expert Interview CLI")
    parser.add_argument("--expert-name", help="Expert's name")
    parser.add_argument("--role", help="Expert's role")
    parser.add_argument("--domain", help="Expert's domain")
    parser.add_argument("--years-experience", type=int, help="Years of experience")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress debug logs")

    args = parser.parse_args()

    # Configure logging based on quiet flag
    if args.quiet:
        # Suppress all but critical logs
        logging.basicConfig(level=logging.CRITICAL, force=True)
        # Also suppress logs from structlog (used by Dana)
        logging.getLogger().setLevel(logging.CRITICAL)
        for logger_name in ["dana", "anthropic", "openai", "httpx"]:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
        # Suppress structlog output
        import structlog
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL),
        )

    # Build expert profile
    expert_profile = {}
    if args.expert_name:
        expert_profile["name"] = args.expert_name
    if args.role:
        expert_profile["role"] = args.role
    if args.domain:
        expert_profile["domain"] = args.domain
    if args.years_experience:
        expert_profile["years_experience"] = args.years_experience

    # Create session
    session = InterviewSession(expert_profile=expert_profile if expert_profile else None)
    session.start_interview()

    # Initial question
    session.ask_question("Can you describe your experience and what you'd like to share today?")

    # Interview loop
    analysis = None
    while True:
        try:
            response = input("\n💬 Expert: ").strip()

            if not response:
                continue

            # Handle commands
            if response.lower() in ["quit", "exit", "bye"]:
                print("\n👋 Thank you for your time!")
                save = input("Save session? (y/n): ").strip().lower()
                if save == "y":
                    session.save_session()
                break

            elif response.lower() == "summary":
                if session.conversation_history:
                    session.show_summary()
                else:
                    print("\n⚠️  No conversation to summarize yet")
                continue

            elif response.lower() == "context":
                if analysis:
                    session.show_context(analysis)
                else:
                    print("\n⚠️  No analysis available yet")
                continue

            # Process response
            analysis = session.process_expert_response(response)
            session.display_analysis(analysis)

            # Ask next question
            next_question = analysis.get("next_question", "Can you tell me more?")
            session.ask_question(next_question)

        except KeyboardInterrupt:
            print("\n\n👋 Interview interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue


if __name__ == "__main__":
    main()
