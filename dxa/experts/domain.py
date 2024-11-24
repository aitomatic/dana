"""Domain expert LLM implementation."""

from dataclasses import dataclass, field
import logging
from typing import Dict, Optional, Any
import time
import openai
from dxa.core.types import ExpertResponse

@dataclass
class DomainExpertLLM:
    """Represents a domain expert LLM with specific expertise."""
    domain: str
    llm: Any  # The OpenAI AsyncClient
    system_prompt: str
    _system_prompt_logged: bool = field(default=False)

    @classmethod
    def create(
        cls,
        domain: str,
        llm_config: Dict,
        system_prompt: Optional[str] = None
    ) -> 'DomainExpertLLM':
        """Create a new domain expert LLM."""
        llm = openai.AsyncOpenAI(**llm_config)
        if system_prompt is None:
            system_prompt = f"""You are an expert-level specialist in {domain}.
            When consulted:
            1. State your confidence level (0-100%)
            2. Provide your main points clearly
            3. Show your detailed analysis
            4. List any assumptions
            5. Note any limitations
            6. Make specific recommendations
            7. Suggest follow-up questions if needed

            Structure your response as:

            CONFIDENCE: <percentage>%

            ANALYSIS:
            - Main point 1
            - Main point 2
            ...

            DETAILS:
            <your detailed analysis>

            ASSUMPTIONS:
            - Assumption 1
            - Assumption 2
            ...

            LIMITATIONS:
            - Limitation 1
            - Limitation 2
            ...

            RECOMMENDATIONS:
            1. First recommendation (Priority: High/Medium/Low)
            2. Second recommendation (Priority: High/Medium/Low)
            ...

            FOLLOW-UP:
            - Question 1
            - Question 2
            ..."""
        return cls(domain=domain, llm=llm, system_prompt=system_prompt)

    async def query(self, prompt: str, logger: logging.Logger) -> ExpertResponse:
        """Query this domain expert and return structured response."""
        start_time = time.time()
        try:
            logger.info("\n" + "=" * 80)
            logger.info(f"👨‍🔬 EXPERT LLM CONVERSATION: {self.domain.upper()}")
            logger.info("=" * 80)
            
            if not self._system_prompt_logged:
                logger.info("📝 SYSTEM PROMPT TO EXPERT:")
                logger.info("-" * 40)
                logger.info(self.system_prompt)
                self._system_prompt_logged = True
            
            logger.info("\n📤 REQUEST TO EXPERT:")
            logger.info("-" * 40)
            logger.info(prompt)
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            logger.info("\nWaiting for expert response...")
            response = await self.llm.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            
            content = response.choices[0].message.content
            logger.info("\n📥 RESPONSE FROM EXPERT:")
            logger.info("-" * 40)
            logger.info(content)
            
            # Parse the response into structured format
            try:
                # Extract confidence
                conf_start = content.find('CONFIDENCE:')
                conf_end = content.find('%', conf_start)
                confidence = float(content[conf_start + 10:conf_end].strip()) / 100
                
                # Extract analysis
                analysis_start = content.find('ANALYSIS:')
                assumptions_start = content.find('ASSUMPTIONS:')
                analysis = content[analysis_start:assumptions_start].strip()
                
                # Extract assumptions
                limitations_start = content.find('LIMITATIONS:')
                assumptions = content[assumptions_start:limitations_start].strip()
                
                # Extract limitations
                recommendations_start = content.find('RECOMMENDATIONS:')
                limitations = content[limitations_start:recommendations_start].strip()
                
                # Extract recommendations
                follow_up_start = content.find('FOLLOW-UP:')
                recommendations = content[recommendations_start:follow_up_start].strip()
                
                # Extract follow-up
                follow_up = content[follow_up_start:].strip()
                
                expert_response = ExpertResponse(
                    confidence=confidence,
                    analysis={
                        "main_points": [p.strip() for p in analysis.split('-') if p.strip()],
                        "details": analysis,
                        "assumptions": [a.strip() for a in assumptions.split('-') if a.strip()],
                        # flake8: noqa: E741
                        "limitations": [l.strip() for l in limitations.split('-') if l.strip()]
                    },
                    recommendations=[
                        {
                            "suggestion": r.strip(),
                            "rationale": "From expert analysis",
                            "priority": "High"
                        }
                        for r in recommendations.split('\n') if r.strip()
                    ],
                    follow_up=[q.strip() for q in follow_up.split('-') if q.strip()]
                )
                
            # pylint: disable=broad-exception-caught
            except Exception as e:
                logger.warning("Failed to parse expert response: %s", str(e))
                expert_response = ExpertResponse.create_fallback(content)
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info("\n⏱️ Response time: %.2f ms", duration_ms)
            logger.info("=" * 80 + "\n")
            return expert_response
            
        finally:
            duration_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"{self.domain} expert LLM query completed",
                extra={"duration_ms": duration_ms}
            )
