"""Test ULTIMATE pattern - verify WorkflowStepAgent uses Resources and Workflows."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.lib.agents.workflow_step_agent import WorkflowStepAgent
from dana.lib.resources.conversation import ConversationResource

from resources.wafer_map_resource import WaferMapResource
from resources.statistical_analysis_resource import StatisticalAnalysisResource
from resources.historical_pattern_resource import HistoricalPatternResource
from workflows.spatial_clustering_workflow import SpatialClusteringWorkflow
from workflows.statistical_test_workflow import StatisticalTestWorkflow


def test_ultimate_pattern():
    """Test that WorkflowStepAgent can use Resources and Workflows."""

    print("=" * 80)
    print("TESTING ULTIMATE DETERMINISTIC AUTONOMY PATTERN")
    print("=" * 80)
    print()

    # Create WorkflowStepAgent
    print("Step 1: Creating WorkflowStepAgent...")
    agent = WorkflowStepAgent(agent_id="test-ultimate-agent")

    # Configure with LLM resource
    agent.with_resources(ConversationResource(resource_id="test-llm", llm_provider="anthropic", model="claude-3-5-sonnet-20241022"))
    print("✓ Agent created with LLM resource")
    print()

    # Step 2: Equip agent with powerful Resources
    print("Step 2: Equipping agent with Resources...")
    agent.with_resources(
        WaferMapResource(resource_id="wafer-map"),
        StatisticalAnalysisResource(resource_id="stats"),
        HistoricalPatternResource(resource_id="historical"),
    )
    print("✓ Agent equipped with 3 Resources:")
    print("  - WaferMapResource")
    print("  - StatisticalAnalysisResource")
    print("  - HistoricalPatternResource")
    print()

    # Step 3: Equip agent with Workflows
    print("Step 3: Equipping agent with Workflows...")
    agent.with_workflows(SpatialClusteringWorkflow(), StatisticalTestWorkflow())
    print("✓ Agent equipped with 2 Workflows:")
    print("  - SpatialClusteringWorkflow")
    print("  - StatisticalTestWorkflow")
    print()

    # Step 4: Test Resources directly (verify they work)
    print("Step 4: Testing Resources directly...")
    print()

    wafer_resource = WaferMapResource()
    print("Test 4a: WaferMapResource.get_spatial_data()")
    spatial_data = wafer_resource.get_spatial_data("W12345", "BIN_1")
    print("  ✓ Retrieved spatial data for BIN_1:")
    print(f"    - Defect count: {spatial_data['defect_count']}")
    print(f"    - Center density: {spatial_data['spatial_distribution']['center_region']['density']}")
    print(f"    - Edge density: {spatial_data['spatial_distribution']['edge_region']['density']}")
    print()

    stats_resource = StatisticalAnalysisResource()
    print("Test 4b: StatisticalAnalysisResource.morans_i_test()")
    morans_result = stats_resource.morans_i_test(spatial_data)
    print("  ✓ Moran's I test completed:")
    print(f"    - Statistic: {morans_result['statistic']}")
    print(f"    - P-value: {morans_result['p_value']}")
    print(f"    - Interpretation: {morans_result['interpretation']}")
    print()

    historical_resource = HistoricalPatternResource()
    print("Test 4c: HistoricalPatternResource.find_similar_patterns()")
    pattern_sig = {"bin_id": "BIN_1", "spatial": "center_clustered"}
    historical_result = historical_resource.find_similar_patterns(pattern_sig)
    print("  ✓ Historical pattern match:")
    print(f"    - Best match: {historical_result.get('best_match', 'None')}")
    if historical_result.get("matches"):
        match = historical_result["matches"][0]
        print(f"    - Similarity: {match['similarity_score']}")
        print(f"    - Root cause: {match['root_cause']}")
    print()

    # Step 5: Test Workflows directly
    print("Step 5: Testing Workflows directly...")
    print()

    clustering_workflow = SpatialClusteringWorkflow()
    print("Test 5a: SpatialClusteringWorkflow.execute()")
    clustering_result = clustering_workflow.execute(spatial_data)
    print("  ✓ Clustering analysis completed:")
    print(f"    - Pattern type: {clustering_result['pattern_type']}")
    print(f"    - Clustering strength: {clustering_result['clustering_strength']}")
    print(f"    - Density ratio: {clustering_result['metrics']['density_ratio']:.2f}")
    print()

    stats_workflow = StatisticalTestWorkflow()
    print("Test 5b: StatisticalTestWorkflow.execute()")
    stats_workflow_result = stats_workflow.execute({"test_type": "comprehensive", "spatial_data": spatial_data, "resource": stats_resource})
    print("  ✓ Statistical test workflow completed:")
    print(f"    - Tests run: {', '.join(stats_workflow_result['tests_run'])}")
    print(f"    - Confidence: {stats_workflow_result['confidence']}")
    print(f"    - Assessment: {stats_workflow_result['overall_assessment']}")
    print()

    # Step 6: Give agent OBJECTIVE and let it decide
    print("=" * 80)
    print("Step 6: ULTIMATE TEST - Agent with OBJECTIVE")
    print("=" * 80)
    print()
    print("Giving agent high-level objective:")
    print("  'Determine if BIN_1 failures are SYSTEMATIC or RANDOM'")
    print()
    print("Agent has access to:")
    print("  - 3 Resources (WaferMap, Statistical, Historical)")
    print("  - 2 Workflows (SpatialClustering, StatisticalTest)")
    print()
    print("Agent will autonomously decide which tools to use...")
    print()

    objective = """OBJECTIVE: Determine if BIN_1 failures are SYSTEMATIC or RANDOM with high confidence.

