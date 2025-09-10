from pydantic import BaseModel

SIMPLE_PLANNING_TEMPLATE = """
**OBJECTIVE**: [One clear sentence stating what needs to be determined]

---

**STEP 1: IDENTIFY INFORMATION NEEDED**
- [ ] [Specific information item] from [Source/Context]
- [ ] [Any additional basic information required]

---

**STEP 2: PROVIDE ANSWER**
Present the requested information clearly:
- Direct answer to the question
- Brief context if relevant
"""

MODERATE_PLANNING_TEMPLATE = """
**OBJECTIVE**: [One clear sentence stating what needs to be determined]

---

**STEP 1: GATHER REQUIRED INFORMATION**
- [ ] [Primary information source] for comprehensive understanding
- [ ] [Secondary information] for context and comparison
- [ ] [Related data points] that inform the analysis

---

**STEP 2: ANALYZE AND COMPARE**
- [ ] [Key analysis method] to process the information
- [ ] [Comparison or calculation] if needed
- [ ] [Pattern identification] or trend analysis

---

**STEP 3: DRAW CONCLUSION**
Based on the analysis:
- Synthesize findings
- Address the original question
- Provide supporting reasoning
"""

COMPLEX_PLANNING_TEMPLATE = """
**OBJECTIVE**: [One clear sentence stating what needs to be determined]

---

**STEP 1: COMPREHENSIVE DATA GATHERING**
- [ ] [Primary data sources] across all relevant areas
- [ ] [Historical context] and background information
- [ ] [Multiple perspectives] or viewpoints on the topic
- [ ] [Quantitative data] where applicable
- [ ] [Qualitative factors] that influence the analysis

---

**STEP 2: SYSTEMATIC ANALYSIS**
- [ ] [Framework or methodology] for structured analysis
- [ ] [Multiple analysis approaches] to validate findings
- [ ] [Cross-referencing] between different data sources
- [ ] [Pattern recognition] and trend identification

---

**STEP 3: SCENARIO CONSIDERATION**
- [ ] [Different scenarios] or conditions to consider
- [ ] [Assumptions and their validity] underlying the analysis
- [ ] [Risk factors] or uncertainties that may affect outcomes
- [ ] [Alternative interpretations] of the data

---

**STEP 4: SYNTHESIS AND CONCLUSION**
- [ ] [Integration] of all analysis components
- [ ] [Evidence-based reasoning] supporting conclusions
- [ ] [Confidence levels] in different aspects of the findings
- [ ] [Implications] and actionable insights
"""

CATEGORIZE_PROMPT = """
Classify this question's complexity level by considering the scope and depth required:

**SIMPLE (1-2 steps)** - Direct lookups, basic information requests:
- Questions requiring straightforward information retrieval
- Single-point data requests
- Basic factual inquiries

**MODERATE (3-4 steps)** - Analysis, comparisons, trends:
- Questions requiring some analysis or comparison
- Multi-step reasoning processes
- Pattern identification or basic calculations

**COMPLEX (5+ steps)** - Multi-faceted analysis, scenarios, projections:
- Questions requiring comprehensive analysis
- Multiple data sources and perspectives
- Scenario planning or complex reasoning
- Strategic implications or future projections

**CLASSIFICATION RULE**: 
- If question asks for basic information → SIMPLE
- If question requires analysis or comparison → MODERATE
- If question involves multiple factors, scenarios, or strategic thinking → COMPLEX

Question: {question}

Match this question to the most appropriate complexity level based on the analysis required.

Classification: [SIMPLE/MODERATE/COMPLEX]
"""

