# LLM as Judge: Evaluation Guide for Semiconductor Dispensing AI Agents

This guide explains how to use Large Language Models (LLMs) as judges to evaluate AI agents' performance in semiconductor dispensing optimization tasks using our testset.

## 📋 Overview

**LLM as Judge** is an evaluation methodology where a capable LLM evaluates the responses of AI agents being tested. This approach is particularly effective for domain-specific technical tasks where traditional metrics may not capture nuanced quality aspects.

### **Why LLM as Judge for Dispensing Optimization?**

✅ **Technical Accuracy**: Judges can assess semiconductor physics compliance  
✅ **Parameter Reasoning**: Evaluates logical relationships between inputs and outputs  
✅ **Domain Knowledge**: Leverages extensive engineering knowledge in evaluation  
✅ **Scalable Assessment**: Automated evaluation across large test sets  
✅ **Nuanced Scoring**: Goes beyond simple pass/fail to graduated assessments  

---

## 🎯 Evaluation Framework

### **Single-Phase Evaluation Strategy**

#### **Use Case 1: Initial Recipe Generation**
**Task**: Evaluate AI agent's ability to generate dispensing parameters from product specifications by comparing against validated reference solutions from historical optimization data

---

## 🧪 Use Case 1: Initial Recipe Generation Evaluation

### **Judge Prompt Template**

```markdown
You are an expert Field Application Engineer with 15+ years of experience in semiconductor dispensing optimization. You will evaluate an AI agent's parameter accuracy by comparing against a validated reference solution.

## EVALUATION TASK
The AI agent generated dispensing parameters for the given specification. Score how accurately the AI matches the proven reference solution from historical optimization data.

## INPUT SPECIFICATION
{input_specification}

## AI AGENT OUTPUT
{ai_agent_response}

## VALIDATED REFERENCE SOLUTION
{expected_output}

## EVALUATION CRITERIA

### 1. Parameter Accuracy (60 points)
Compare AI parameters to reference values using this scoring:
- **50-60**: Within ±10% for most critical parameters (pressure, valve time, height)
- **40-49**: Within ±15% for most parameters, ±25% for less critical  
- **30-39**: Within ±25% for most parameters, some ±40% deviations
- **20-29**: Within ±40% for most parameters, some larger deviations
- **0-19**: Major deviations >40% from reference

### 2. Recipe Completeness (25 points)
- Are all required categories provided (vision, motion, dispensing)?
- Are values formatted properly with appropriate precision?
- **20-25**: Complete with proper structure
- **15-19**: Mostly complete, minor formatting issues
- **10-14**: Some missing parameters or poor formatting
- **0-9**: Major gaps or structural problems

### 3. Technical Reasonableness (15 points)
- Do parameter values make sense for the material and package type?
- Are parameter combinations technically feasible?
- **12-15**: All values technically sound
- **8-11**: Most values reasonable, minor concerns
- **4-7**: Some questionable parameter choices
- **0-3**: Multiple unrealistic or problematic values

## PARAMETER DEVIATION CALCULATION
Calculate % deviation for key parameters:
- Air Pressure: |AI_value - Reference_value| / Reference_value * 100%
- Valve Time: |AI_value - Reference_value| / Reference_value * 100%  
- Z-Height: |AI_value - Reference_value| / Reference_value * 100%
- XY Speed: |AI_value - Reference_value| / Reference_value * 100%

## EVALUATION FORMAT
**PARAMETER ACCURACY: [Score]/60**
Key deviations: [List top 3-4 parameter differences with % deviation]

**RECIPE COMPLETENESS: [Score]/25**
Status: [Complete/Mostly Complete/Incomplete]

**TECHNICAL REASONABLENESS: [Score]/15**
Assessment: [Brief technical evaluation]

**TOTAL SCORE: [Sum]/100**

**OVERALL GRADE: [EXCELLENT/GOOD/NEEDS_IMPROVEMENT]**
- EXCELLENT: 85-100 points (≤±15% deviation for most parameters)
- GOOD: 70-84 points (≤±25% deviation for most parameters)
- NEEDS_IMPROVEMENT: <70 points (>±25% deviation for many parameters)

**ACCURACY SUMMARY:**
- Parameters within ±15%: [count]/[total_key_parameters]
- Parameters within ±25%: [count]/[total_key_parameters]
- Largest deviations: [parameter_name: ±X%]

**PERFORMANCE PREDICTION:**
[One sentence: How would this AI recipe perform vs. the validated reference?]
```

### **Implementation Example**

