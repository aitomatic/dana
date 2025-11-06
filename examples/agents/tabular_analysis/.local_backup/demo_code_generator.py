#!/usr/bin/env python3
"""
Demo: Complete Tabular Analysis Pipeline with Code Generation

This demonstrates the full workflow:
1. Index tabular data
2. Run analysis workflow to identify relevant files
3. Generate Python code from analysis
4. Execute code and display results
"""

import sys
from pathlib import Path

# Add tabular_analysis to path
sys.path.insert(0, str(Path(__file__).parent))

from tabular_workflows.tabular_analysis_workflow import TabularAnalysisWorkflow
from resources.dataframe_indexer_resource import DataFrameIndexerResource
from resources.metadata_extractor_resource import MetadataExtractorResource
from resources.query_code_generator_resource import QueryCodeGeneratorResource


def main():
    print("=" * 80)
    print("Complete Tabular Analysis Pipeline with Code Generation")
    print("=" * 80)
    print()
    
    # Setup paths
    dataset_dir = Path(__file__).parent / "dataset"
    cache_dir = "/tmp/tabular_pipeline_demo"
    
    print(f"Dataset directory: {dataset_dir}")
    print(f"Cache directory: {cache_dir}")
    print()
    
    # ========================================
    # STEP 1: Initialize Resources
    # ========================================
    print("=" * 80)
    print("STEP 1: Initializing Resources")
    print("=" * 80)
    
    indexer = DataFrameIndexerResource(
        workspace_root=str(dataset_dir),
        cache_dir=cache_dir,
        debug=False
    )
    
    metadata_extractor = MetadataExtractorResource(
        workspace_root=str(dataset_dir)
    )
    
    code_generator = QueryCodeGeneratorResource(
        workspace_root=str(dataset_dir),
        llm_model="gpt-4o-mini",
        debug=False
    )
    
    print("✅ Resources initialized")
    print()
    
    # ========================================
    # STEP 2: Index Data
    # ========================================
    print("=" * 80)
    print("STEP 2: Indexing Dataset")
    print("=" * 80)
    
    index_result = indexer.index_file('NL2SQL_Query_Dataset.csv')
    
    if index_result['success']:
        if index_result.get('skipped'):
            print("✅ File already indexed (using cache)")
        else:
            print("✅ File indexed successfully")
            print(f"   Data documents: {index_result['num_data_documents']}")
            print(f"   Column documents: {index_result['num_column_documents']}")
            print(f"   Total: {index_result['total_documents']}")
    else:
        print(f"❌ Indexing failed: {index_result.get('error')}")
        return
    
    print()
    
    # ========================================
    # STEP 3: Run Analysis Workflow
    # ========================================
    print("=" * 80)
    print("STEP 3: Running Analysis Workflow")
    print("=" * 80)
    
    workflow = TabularAnalysisWorkflow(
        dataframe_indexer=indexer,
        metadata_extractor=metadata_extractor,
        llm_agent=None  # Use fallback analysis
    )
    
    user_query = "Find all SQL query examples and count how many there are"
    print(f"User Query: {user_query}\n")
    
    response = workflow.execute(user_query=user_query, top_k=3)
    result = response.get('result', response)
    
    if result['success']:
        print("✅ Workflow completed\n")
        print(f"Relevant Files: {', '.join(result['relevant_files'])}")
        
        if result['relevant_columns']:
            print("\nKey Columns:")
            for file_name, columns in result['relevant_columns'].items():
                print(f"  {file_name}: {', '.join(columns)}")
        
        print("\nLLM Analysis:")
        print("-" * 80)
        print(result['llm_analysis'])
        print("-" * 80)
    else:
        print(f"❌ Workflow failed: {result.get('error')}")
        return
    
    print()
    
    # ========================================
    # STEP 4: Generate and Execute Code
    # ========================================
    print("=" * 80)
    print("STEP 4: Generating and Executing Python Code")
    print("=" * 80)
    
    # Use the workflow's analysis to generate code
    code_result = code_generator.generate_and_execute(
        analysis_text=result['llm_analysis'],
        execute=True
    )
    
    if code_result['success']:
        print("✅ Code generated and executed successfully\n")
        
        print("Generated Python Code:")
        print("-" * 80)
        print(code_result['generated_code'])
        print("-" * 80)
        print()
        
        print("Execution Results:")
        print(f"Summary: {code_result['result_summary']}")
        print(f"Execution time: {code_result['execution_time']:.3f}s")
        print()
        
        if code_result['execution_result']:
            print("Data Preview:")
            print("-" * 80)
            
            # Display results based on type
            exec_result = code_result['execution_result']
            
            if isinstance(exec_result, list):
                # List of records (DataFrame converted to dict)
                import json
                preview = exec_result[:5] if len(exec_result) > 5 else exec_result
                print(json.dumps(preview, indent=2, default=str))
                if len(exec_result) > 5:
                    print(f"\n... ({len(exec_result) - 5} more records)")
            
            elif isinstance(exec_result, dict):
                # Dictionary result
                import json
                print(json.dumps(exec_result, indent=2, default=str))
            
            else:
                # Scalar or other type
                print(exec_result)
            
            print("-" * 80)
    
    else:
        print(f"❌ Code generation/execution failed: {code_result.get('error')}")
    
    print()
    print("=" * 80)
    print("Pipeline Demo Complete")
    print("=" * 80)
    print()
    print("Summary:")
    print("✅ Data indexed for semantic search")
    print("✅ Workflow identified relevant files and columns")
    print("✅ Python code generated from analysis")
    print("✅ Code executed and results returned")
    print()
    print("This demonstrates the complete pipeline from data discovery")
    print("to automated query execution!")


if __name__ == "__main__":
    main()

