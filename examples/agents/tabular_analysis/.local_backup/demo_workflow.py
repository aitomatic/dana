#!/usr/bin/env python3
"""
Quick demo to verify TabularAnalysisWorkflow is runnable.
"""

import sys
from pathlib import Path

# Add tabular_analysis to path
sys.path.insert(0, str(Path(__file__).parent))

from tabular_workflows.tabular_analysis_workflow import TabularAnalysisWorkflow
from resources.dataframe_indexer_resource import DataFrameIndexerResource
from resources.metadata_extractor_resource import MetadataExtractorResource

def main():
    print("=" * 80)
    print("TabularAnalysisWorkflow Demo")
    print("=" * 80)
    print()
    
    # Setup paths
    dataset_dir = Path(__file__).parent / "dataset"
    cache_dir = "/tmp/tabular_workflow_demo"
    
    print(f"Dataset directory: {dataset_dir}")
    print(f"Cache directory: {cache_dir}")
    print()
    
    # Initialize resources
    print("Initializing resources...")
    indexer = DataFrameIndexerResource(
        workspace_root=str(dataset_dir),
        cache_dir=cache_dir,
        debug=True
    )
    
    metadata_extractor = MetadataExtractorResource(
        workspace_root=str(dataset_dir)
    )
    
    # Create workflow
    workflow = TabularAnalysisWorkflow(
        dataframe_indexer=indexer,
        metadata_extractor=metadata_extractor,
        llm_provider="openai",
        llm_model="gpt-4o-mini"
    )
    
    print("✅ Workflow created successfully\n")
    
    # Index a file
    print("-" * 80)
    print("Step 1: Indexing dataset file...")
    print("-" * 80)
    
    index_result = indexer.index_file('NL2SQL_Query_Dataset.csv')
    
    if index_result['success']:
        print(f"✅ File indexed successfully")
        print(f"   Total documents: {index_result['total_documents']}")
        print(f"   Data documents: {index_result['num_data_documents']}")
        print(f"   Column documents: {index_result['num_column_documents']}")
    else:
        print(f"❌ Indexing failed: {index_result.get('error')}")
        return
    
    print()
    
    # Execute workflow
    print("-" * 80)
    print("Step 2: Executing workflow...")
    print("-" * 80)
    
    user_query = "SQL query examples with customer data"
    print(f"Query: {user_query}\n")
    
    response = workflow.execute(user_query=user_query, top_k=2)
    result = response.get('result', response)
    
    if result['success']:
        print("✅ Workflow executed successfully\n")
        
        print(f"Relevant Files ({len(result['relevant_files'])}):")
        for file in result['relevant_files']:
            print(f"  - {file}")
        
        print(f"\nRelevant Columns:")
        if result['relevant_columns']:
            for file_name, columns in result['relevant_columns'].items():
                print(f"  {file_name}: {', '.join(columns)}")
        else:
            print("  (None identified)")
        
        print(f"\n{'-' * 80}")
        print("LLM Analysis:")
        print(f"{'-' * 80}")
        print(result['llm_analysis'])
        
    else:
        print(f"❌ Workflow failed: {result.get('error')}")
    
    print()
    print("=" * 80)
    print("Demo completed")
    print("=" * 80)

if __name__ == "__main__":
    main()