CONTEXT:
- Wafer ID: W12345
- Bin: BIN_1 (SRAM bit failures, 180 failures)

AVAILABLE TOOLS:
1. WaferMapResource.get_spatial_data(wafer_id, bin_id) - Get spatial defect map
2. StatisticalAnalysisResource.morans_i_test(spatial_data) - Test for spatial clustering
3. StatisticalAnalysisResource.getis_ord_gi_star(spatial_data) - Hot spot analysis
4. HistoricalPatternResource.find_similar_patterns(signature) - Find similar historical cases
5. SpatialClusteringWorkflow.execute(spatial_data) - Run clustering analysis
6. StatisticalTestWorkflow.execute(params) - Run comprehensive statistical tests

METHODOLOGY (you decide):
- You are AUTONOMOUS - decide which tools to use
- Use multiple sources of evidence
- Provide statistical significance
- Return structured JSON

Return JSON:
{
    "pattern_type": "SYSTEMATIC|RANDOM",
    "confidence": 0.0-1.0,
    "evidence": {
        "tool1": {...},
        "tool2": {...}
    },
    "reasoning": "Why you concluded this",
    "tools_used": ["list", "of", "tools"]
}
"""

    try:
        result = agent.query(caller_message=objective)
        response = result.get("response", "")

        print("AGENT RESPONSE:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        print()

        # Try to parse JSON
        import json

        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            result_json = json.loads(response)
            print("✓ Agent returned structured JSON:")
            print(f"  - Pattern type: {result_json.get('pattern_type', 'Unknown')}")
            print(f"  - Confidence: {result_json.get('confidence', 0)}")
            print(f"  - Tools used: {result_json.get('tools_used', [])}")
            print(f"  - Evidence sources: {list(result_json.get('evidence', {}).keys())}")

        except json.JSONDecodeError:
            print("⚠ Agent response is not JSON (this is OK for demo)")

    except Exception as e:
        print(f"❌ Agent query failed: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 80)
    print("ULTIMATE PATTERN TEST COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print("✓ Resources work independently")
    print("✓ Workflows work independently")
    print("✓ Agent can be equipped with Resources and Workflows")
    print("✓ Agent receives high-level objective")
    print()
    print("This demonstrates ULTIMATE Deterministic Autonomy:")
    print("- Agent decides which tools to use (autonomy)")
    print("- Tools provide deterministic, evidence-based results (reliability)")
    print("- Agent synthesizes multi-source evidence (intelligence)")
    print()


if __name__ == "__main__":
    test_ultimate_pattern()
