# ULTIMATE Deterministic Autonomy Architecture

## The Most Powerful Pattern

**Deterministic Autonomy** reaches its ultimate form when WorkflowStepAgent is not just making simple LLM calls, but is a **full autonomous agent** equipped with Resources and Workflows to accomplish complex objectives.

## Architecture

```
Calling Agent (LLM - decides WHICH workflows to run)
    ↓
  Workflow (Deterministic structure - can't skip steps)
      ├─ Step 1: Data collection (deterministic code)
      ├─ Step 2: Calculation (deterministic code)
      ├─ Step 3: WorkflowStepAgent.query(objective="Classify patterns")
      │           ↓
      │       WorkflowStepAgent (AUTONOMOUS, goal-oriented)
      │           ├─ .with_resources(DataResource, AnalysisResource, ExternalAPIResource)
      │           ├─ .with_workflows(ImageAnalysisWorkflow, StatisticalTestWorkflow)
      │           ├─ Agent autonomously decides: "I need spatial data"
      │           │   → Calls DataResource.get_wafer_map()
      │           ├─ Agent decides: "I should run statistical tests"
      │           │   → Invokes StatisticalTestWorkflow
      │           ├─ Agent decides: "I need to analyze defect images"
      │           │   → Invokes ImageAnalysisWorkflow
      │           ├─ Agent synthesizes all results
      │           └─ Returns structured JSON: {"classifications": {...}, "confidence": 0.95}
      │           ↑
      ├─ Step 4: Workflow receives structured data (deterministic)
      ├─ Step 5: Makes deterministic decision based on structured data
      └─ Returns complete results to Calling Agent
    ↓
Calling Agent reviews complete data, decides next workflow
```

## Key Insight

**At each workflow step that needs intelligence:**

1. **Workflow gives WorkflowStepAgent an OBJECTIVE** (not just a prompt)
   - ❌ OLD: "Classify these patterns: BIN_1, BIN_2..."
   - ✅ NEW: **Objective: "Determine if failure patterns are systematic or random, with high confidence"**

2. **WorkflowStepAgent is equipped with TOOLS** to accomplish the objective
   ```python
   step_agent.with_resources(
       WaferMapResource,      # Get spatial defect maps
       DefectImageResource,   # Get SEM/TEM images
       StatisticalResource,   # Run statistical tests
       HistoricalDataResource # Compare with historical patterns
   )

   step_agent.with_workflows(
       ImageAnalysisWorkflow,     # Analyze defect images with CV
       ClusteringWorkflow,        # Run spatial clustering analysis
       StatisticalTestWorkflow    # Run chi-square, spatial autocorrelation tests
   )
   ```

3. **WorkflowStepAgent autonomously decides HOW to achieve objective**
   - Agent reasons: "To determine if patterns are systematic, I need:"
   - → "1. Spatial defect map" → Calls WaferMapResource
   - → "2. Clustering analysis" → Invokes ClusteringWorkflow
   - → "3. Statistical significance test" → Invokes StatisticalTestWorkflow
   - → "4. Compare with historical systematic patterns" → Calls HistoricalDataResource
   - → Synthesizes all results into structured answer with confidence level

4. **Workflow gets STRUCTURED, DETERMINISTIC result**
   ```json
   {
     "pattern_type": "SYSTEMATIC",
     "confidence": 0.95,
     "evidence": {
       "spatial_clustering": {"p_value": 0.001, "result": "significant"},
       "morans_i": {"value": 0.87, "result": "strong_positive_autocorrelation"},
       "defect_density": {"center": 0.82, "edge": 0.15, "ratio": 5.47},
       "historical_match": {"similarity": 0.91, "case_id": "CASE_2024_045"}
     },
     "reasoning": "High spatial clustering (p<0.001), strong autocorrelation (I=0.87), center-weighted density (5.5x), matches historical systematic case with 91% similarity"
   }
   ```

5. **Workflow makes DETERMINISTIC decision** based on structured data
   ```python
   if classifications["confidence"] >= 0.9 and classifications["pattern_type"] == "SYSTEMATIC":
       # High confidence systematic pattern → proceed to root cause analysis
       next_step = "root_cause_workflow"
   elif classifications["confidence"] < 0.7:
       # Low confidence → need more data
       next_step = "collect_additional_data"
   else:
       # Medium confidence random pattern → proceed with different approach
       next_step = "random_defect_analysis"
   ```

