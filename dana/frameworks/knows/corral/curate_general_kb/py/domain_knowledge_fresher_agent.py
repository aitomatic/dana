from dana.libs.corelib.py_wrappers.py_reason import py_reason as reason_function
from dana.core.lang.sandbox_context import SandboxContext
import yaml
import logging

logger = logging.getLogger(__name__)


def reason(prompt: str, target_type: type | None = None) -> str:
    context = SandboxContext()
    context.set("system:__current_assignment_type", target_type)
    return reason_function(context, prompt)


class DomainKnowledgeFresherAgent:
    def __init__(self, topic: str, role: str, confidence_threshold: float = 85.0, max_iterations: int = 10):
        self.topic = topic
        self.role = role
        self.confidence_threshold = confidence_threshold
        self.max_iterations = max_iterations

    def assess_domain_confidence(self, knowledge_area_description: str, questions: dict, previous_assessment: dict = None) -> dict:
        """Assess LLM confidence using dynamic topic-based framework"""

        # Handle None default argument
        if previous_assessment is None:
            previous_assessment = {}

        # Extract topic names from questions dict
        if previous_assessment is None:
            previous_assessment = {}
        topic_names = list(questions.keys())

        confidence_prompt = f"""
You are a senior domain expert performing a self-assessment.

OBJECTIVE: Re-evaluate your confidence that the current set of questions will let you comprehensively understand and teach this knowledge area.

KNOWLEDGE AREA: {knowledge_area_description}

QUESTIONS TO ASSESS:
{yaml.dump(questions, indent=2)}

PRIOR ASSESSMENT: {yaml.dump(previous_assessment, indent=2) if previous_assessment else "First iteration - starting at 0% confidence."}

INSTRUCTIONS:
1. Rate each topic 0-100 based on question comprehensiveness
2. Compute overall confidence as average of topic scores
3. Status: "Ready to proceed" if e85, else "More info needed"
4. Gaps: List topics whose questions are still inadequate with reasons

OUTPUT FORMAT (valid JSON):
{{
    "per_criterion": {{{", ".join([f'"{topic}": 0-100' for topic in topic_names])}}},
    "overall_confidence": 0-100,
    "status": "Ready to proceed | More info needed",
    "gaps": [["topic_name", "reason for inadequacy"]]
}}
"""

        return reason(confidence_prompt, target_type=dict)

    def generate_targeted_domain_questions(self, knowledge_area_description: str, gaps: list, existing_questions: dict) -> dict:
        """Generate additional targeted questions for gaps"""

        prompt = f"""
You are a seasoned {self.role} with expertise in {self.topic}.

OBJECTIVE: For each knowledge topic listed in gaps, write 1-2 new questions that elicit missing knowledge not covered by existing questions.

CONTEXT:
Knowledge Area: {knowledge_area_description}
Gap Topics: {gaps}

EXISTING QUESTIONS:
{yaml.dump(existing_questions, indent=2)}

OUTPUT FORMAT:
{{
    "topic_name_1": ["new question 1", "new question 2"],
    "topic_name_2": ["new question 3", "new question 4"]
}}
"""

        return reason(prompt, target_type=dict)

    def generate_initial_domain_questions(self, knowledge_area_description: str, key_topics: list = None) -> dict:
        """Generate high-quality initial questions focused on key topics"""

        if key_topics is None:
            key_topics = []
        if not key_topics:
            key_topics = ["concepts", "methods", "tools", "applications", "standards", "evaluation"]

        # Convert key topics to safe keys
        safe_topics = [topic.lower().replace(" ", "_").replace("-", "_") for topic in key_topics]

        # Build criteria section
        criteria_section = ""
        for i, topic in enumerate(key_topics, 1):
            criteria_section += f"{i}. **{topic}**  key knowledge about {topic}\n    "

        # Build output format
        output_format = "{\n"
        for i, safe_topic in enumerate(safe_topics):
            output_format += f'      "{safe_topic}": ["single focused question"]'
            if i < len(safe_topics) - 1:
                output_format += ",\n"
            else:
                output_format += "\n"
        output_format += "    }"

        prompt = f"""
You are a veteran {self.role} with deep, hands-on expertise in {self.topic}.

OBJECTIVE: Generate exactly one crisp, answerable question for each Knowledge Topic below. These will be enhanced iteratively based on confidence assessment.

KNOWLEDGE AREA CONTEXT:
" Knowledge Area   : {knowledge_area_description}
" Domain / Topic   : {self.topic}
" Role Perspective : {self.role}

KNOWLEDGE TOPICS (ask for each topic):
{criteria_section}

QUALITY RULES:
" Use domain-specific terms, tools, or standards where they add clarity.  
" Keep each question 15 20 words, one sentence, no run-ons.  
" No overlap in scope: one topic one question.  
" Phrase so a subject-matter expert can give concrete, practical knowledge.  
" Focus on learning and understanding rather than implementation steps.
" Never mention "topic," "criterion," or variable names inside the questions.  

OUTPUT FORMAT (strict)  return ONLY this:
{output_format}
"""

        return reason(prompt, target_type=dict)

    def generate_domain_questions(self, knowledge_area_description: str, key_topics: list = None) -> dict:
        """Main method to generate questions for a knowledge area until confidence threshold is reached"""

        if key_topics is None:
            key_topics = []
        print("<� Processing knowledge area")

        # Generate initial questions
        questions = self.generate_initial_domain_questions(knowledge_area_description, key_topics)

        # Ensure questions is a dictionary
        if not isinstance(questions, dict):
            print(f"Warning: Expected dictionary but got {type(questions)}. Creating fallback structure.")
            questions = {}
            # Create fallback structure with default topics
            if not key_topics:
                key_topics = ["concepts", "methods", "tools", "applications", "standards", "evaluation"]
            for topic in key_topics:
                safe_topic = topic.lower().replace(" ", "_").replace("-", "_")
                questions[safe_topic] = []

        iteration = 1
        previous_assessment = {}

        print("= Starting iterative question generation...")

        while iteration <= self.max_iterations:
            # Count total questions
            total_questions = sum(len([q for q in questions.get(topic, []) if q and q.strip()]) for topic in questions)
            print(f"   Iteration {iteration}: {total_questions} total questions across all topics")

            # Assess confidence
            confidence_result = self.assess_domain_confidence(knowledge_area_description, questions, previous_assessment)

            # Ensure confidence_result is a dictionary
            if not isinstance(confidence_result, dict):
                print(f"Warning: Expected confidence_result dictionary but got {type(confidence_result)}. Using fallback values.")
                confidence_result = {"overall_confidence": 0.0, "gaps": []}

            confidence_score = confidence_result.get("overall_confidence", 0.0)
            gaps = confidence_result.get("gaps", [])

            print(f"   Confidence: {confidence_score}%")

            # Update previous assessment
            previous_assessment = confidence_result

            # Check if threshold reached
            if confidence_score >= self.confidence_threshold:
                print(f"Target confidence {self.confidence_threshold}% achieved!")
                break

            # Generate improved questions for gaps
            if gaps:
                gap_topic_names = {}
                for gap in gaps:
                    try:
                        if isinstance(gap, list) and len(gap) > 0:
                            gap_topic_names[gap[0]] = gap[1]
                    except Exception as _:
                        # Handle string gaps
                        gap_str = str(gap)
                        for topic_key in questions:
                            if topic_key.lower() in gap_str.lower():
                                gap_topic_names[topic_key] = gap_str
                                break

                print(f"   Gap topics identified: {gap_topic_names}")

                if gap_topic_names:
                    improved_questions = self.generate_targeted_domain_questions(knowledge_area_description, gap_topic_names, questions)

                    # Ensure improved_questions is a dictionary
                    if not isinstance(improved_questions, dict):
                        print(f"Warning: Expected improved_questions dictionary but got {type(improved_questions)}. Skipping improvement.")
                        improved_questions = {}

                    # Append new questions to existing arrays
                    for topic_key, new_questions_array in improved_questions.items():
                        # Ensure new_questions_array is a list
                        if not isinstance(new_questions_array, list):
                            print(f"Warning: Expected list for topic {topic_key} but got {type(new_questions_array)}. Converting to list.")
                            new_questions_array = [str(new_questions_array)] if new_questions_array else []

                        if topic_key in questions:
                            # Ensure questions[topic_key] is a list
                            if not isinstance(questions[topic_key], list):
                                print(
                                    f"Warning: Expected list for existing topic {topic_key} but got {type(questions[topic_key])}. Converting to list."
                                )
                                questions[topic_key] = [str(questions[topic_key])] if questions[topic_key] else []

                            questions[topic_key].extend(new_questions_array)
                        else:
                            questions[topic_key] = new_questions_array

                    print(f"   Improved questions for {len(improved_questions)} topics")

            iteration += 1

        # Final assessment
        final_confidence = self.assess_domain_confidence(knowledge_area_description, questions, previous_assessment)

        # Ensure final_confidence is a dictionary
        if not isinstance(final_confidence, dict):
            print(f"Warning: Expected final_confidence dictionary but got {type(final_confidence)}. Using fallback values.")
            final_confidence = {"overall_confidence": 0.0, "per_criterion": {}}

        # Convert questions dict to flat list
        questions_list = []
        for _, question_array in questions.items():
            if question_array:
                # Ensure question_array is a list
                if isinstance(question_array, list):
                    questions_list.extend([q for q in question_array if q and q.strip()])
                else:
                    # Handle case where question_array is not a list
                    question_str = str(question_array).strip()
                    if question_str:
                        questions_list.append(question_str)

        result = {
            "knowledge_area_description": knowledge_area_description,
            "questions": questions_list,
            "questions_by_topics": questions,
            "final_confidence": final_confidence.get("overall_confidence", 0.0),
            "confidence_by_topics": final_confidence.get("per_criterion", {}),
            "iterations_used": iteration - 1,
            "total_questions": len(questions_list),
        }

        print(
            f"<� Completed! Generated {len(questions_list)} high-quality questions across {len(questions)} topics in {iteration - 1} iterations"
        )
        return result


if __name__ == "__main__":
    agent = DomainKnowledgeFresherAgent("Investing in stock market", "Financial Analyst")
    knowledge_area = "Technical Analysis - Chart patterns and trend identification"
    key_topics = ["chart_patterns", "trend_analysis", "indicators", "volume_analysis"]
    result = agent.generate_domain_questions(knowledge_area, key_topics)
    print(result)
