from .default_domain import DefaultDomain

SIMPLE_PLANNING_TEMPLATE = """
**OBJECTIVE**: [One clear sentence stating what needs to be determined]

---

**STEP 1: EXTRACT DATA**
- [ ] [Specific data item] from [Source] for latest period AND historical context

---

**STEP 2: PROVIDE ANSWER**
Present the requested information with:
- Latest period value with label (e.g., "Q4 2024: $X")
- Brief historical context if relevant
"""

MODERATE_PLANNING_TEMPLATE = """
**OBJECTIVE**: [One clear sentence stating what needs to be determined]

---

**STEP 1: EXTRACT REQUIRED DATA**
- [ ] [Data item 1] from [Statement] for ALL available periods (Q1, Q2, Q3, Q4)
- [ ] [Data item 2] from [Statement] for ALL available periods with labels

---

**STEP 2: CALCULATE KEY METRICS**
For EACH period:
- [ ] [Metric Name] = [Formula] (Q1: X, Q2: Y, Q3: Z, Q4: W)
- [ ] [Additional calculations with period labels]

---

**STEP 3: ANALYZE AND CONCLUDE**
Apply decision criteria based on:
- Latest period values
- Historical trends across periods
- Answer the original question with temporal context
"""

COMPLEX_PLANNING_TEMPLATE = """
**OBJECTIVE**: [One clear sentence stating what needs to be determined]

---

**STEP 1: EXTRACT BASE DATA**
- [ ] ALL relevant financial metrics from statements for ALL available quarters/years  
- [ ] For growth questions: Revenue data across periods
- [ ] For profitability questions: Revenue AND expense data across periods
- [ ] For funding/cash requirement questions: Revenue, expenses, AND current cash position
- [ ] If question mentions both growth AND cash needs: Treat as funding question with growth assumptions
- [ ] Ensure complete time series with period labels (Q1 2024, Q2 2024, etc.)

---

**STEP 2: ESTABLISH BASELINE METRICS** 
- [ ] Calculate current state metrics for EACH period
- [ ] Calculate relevant rates: growth rates, burn rates, profitability margins
- [ ] Perform trend analysis across ALL periods
- [ ] Identify patterns, seasonality, or anomalies

---

**STEP 3: BUILD ASSUMPTIONS**
- [ ] Derive assumptions from historical multi-period data
- [ ] For growth questions: Calculate growth rates from period-over-period analysis
- [ ] For funding questions: Determine burn rate and profitability trajectory  
- [ ] If growth rate is provided in question: Use that rate instead of historical calculation
- [ ] Document which periods inform each assumption

---

**STEP 4: PERFORM PROJECTIONS**
- [ ] Project future periods based on historical patterns OR provided growth rates
- [ ] For funding questions: Project path to profitability and cash requirements
- [ ] If specific growth rate mentioned: Apply that rate to revenue projections
- [ ] Model scenarios using different growth assumptions
- [ ] Maintain period labeling in projections (Q1 2025, Q2 2025, etc.)

---

**STEP 5: ANALYZE REQUIREMENTS**
- [ ] Calculate requirements based on multi-period projections
- [ ] For funding questions: Total cash needed = Projected losses + Current cash gap
- [ ] Consider timing of cash flows across periods
- [ ] Account for seasonal variations if present

---

**STEP 6: DRAW COMPREHENSIVE CONCLUSION**
Synthesize findings using:
- Historical multi-period trends  
- Projected future periods
- Clear temporal context throughout
"""

CATEGORIZE_PROMPT = """
Classify this financial question's complexity level by matching it to the examples below:

**SIMPLE (1-2 steps)** - Direct lookups or single calculations:
- "What is the revenue for Q4 2024?"
- "What is the cash position at end of 2024?"
- "What is the current ratio?"

**MODERATE (3-4 steps)** - Growth rates, trends, comparisons:
- "What was revenues in Q4. What is growth rate (compute)."
- "What is the quarterly revenue growth rate?"
- "Is profitability improving?"
- "How has cash position changed over the year?"

**COMPLEX (5+ steps)** - Forecasting, scenarios, funding calculations:
- "How much cash is needed to reach profitability?"
- "What happens to runway if growth slows by 20%?"
- "Can the company self-fund its growth?"

**CLASSIFICATION RULE**: 
- If question asks for growth rate or growth calculation → MODERATE
- If question asks "what if" or future projections → COMPLEX
- If question is simple lookup → SIMPLE

Question: {question}

Match this question to the most similar example above.

Return only the following classification: [SIMPLE/MODERATE/COMPLEX]
"""