FOCUSED_PLANNING_PROMPT = """
You are creating executable plans for answering questions systematically.

**CORE RULE**: Use the provided template exactly as given.

**PLANNING REQUIREMENTS**:
- Every step must be actionable and clear
- Use specific, measurable criteria when possible
- Separate each step with --- on its own line
- Focus only on answering the specific question asked

Create your plan using the template provided.

**QUESTION COMPLEXITY**: {complexity_level}

**STRICT TEMPLATE TO FOLLOW**:
{template}

**QUESTION**: {question}

**INSTRUCTIONS**:
- You MUST follow the {complexity_level} template exactly
- Do NOT add extra steps beyond the template
- Replace bracketed placeholders with specific details for this question
- Focus on answering the specific question asked

Create your plan now:
"""


class DefaultDomain(BaseModel):
    role: str = "Generalist"
    domain: str = "General Knowledge"
    tasks: list[str] = ["Answer Questions", "Provide Analysis", "Offer Insights"]

    plan_templates: dict[str, str] = {
        "SIMPLE": SIMPLE_PLANNING_TEMPLATE,
        "MODERATE": MODERATE_PLANNING_TEMPLATE,
        "COMPLEX": COMPLEX_PLANNING_TEMPLATE,
    }

    categorize_prompt: str = CATEGORIZE_PROMPT

    def get_plan_prompt(self, question: str, category: str) -> str:
        """Generate a planning prompt based on question complexity."""
        for key, value in self.plan_templates.items():
            if key.lower() in category.lower():
                return FOCUSED_PLANNING_PROMPT.format(complexity_level=key, template=value, question=question)
        # Default to moderate if category not found
        return FOCUSED_PLANNING_PROMPT.format(complexity_level="MODERATE", template=self.plan_templates["MODERATE"], question=question)

    def get_fact_prompt(self, question: str) -> str:
        """Generate a prompt focused on extracting factual information."""
        return f"""You are an information specialist focused on identifying and extracting factual data needed to answer questions.

**OBJECTIVE**: Identify key factual information needed to answer: "{question}"

**FOCUS ON**:
- Specific data points, numbers, dates, or measurements
- Concrete facts and verified information
- Primary sources and authoritative references
- Historical data or established records
- Quantifiable metrics and statistics

**INSTRUCTIONS**:
1. Identify what factual information is essential to answer the question
2. Specify the types of data sources that would be most reliable
3. Include both current and historical context where relevant
4. Focus on measurable, objective information only
5. Avoid opinions, interpretations, or subjective assessments

**QUESTION**: {question}

**FACTUAL INFORMATION REQUIREMENTS**:
List the specific factual data needed to answer this question:"""

    def get_heuristic_prompt(self, question: str) -> str:
        """Generate a prompt focused on expert insights and best practices."""
        return f"""You are an expert consultant providing insights, best practices, and rules of thumb for complex problem-solving.

**OBJECTIVE**: Provide expert heuristics and practical wisdom relevant to: "{question}"

**FOCUS ON**:
- General principles and rules of thumb that apply
- Best practices from experienced practitioners
- Common patterns and typical approaches
- Warning signs and potential pitfalls to avoid
- Contextual factors that influence decision-making
- Expert judgment criteria and evaluation methods

**INSTRUCTIONS**:
1. Share relevant principles and established best practices
2. Provide practical rules of thumb that experts commonly use
3. Highlight important contextual factors to consider
4. Mention common mistakes or misleading indicators
5. Include guidance on when these heuristics apply vs. when they don't
6. Focus on actionable insights rather than theoretical concepts

**QUESTION**: {question}

**EXPERT INSIGHTS AND BEST PRACTICES**:
Provide the key principles, rules of thumb, and expert guidance:"""

    def get_categorize_prompt(self, question: str) -> str:
        """Generate a categorization prompt for the given question."""
        return self.categorize_prompt.format(question=question)

    def get_fresher_question_prompt(self, paths_description: str, task_descriptions: str) -> str:
        """
        Generate generic prompt for creating real-world questions based on tree paths.

        Args:
            paths_description: Description of all tree paths
            task_descriptions: Description of the role's tasks

        Returns:
            A generic prompt for generating domain-specific questions
        """
        return f"""You are a seasoned {self.role} crafting real-world questions that professionals in {self.domain} encounter daily. These questions will generate comprehensive knowledge including execution plans, critical facts, and expert heuristics.

**MISSION**: For each knowledge path in the tree, create 2-3 questions that capture the authentic challenges, dilemmas, and analytical problems this role faces. Think beyond textbook questions—what keeps this professional up at night?

**ROLE CONTEXT**: {self.role}
**DOMAIN**: {self.domain}
**DAILY RESPONSIBILITIES**:
{task_descriptions}

**KNOWLEDGE PATHWAYS** (domain → subdomain → specific topic):
{paths_description}

**🎯 QUESTION CREATIVITY FRAMEWORK**:

**DIVERSE QUESTION TYPES** (mix these creatively):

1. **HOW-TO EXECUTION**: "How to calculate/determine X when Y conditions exist?"
2. **ANALYTICAL SCENARIOS**: "Based on X situation, how much Y is needed for Z outcome?"
3. **RESOURCE PLANNING**: "How much time/resources/capital needed to achieve X given Y constraints?"
4. **DECISION FRAMEWORKS**: "When should you choose X over Y in Z situation?"
5. **RISK ASSESSMENT**: "What are the warning signs that X strategy will fail?"
6. **OPTIMIZATION**: "How to maximize X while minimizing Y under Z conditions?"
7. **COMPARATIVE ANALYSIS**: "How does X performance compare when adjusting for Y factors?"
8. **PREDICTIVE MODELING**: "What will X look like in Y timeframe based on Z trends?"
9. **STAKEHOLDER SCENARIOS**: "How to present X findings to Y audience for Z decision?"
10. **CRISIS MANAGEMENT**: "What to do when X assumptions prove wrong and Y happens?"

**🔥 REAL-WORLD EXAMPLES** (adapt to your domain):
- "Based on 20% growth in X metric, how much Y resource is needed for next period?"
- "How much investment is needed to achieve X outcome based on current Y trends?"
- "When do declining Z indicators signal fundamental problems vs. temporary issues?"
- "How to adjust X models when Y assumptions change mid-analysis?"
- "What are the early warning indicators that X strategy will hit problems?"

**💡 QUESTION GENERATION PRINCIPLES**:

1. **CONTEXT-RICH**: Include specific scenarios, percentages, timeframes, constraints
2. **MULTI-LAYERED**: Questions should require both analytical thinking and practical execution
3. **STAKEHOLDER-AWARE**: Consider different audiences (clients, management, teams, regulators)
4. **TIME-SENSITIVE**: Reflect real business urgency and decision deadlines
5. **RESOURCE-CONSTRAINED**: Acknowledge real-world limitations (budget, data, time)
6. **UNCERTAINTY-AWARE**: Include questions about incomplete information and changing conditions
7. **DOMAIN-SPECIFIC**: Use terminology and scenarios specific to this domain
8. **EXPERTISE-APPROPRIATE**: Match the sophistication level of this role

**📋 GENERATION INSTRUCTIONS**:
- Create 2-3 questions per leaf topic path
- Vary question types across the framework above
- Make each question feel like it came from a real professional situation
- Ensure questions would generate rich plans, facts, and heuristics
- Use specific numbers, percentages, timeframes when realistic
- Include edge cases and challenging scenarios

**OUTPUT FORMAT** (valid JSON):
{{
    "domain_subdomain_topic_1": {{
        "path": ["Domain", "Subdomain", "Topic"],
        "questions": [
            "Based on X scenario with specific constraints, how to determine Y outcome?",
            "When Z conditions change, what are the key indicators to monitor for A decision?",
            "How much B resource is needed to achieve C goal given D limitations?"
        ]
    }},
    "domain_subdomain_topic_2": {{
        "path": ["Domain", "Subdomain", "Topic"],
        "questions": [
            "How to optimize X process when Y constraints limit Z options?",
            "What early warning signs indicate that A strategy needs B adjustment?"
        ]
    }}
}}"""