```python
def evaluate_initial_recipe_generation(test_case, ai_agent_response):
    """
    Evaluate AI agent's initial recipe generation using LLM judge
    """
    
    # Extract test case components
    input_spec = test_case["input"]
    expected_output = test_case["expected_output"]
    
    # Format judge prompt
    judge_prompt = f"""
    You are an expert Field Application Engineer with 15+ years of experience in semiconductor dispensing optimization...
    
    ## INPUT SPECIFICATION
    Product: {input_spec['product_id']}
    Material: {input_spec['coating_material']}
    Package: {input_spec['layout']['type']} {input_spec['layout']['size_mm']}
    Target Specifications:
    {json.dumps(input_spec['target_specification'], indent=2)}
    
    ## AI AGENT OUTPUT
    {json.dumps(ai_agent_response, indent=2)}
    
    ## VALIDATED REFERENCE SOLUTION
    {json.dumps(expected_output['optimized_parameters'], indent=2)}
    
    [Rest of evaluation criteria...]
    """
    
    # Send to judge LLM
    judge_response = judge_llm.generate(judge_prompt)
    
    # Parse scores
    scores = parse_judge_scores(judge_response)
    
    return {
        "test_id": test_case["test_id"],
        "scores": scores,
        "judge_feedback": judge_response,
        "pass_threshold": scores["total"] >= 70,
        "accuracy_grade": "HIGH" if scores["parameter_accuracy"] >= 50 else "MEDIUM" if scores["parameter_accuracy"] >= 40 else "LOW"
    }
```

---

## 📊 Evaluation Implementation

### **Judge Implementation**

```python
class DispensingSMEJudge:
    """
    LLM Judge for Semiconductor Dispensing Optimization - Use Case 1 Only
    """
    
    def __init__(self, judge_llm_model="gpt-4o", testset_path="dispensing_optimization_testset.json"):
        self.judge = judge_llm_model
        self.testset = load_testset(testset_path)
        
    def evaluate_ai_agent(self, ai_agent):
        """
        Evaluate AI agent's initial recipe generation capability
        """
        results = {
            "use_case_1_results": [],
            "summary_metrics": {}
        }
        
        for test_case in self.testset["test_cases"]:
            # Use Case 1: Initial Recipe Generation
            ai_initial_recipe = ai_agent.generate_initial_recipe(test_case["input"])
            uc1_result = self.evaluate_initial_recipe_generation(
                test_case, ai_initial_recipe
            )
            results["use_case_1_results"].append(uc1_result)
        
        # Calculate summary metrics
        results["summary_metrics"] = self.calculate_summary_metrics(results)
        
        return results
    
    def calculate_summary_metrics(self, results):
        """
        Calculate overall performance metrics for Use Case 1
        """
        uc1_scores = [r["scores"]["total"] for r in results["use_case_1_results"]]
        uc1_pass_rate = sum(1 for r in results["use_case_1_results"] if r["pass_threshold"]) / len(uc1_scores)
        
        return {
            "use_case_1": {
                "average_score": np.mean(uc1_scores),
                "pass_rate": uc1_pass_rate,
                "excellence_rate": sum(1 for s in uc1_scores if s >= 85) / len(uc1_scores),
                "parameter_accuracy_avg": np.mean([r["scores"]["parameter_accuracy"] for r in results["use_case_1_results"]]),
                "completeness_avg": np.mean([r["scores"]["completeness"] for r in results["use_case_1_results"]]),
                "technical_reasonableness_avg": np.mean([r["scores"]["technical_reasonableness"] for r in results["use_case_1_results"]]),
                "high_accuracy_rate": sum(1 for r in results["use_case_1_results"] if r["accuracy_grade"] == "HIGH") / len(results["use_case_1_results"])
            },
            "overall_assessment": self.get_overall_assessment(uc1_scores)
        }
    
    def get_overall_assessment(self, scores):
        """
        Determine overall readiness assessment
        """
        avg_score = np.mean(scores)
        pass_rate = sum(1 for s in scores if s >= 70) / len(scores)
        excellence_rate = sum(1 for s in scores if s >= 85) / len(scores)
        
        if avg_score >= 85 and pass_rate >= 0.9:
            return "READY_FOR_PRODUCTION"
        elif avg_score >= 75 and pass_rate >= 0.8:
            return "READY_WITH_MONITORING"
        elif avg_score >= 65 and pass_rate >= 0.7:
            return "NEEDS_REFINEMENT"
        else:
            return "SIGNIFICANT_WORK_NEEDED"
```

---

## 🎯 Judge Quality Assurance

### **Judge Calibration Process**

#### **1. Judge Consistency Testing**
```python
def test_judge_consistency():
    """
    Test judge consistency by evaluating same response multiple times
    """
    sample_test_case = testset["test_cases"][0]
    sample_response = generate_sample_response(sample_test_case)
    
    consistency_scores = []
    for trial in range(5):
        evaluation = judge.evaluate_initial_recipe_generation(sample_test_case, sample_response)
        consistency_scores.append(evaluation["scores"]["total"])
    
    variance = np.var(consistency_scores)
    return {
        "mean_score": np.mean(consistency_scores),
        "variance": variance,
        "consistency_rating": "HIGH" if variance < 25 else "MEDIUM" if variance < 100 else "LOW"
    }
```