## Example: YieldParetoWorkflow with Autonomous WorkflowStepAgent

### Current Implementation (Simple)

```python
def _classify_failure_patterns(self, pareto_bins: list) -> dict:
    prompt = f"Classify these patterns: {bins_summary}..."

    # Simple LLM call
    result = self.workflow_step_agent.query(caller_message=prompt)
    response_text = result.get("response", "{}")

    return json.loads(response_text)
```

### ULTIMATE Implementation (Autonomous Agent with Tools)

```python
def _classify_failure_patterns(self, pareto_bins: list, wafer_id: str) -> dict:
    """
    Use autonomous WorkflowStepAgent with full resources and workflows
    to accomplish complex pattern classification objective.
    """

    # Configure step agent with powerful resources
    self._ensure_step_agent_configured()

    # Give agent access to data resources
    from resources.wafer_map_resource import WaferMapResource
    from resources.defect_image_resource import DefectImageResource
    from resources.statistical_analysis_resource import StatisticalAnalysisResource
    from resources.historical_pattern_resource import HistoricalPatternResource

    self.workflow_step_agent.with_resources(
        WaferMapResource(resource_id="wafer-map"),
        DefectImageResource(resource_id="defect-images"),
        StatisticalAnalysisResource(resource_id="stats"),
        HistoricalPatternResource(resource_id="historical-patterns")
    )

    # Give agent access to analysis workflows
    from workflows.spatial_clustering_workflow import SpatialClusteringWorkflow
    from workflows.defect_image_analysis_workflow import DefectImageAnalysisWorkflow
    from workflows.statistical_test_workflow import StatisticalTestWorkflow

    self.workflow_step_agent.with_workflows(
        SpatialClusteringWorkflow(),
        DefectImageAnalysisWorkflow(),
        StatisticalTestWorkflow()
    )

    # Give agent objective-driven task (not just a prompt!)
    objective = f"""
    OBJECTIVE: Determine if failure patterns for bins {[b['bin_id'] for b in pareto_bins]}
    are SYSTEMATIC or RANDOM, with HIGH CONFIDENCE (>0.9).

    CONTEXT:
    - Wafer ID: {wafer_id}
    - Top failing bins: {bins_summary}
    - Must provide: pattern_type, confidence, evidence, reasoning

    AVAILABLE TOOLS:
    - WaferMapResource: Get spatial defect distribution maps
    - DefectImageResource: Get SEM/TEM defect images
    - StatisticalAnalysisResource: Run spatial autocorrelation, clustering tests
    - HistoricalPatternResource: Compare with known systematic/random patterns
    - SpatialClusteringWorkflow: Run DBSCAN/K-means clustering analysis
    - DefectImageAnalysisWorkflow: Analyze defect morphology from images
    - StatisticalTestWorkflow: Run Moran's I, Getis-Ord Gi*, chi-square tests

    REQUIREMENTS:
    - Use multiple sources of evidence
    - Provide statistical significance (p-values)
    - Return structured JSON with all evidence
    - Include confidence score (0.0-1.0)

    You are AUTONOMOUS - decide which tools to use and in what order.
    """

    # Agent autonomously accomplishes objective
    result = self.workflow_step_agent.query(caller_message=objective)

    # Agent might have:
    # 1. Called WaferMapResource to get spatial data
    # 2. Invoked SpatialClusteringWorkflow to run DBSCAN
    # 3. Invoked StatisticalTestWorkflow to run Moran's I test
    # 4. Called HistoricalPatternResource to find similar cases
    # 5. Synthesized all evidence into structured response

    response_text = result.get("response", "{}")
    classifications = json.loads(response_text)

    # Workflow gets structured, evidence-based result:
    # {
    #   "classifications": {
    #     "BIN_1": {
    #       "pattern_type": "SYSTEMATIC",
    #       "confidence": 0.95,
    #       "evidence": {
    #         "spatial_clustering": {"method": "DBSCAN", "clusters": 3, "p_value": 0.001},
    #         "morans_i": {"value": 0.87, "p_value": 0.0001},
    #         "defect_morphology": {"type": "gate_oxide_pinhole", "confidence": 0.92},
    #         "historical_match": {"case_id": "CASE_2024_045", "similarity": 0.91}
    #       }
    #     }
    #   },
    #   "overall_assessment": "Strong evidence of systematic process defect",
    #   "has_systematic_patterns": true
    # }

    return classifications
```

