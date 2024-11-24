"""Console-based agent implementations."""

from typing import Dict, Optional
from dxa.core.ooda_agent import OODAAgent
from dxa.core.agent_with_experts import AgentWithExperts

class ConsoleOODAAgent(OODAAgent):
    """Console implementation of OODA agent."""
    
    async def observe(self) -> None:
        """Observation phase: Gather information."""
        pass

    async def orient(self) -> None:
        """Orientation phase: Analyze information."""
        pass

    async def decide(self) -> None:
        """Decision phase: Determine next actions."""
        pass

    async def act(self) -> None:
        """Action phase: Execute actions."""
        pass

    async def start_session(self, initial_problem: Optional[str] = None):
        """Start a console-based interaction session."""
        if not initial_problem:
            initial_problem = await self._query_user(
                "Please describe the problem you need help with:"
            )
        
        self.initialize_problem(initial_problem)
        await self._solve_problem()

    async def _solve_problem(self):
        """Main problem-solving loop."""
        self.logger.info("Starting problem-solving loop")
        try:
            cycle_count = 0
            while True:
                cycle_count += 1
                self.logger.info("Starting OODA cycle %d", cycle_count)
                solution_found = await self.run_ooda_loop()
                
                if solution_found:
                    self.logger.info("Potential solution found in cycle %d", cycle_count)
                    response = await self._query_user(
                        "I believe I have a solution. Would you like to see it? (yes/no)"
                    )
                    if response.lower().startswith('y'):
                        solution = self.state.working_memory.get('last_action')
                        await self._inform_user(f"Solution: {solution}")
                        
                        if await self._confirm_solution():
                            self.logger.info("Solution accepted by user")
                            break
                
                if self._is_stuck():
                    self.logger.warning("Agent is stuck, requesting user assistance")
                    if not await self._handle_stuck():
                        self.logger.info("User chose to end session while stuck")
                        break

        except KeyboardInterrupt:
            self.logger.warning("Session interrupted by user after %d cycles", cycle_count)
            await self.handle_interruption()

    async def handle_interruption(self) -> bool:
        """Handle keyboard interrupt by providing user options."""
        menu = (
            "Session interrupted. What would you like to do?\n"
            "1. Provide feedback/guidance\n"
            "2. Review current progress\n"
            "3. Exit session\n"
            "Enter number (1-3):"
        )
        options = await self._query_user(menu)
        
        if options == "1":
            feedback = await self._query_user("Please provide your feedback or guidance:")
            self.state.agent_history.add_message("user", feedback)
            return True
        elif options == "2":
            observations = (
                self.state.observations[-3:] 
                if self.state.observations 
                else 'None'
            )
            await self._inform_user(
                f"Current problem statement: {self.state.problem_statement}\n"
                f"Current phase: {self.state.current_phase.value}\n"
                f"Recent observations: {observations}"
            )
            await self._query_user("Press Enter to continue.")
            return True
        else:
            confirm = await self._query_user("Are you sure you want to exit? (yes/no)")
            return not confirm.lower().startswith('y')

    def _is_stuck(self) -> bool:
        """Determine if the agent is stuck and needs user input."""
        # Check for repeated similar states
        if len(self.state.observations) >= 3:
            last_three = self.state.observations[-3:]
            if all(
                obs.data.get('content') == last_three[0].data.get('content')
                for obs in last_three
            ):
                return True
        
        # Check for low confidence markers
        last_decision = self.state.working_memory.get('last_decision', '')
        uncertainty_markers = ['uncertain', 'unclear', 'not sure', 'ambiguous']
        if any(marker in last_decision.lower() for marker in uncertainty_markers):
            return True
        
        # Check for lack of progress
        if self.state.working_memory.get('no_progress_count', 0) > 3:
            return True
        
        return False

    async def _query_user(self, message: str, require_response: bool = True) -> Optional[str]:
        """Get input from user with optional prompt message."""
        self.logger.debug("Querying user: %s", message)
        print(f"\nAgent: {message}")
        if require_response:
            print("Your response (Ctrl+C to interrupt): ")
            response = input("> ").strip()
            self.logger.debug("User response: %s", response)
            return response
        return None

    async def _inform_user(self, message: str):
        """Send a message to the user."""
        print(f"\nAgent: {message}")

    async def _confirm_solution(self) -> bool:
        """Confirm if the solution is satisfactory."""
        response = await self._query_user(
            "Is this solution satisfactory? (yes/no)"
        )
        return response.lower().startswith('y')

    async def _handle_stuck(self) -> bool:
        """Handle the case when the agent is stuck."""
        help_needed = self.state.working_memory.get(
            'help_needed', 
            'proceeding with the solution'
        )
        response = await self._query_user(
            f"I'm having difficulty {help_needed}. Would you like to:\n"
            "1. Provide guidance\n"
            "2. Modify the problem statement\n"
            "3. End the session\n"
            "Please choose (1-3):"
        )
        
        if response == "1":
            guidance = await self._query_user("Please provide your guidance:")
            msg = f"Guidance: {guidance}"
            self.state.agent_history.add_message("user", msg)
            return True
        elif response == "2":
            new_statement = await self._query_user(
                "Please revise the problem statement:"
            )
            self.state.problem_statement = new_statement
            return True
        return False


class ConsoleModelUsingAgent(AgentWithExperts, ConsoleOODAAgent):
    """Console implementation of Model-Using OODA agent."""
    
    async def _get_user_response(self, interaction_request: Dict) -> Optional[str]:
        """Get response from user based on interaction request."""
        try:
            role = interaction_request.get('role')
            question = interaction_request.get('question', 'No question specified')
            context = interaction_request.get('context', '')
            purpose = interaction_request.get('purpose', '')
            
            # Format the prompt with context and purpose
            prompt = f"""[User Interaction Request]
            Role: {role}
            Purpose: {purpose}
            Context: {context}
            
            Question: {question}"""
            
            # Get user response through console
            return await self._query_user(prompt)
            
        # pylint: disable=broad-exception-caught
        except Exception as e:
            self.logger.error(
                "Error getting user response: %s", 
                str(e),
                exc_info=True
            )
            return None