#### **2. Expert Validation**
- Compare LLM judge scores with human expert evaluations on subset
- Aim for >90% agreement on pass/fail decisions
- Validate physics compliance checking accuracy

#### **3. Judge Prompt Optimization**
```python
def optimize_judge_prompts():
    """
    A/B test different judge prompt variations
    """
    prompt_variants = [
        "standard_prompt.md",
        "detailed_physics_prompt.md", 
        "industry_expert_prompt.md"
    ]
    
    for prompt_file in prompt_variants:
        scores = evaluate_with_prompt(prompt_file)
        analyze_score_distribution(scores)
        measure_expert_agreement(scores)
    
    return best_performing_prompt
```

---

## 📈 Evaluation Metrics & Reporting

### **Performance Dashboard**

```python
def generate_evaluation_report(results):
    """
    Generate comprehensive evaluation report for Use Case 1
    """
    report = {
        "executive_summary": {
            "overall_grade": calculate_overall_grade(results),
            "key_strengths": extract_key_strengths(results),
            "improvement_areas": extract_improvement_areas(results),
            "readiness_assessment": results["summary_metrics"]["overall_assessment"]
        },
        
        "detailed_metrics": {
            "recipe_generation_performance": {
                "parameter_accuracy_avg": results["summary_metrics"]["use_case_1"]["parameter_accuracy_avg"],
                "recipe_completeness_avg": results["summary_metrics"]["use_case_1"]["completeness_avg"],
                "technical_reasonableness_avg": results["summary_metrics"]["use_case_1"]["technical_reasonableness_avg"],
                "overall_score_avg": results["summary_metrics"]["use_case_1"]["average_score"],
                "pass_rate": results["summary_metrics"]["use_case_1"]["pass_rate"],
                "excellence_rate": results["summary_metrics"]["use_case_1"]["excellence_rate"],
                "high_accuracy_rate": results["summary_metrics"]["use_case_1"]["high_accuracy_rate"]
            }
        },
        
        "test_case_breakdown": generate_per_test_analysis(results),
        
        "recommendations": generate_improvement_recommendations(results)
    }
    
    return report
```

### **Success Criteria**

| **Metric** | **Excellent** | **Good** | **Needs Improvement** |
|---|---|---|---|
| **Average Score** | ≥85 | 70-84 | <70 |
| **Pass Rate** | ≥90% | 75-89% | <75% |
| **Parameter Accuracy** | ≥50/60 | 40-49/60 | <40/60 |
| **Recipe Completeness** | ≥20/25 | 15-19/25 | <15/25 |
| **Technical Reasonableness** | ≥12/15 | 8-11/15 | <8/15 |
| **High Accuracy Rate** | ≥80% | 60-79% | <60% |
| **Production Readiness** | Ready | Needs refinement | Significant work needed |

---

## 🚀 Best Practices

### **Judge Prompt Engineering**
1. **Be Specific**: Include exact scoring criteria and examples
2. **Domain Expertise**: Frame judge as experienced SME with credentials
3. **Structured Output**: Require consistent evaluation format
4. **Physics Grounding**: Include cause-effect relationship validation
5. **Comparative Analysis**: Provide reference solutions for calibration

### **Evaluation Process**
1. **Baseline Establishment**: Test judge consistency before agent evaluation
2. **Batch Processing**: Evaluate multiple test cases in single session
3. **Score Calibration**: Regularly validate against expert assessments
4. **Iterative Improvement**: Refine prompts based on evaluation quality
5. **Documentation**: Maintain detailed evaluation logs and reasoning

### **Quality Control**
1. **Cross-Validation**: Use multiple judge prompts for critical evaluations
2. **Expert Review**: Randomly sample judge evaluations for human validation
3. **Statistical Analysis**: Monitor score distributions for anomalies
4. **Version Control**: Track judge prompt versions and performance changes

---

## 📚 Implementation Checklist

### **Setup Phase**
- [ ] Configure judge LLM with appropriate model (GPT-4, Claude-3, etc.)
- [ ] Load and validate testset data structure
- [ ] Implement score parsing and aggregation functions
- [ ] Set up evaluation pipeline with error handling

### **Calibration Phase**  
- [ ] Run judge consistency tests
- [ ] Validate against expert evaluations (sample size ≥20)
- [ ] Optimize prompt templates based on performance
- [ ] Establish baseline metrics and thresholds

### **Evaluation Phase**
- [ ] Execute initial recipe generation evaluations across full testset
- [ ] Analyze parameter accuracy and deviations from reference solutions
- [ ] Generate detailed performance reports
- [ ] Document findings and recommendations

### **Quality Assurance**
- [ ] Review evaluation results for consistency
- [ ] Validate physics compliance checking accuracy
- [ ] Confirm score distributions align with expectations
- [ ] Archive evaluation data and judge responses

---

**🎯 Ready to implement LLM-as-Judge evaluation for initial recipe generation in semiconductor dispensing AI agents!** 