## Why This is ULTIMATE Deterministic Autonomy

### Level 1: Calling Agent Autonomy
- **Calling agent decides which workflows to run** (goal-directed)
- Flexible, adapts to data

### Level 2: Workflow Determinism
- **Workflows execute ALL steps** (can't skip)
- Systematic, reliable

### Level 3: WorkflowStepAgent Autonomy (ULTIMATE)
- **At each intelligence step, agent is fully autonomous**
- Equipped with Resources and Workflows (powerful tools)
- Given high-level objective, not step-by-step instructions
- Agent decides: which resources to call, which workflows to invoke, in what order
- Agent synthesizes multi-source evidence into structured result
- **Workflow gets back HIGH-CONFIDENCE, EVIDENCE-BASED structured data**

### Level 4: Deterministic Continuation
- **Workflow makes deterministic decision** based on structured data
- `if confidence >= 0.9: next_action = X`
- `elif confidence < 0.7: next_action = Y`

## Comparison

| Approach | Intelligence Level | Workflow Steps Use |
|----------|-------------------|-------------------|
| **Simple Deterministic Autonomy** | Agent decides workflows | Simple LLM prompt at steps |
| **ULTIMATE Deterministic Autonomy** ⭐ | Agent decides workflows | **Autonomous agent with tools** at steps |

## Real-World Example: Pattern Classification

### Simple Approach (what we have now)
```
WorkflowStepAgent receives:
"Classify these bins: BIN_1 (clustered), BIN_2 (random)..."

Agent responds with text/JSON based on prompt.
Confidence: Unknown
Evidence: Agent's reasoning only
```

### ULTIMATE Approach (what you want)
```
WorkflowStepAgent receives:
OBJECTIVE: "Determine if patterns are systematic with >0.9 confidence"

Agent autonomously:
1. Calls WaferMapResource.get_spatial_data(wafer_id, bin_id)
2. Invokes SpatialClusteringWorkflow(spatial_data)
   → Returns: {clusters: 3, dbscan_eps: 2.5, silhouette: 0.82}
3. Invokes StatisticalTestWorkflow(test="morans_i", data=spatial_data)
   → Returns: {morans_i: 0.87, p_value: 0.0001, interpretation: "strong_positive_autocorrelation"}
4. Calls DefectImageResource.get_images(bin_id)
5. Invokes DefectImageAnalysisWorkflow(images)
   → Returns: {defect_type: "gate_oxide_pinhole", confidence: 0.92}
6. Calls HistoricalPatternResource.find_similar(pattern_signature)
   → Returns: {match: "CASE_2024_045", similarity: 0.91, was_systematic: true}

Agent synthesizes:
{
  "pattern_type": "SYSTEMATIC",
  "confidence": 0.95,
  "evidence": {all tool results},
  "reasoning": "Four independent sources agree: spatial clustering (p<0.001),
                autocorrelation (I=0.87, p<0.0001), defect morphology matches
                gate oxide systematic defect (92%), historical case match (91%)"
}
```

## Benefits

1. **Higher Confidence**: Multi-source evidence, statistical rigor
2. **Explainable**: Full evidence trail, not just LLM opinion
3. **Flexible**: Agent can adapt approach based on data availability
4. **Powerful**: Agent can invoke complex analysis workflows
5. **Deterministic**: Workflow still gets structured data for deterministic decisions

## This is the ULTIMATE Pattern

**Three levels of intelligence:**
1. **Calling Agent** (autonomous) - decides workflows
2. **WorkflowStepAgent** (autonomous) - accomplishes complex objectives with tools
3. **Workflows** (deterministic) - guarantee all steps, make deterministic decisions

**Result**: Maximum intelligence + Maximum reliability ⭐
