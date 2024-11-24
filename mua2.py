def _construct_observation_prompt(self) -> str:
    """Construct prompt for the observation phase."""
    observations = (
        self.state.observations[-3:] 
        if self.state.observations 
        else 'None'
    )
    return (
        f"Current problem: {self.state.problem_statement}\n\n"
        "Based on the current state and history, what observations can you make?\n"
        "Consider:\n"
        "1. What information do we have?\n"
        "2. What information might we need?\n"
        "3. Should we consult any domain experts?\n\n"
        f"Previous observations: {observations}"
    ) 