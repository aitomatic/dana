from dataclasses import dataclass
from dana.libs.corelib.py_wrappers.py_reason import py_reason as reason_function
from dana.core.lang.sandbox_context import SandboxContext


def reason(prompt: str, target_type: type | None = None) -> str:
    context = SandboxContext()
    context.set("system:__current_assignment_type", target_type)
    return reason_function(context, prompt)


SENIOR_ANSWER_PROMPT = """
{description}

Topic :
---
{topic}
{subtopic}
---

Role :
---
{role}
---

Previous questions from fresher :
---
{previous_questions}
---


You can lead or drive the conversation, and doesn't need to be a passive or reactive participant in it. You can suggest topics, expand on the topic, take the conversation in new directions, offer observations, or illustrate points with its own thought experiments or concrete examples, just as a human would. You can show genuine interest in the topic of the conversation and not just in what the human thinks or in what interests them. You can offer its own observations or thoughts as they arise.

You are an expert in the domain of the topic. You are able to answer the question based on your expertise. 
Be explanatory, detailed and exhaustive with your answer. Your answer should cover all important aspects of the question : what, why and how.
You are provided with powerful tools to help you get more information. Ultilize the tools to help you answer the question as much as possible.

Question :
---
{question}
---

"""


@dataclass
class SeniorAgent:
    """Senior agent with domain expertise for answering questions"""

    topic: str
    role: str

    def __post_init__(self):
        self.description = "A senior agent with specialized knowledge in the domain of the topic."
        self.subtopic = ""
        self.previous_questions = []

    def answer_domain_question(self, question: str) -> str:
        """Answer a domain question with expert knowledge"""

        # Format previous questions for context
        previous_q_text = "\n".join([f"- {q}" for q in self.previous_questions]) if self.previous_questions else "None"

        prompt = SENIOR_ANSWER_PROMPT.format(
            description=self.description,
            topic=self.topic,
            subtopic=self.subtopic,
            role=self.role,
            previous_questions=previous_q_text,
            question=question,
        )

        # Add question to previous questions for future context
        self.previous_questions.append(question)

        return reason(prompt, target_type=str)


if __name__ == "__main__":
    agent = SeniorAgent("Investing in stock market", "Financial Analyst")

    # Answer first question
    answer1 = agent.answer_domain_question("What are the key principles of value investing?")
    print("Answer 1:", answer1)

    # Answer second question with context from first
    answer2 = agent.answer_domain_question("How do you calculate intrinsic value?")
    print("\nAnswer 2:", answer2)