FOCUSED_PLANNING_PROMPT = """
You are a {role} creating executable financial analysis plans.

**CORE RULE**: Use the provided template exactly as given.

**PLANNING REQUIREMENTS**:
- Every step must be executable with basic financial knowledge
- Use quantitative criteria, avoid subjective assessments  
- Separate each step with --- on its own line
- Focus only on answering the specific question

Create your plan using the template provided.

**QUESTION COMPLEXITY**: {complexity_level}

**STRICT TEMPLATE TO FOLLOW**:
{template}

**QUESTION**: {question}

**INSTRUCTIONS**:
- You MUST follow the {complexity_level} template exactly
- Do NOT add extra steps beyond the template
- Focus on answering the specific question asked

Create your plan now:
"""


class FinancialStmtAnalysisDomain(DefaultDomain):
    role: str = "Senior Financial Statement Analyst"
    domain: str = "Financial Statement Analysis"
    tasks: list[str] = [
        "Analyze Financial Statements",
        "Provide Financial Insights",
        "Answer Financial Questions",
        "Forecast Financial Performance",
    ]

    plan_templates: dict[str, str] = {
        "SIMPLE": SIMPLE_PLANNING_TEMPLATE,
        "MODERATE": MODERATE_PLANNING_TEMPLATE,
        "COMPLEX": COMPLEX_PLANNING_TEMPLATE,
    }

    categorize_prompt: str = CATEGORIZE_PROMPT

    def get_plan_prompt(self, question: str, category: str) -> str:
        for key, value in self.plan_templates.items():
            if key.lower() in category.lower():
                return FOCUSED_PLANNING_PROMPT.format(role=self.role, complexity_level=key, template=value, question=question)
        raise ValueError(f"No plan template found for category: {category}")

    def get_fact_prompt(self, question: str) -> str:
        """Generate a prompt focused on extracting factual data relevant to the question."""
        return f"""You are a {self.role} specializing in {self.domain}. Your role is to identify and extract specific factual information needed to answer the given question.

**OBJECTIVE**: Extract key factual data points needed to answer the question: "{question}"

**FOCUS ON**:
- Specific numerical values (revenue, expenses, cash, ratios, etc.)
- Exact dates and time periods
- Concrete financial statement line items
- Historical data points for trend analysis
- Quantitative metrics and calculations

**INSTRUCTIONS**:
1. Identify what factual data is needed from financial statements
2. Specify exact line items or calculations required
3. Include both current period and historical context where relevant
4. Be specific about data sources (Income Statement, Balance Sheet, Cash Flow)
5. Focus on measurable, objective information only

**QUESTION**: {question}

**FACTUAL DATA REQUIREMENTS**:
List the specific factual information needed:"""

    def get_heuristic_prompt(self, question: str) -> str:
        """Generate a prompt focused on expert rules of thumb and best practices."""
        return f"""You are a {self.role} with expertise in {self.domain}, providing expert insights and rules of thumb for financial analysis.

**OBJECTIVE**: Provide expert heuristics and best practices relevant to: "{question}"

**FOCUS ON**:
- Industry standard benchmarks and thresholds
- Rules of thumb used by experienced analysts
- Best practices for financial interpretation
- Warning signs and red flags to watch for
- Context and qualitative factors that matter
- Expert judgment criteria

**INSTRUCTIONS**:
1. Share relevant industry benchmarks and standards
2. Provide rules of thumb that experienced analysts use
3. Highlight qualitative factors that influence interpretation
4. Mention common pitfalls or misleading indicators
5. Include context about when these heuristics apply vs. don't apply

**QUESTION**: {question}

**EXPERT HEURISTICS AND INSIGHTS**:
Provide the key rules of thumb and expert insights:"""

    def get_categorize_prompt(self, question: str) -> str:
        return self.categorize_prompt.format(question=question)

    def get_fresher_question_prompt(self, paths_description: str, task_descriptions: str) -> str:
        """
        Generate specialized prompt for creating real-world financial analysis questions.

        Args:
            paths_description: Description of all tree paths
            task_descriptions: Description of the role's tasks

        Returns:
            A specialized prompt for generating financial analysis questions
        """
        return f"""You are a seasoned {self.role} crafting real-world questions that financial professionals encounter daily in corporate finance, investment analysis, and financial planning. These questions will generate comprehensive knowledge including execution plans, critical facts, and expert heuristics.

**MISSION**: For each knowledge path in the tree, create 2-3 questions that capture the authentic challenges, dilemmas, and analytical problems this role faces. Think beyond textbook questions—what keeps financial analysts up at night?

**ROLE CONTEXT**: {self.role}
**DOMAIN**: {self.domain}
**DAILY RESPONSIBILITIES**:
{task_descriptions}

**KNOWLEDGE PATHWAYS** (domain → subdomain → specific topic):
{paths_description}

**🎯 FINANCIAL ANALYSIS QUESTION FRAMEWORK**:

**DIVERSE QUESTION TYPES** (mix these creatively for financial scenarios):

1. **CASH FLOW ANALYSIS**: "Based on X% revenue growth, how much cash does the company need for Y period?"
2. **GROWTH SUSTAINABILITY**: "How much capital is required to fund X% growth while maintaining Y margins?"
3. **FINANCIAL HEALTH DIAGNOSTICS**: "When do declining margins signal fundamental problems vs. temporary issues?"
4. **VALUATION CHALLENGES**: "How to adjust DCF models when growth assumptions change mid-analysis?"
5. **LIQUIDITY MANAGEMENT**: "What are early warning signs of cash flow problems in high-growth companies?"
6. **RATIO INTERPRETATION**: "How to interpret P/E ratios when comparing companies across different growth stages?"
7. **TREND ANALYSIS**: "When does revenue volatility indicate business model issues vs. market conditions?"
8. **WORKING CAPITAL**: "How much working capital increase is normal for X% revenue growth?"
9. **DEBT CAPACITY**: "What debt levels are sustainable given current cash generation patterns?"
10. **PROFITABILITY ANALYSIS**: "How to distinguish between margin compression and pricing power loss?"

**🔥 FINANCIAL-SPECIFIC EXAMPLES** (for inspiration):
- "Based on 20% quarterly revenue growth but declining profit margins, how much additional working capital will be needed to maintain growth trajectory?"
- "How much cash is needed to fund this company to profitability based on current burn rate and growth trajectory?"
- "When revenue growth decelerates from 25% to 10% over two quarters, what are the key diagnostic ratios to examine first?"
- "How to assess whether a company's 15% ROIC is sustainable given industry consolidation trends?"
- "What free cash flow yield justifies investing in a company with volatile earnings?"

**💡 FINANCIAL QUESTION GENERATION PRINCIPLES**:

1. **NUMBERS-DRIVEN**: Include specific percentages, ratios, growth rates, timeframes
2. **SCENARIO-BASED**: Present realistic business situations with constraints and trade-offs
3. **STAKEHOLDER-FOCUSED**: Consider perspectives of investors, lenders, management, analysts
4. **TIME-CRITICAL**: Reflect quarterly reporting cycles, budget planning, investment decisions
5. **MARKET-AWARE**: Include industry context, competitive dynamics, economic conditions
6. **RISK-CONSCIOUS**: Address uncertainty, volatility, and downside scenarios
7. **REGULATION-AWARE**: Consider GAAP implications, SEC requirements, audit considerations
8. **STRATEGY-LINKED**: Connect financial metrics to business strategy and operational decisions

**📋 GENERATION INSTRUCTIONS FOR FINANCIAL ANALYSIS**:
- Create 2-3 questions per leaf topic path
- Use realistic financial scenarios with specific metrics
- Include growth rates, margins, ratios, and timeframes
- Address both upside opportunities and downside risks
- Consider different company stages (startup, growth, mature, turnaround)
- Include cross-functional implications (operations, strategy, capital allocation)

**OUTPUT FORMAT** (valid JSON):
{{
    "financial_statement_analysis_trend_analysis_revenue_patterns": {{
        "path": ["Financial Statement Analysis", "Trend Analysis", "Revenue Growth Patterns"],
        "questions": [
            "Based on 15% quarterly revenue growth but declining gross margins from 45% to 38%, how much additional working capital will be required to sustain this growth trajectory over the next 12 months?",
            "When a SaaS company's revenue growth decelerates from 40% to 25% over two quarters while customer acquisition costs remain flat, what are the key leading indicators to determine if this represents market saturation or execution issues?",
            "How to distinguish between seasonal revenue fluctuations of 30-40% and fundamental demand shifts that require strategic pivoting?"
        ]
    }},
    "financial_statement_analysis_cashflow_analysis_operating_trends": {{
        "path": ["Financial Statement Analysis", "Cash Flow Analysis", "Operating Cash Flow Trends"],
        "questions": [
            "What level of free cash flow deterioration can a high-growth company sustain before equity dilution becomes necessary, given current market conditions?",
            "Based on operating cash flow declining 20% while revenue grows 15%, what are the most critical working capital components to analyze first?"
        ]
    }}
}}"""
