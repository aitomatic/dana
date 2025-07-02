#!/usr/bin/env python3
"""
Phase 2 Human Testing Script: Meta Knowledge Extraction

This script allows you to manually test and verify the meta knowledge extraction functionality
of OpenDXA KNOWS Phase 2 components:
- MetaKnowledgeExtractor: Extracting structured knowledge from documents
- KnowledgeCategorizer: Categorizing knowledge into different types
- Integration with Phase 1: End-to-end document processing to knowledge extraction

Usage: python test_phase2_meta_extraction.py
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from opendxa.knows.document.loader import DocumentLoader
from opendxa.knows.document.parser import DocumentParser
from opendxa.knows.document.extractor import TextExtractor
from opendxa.knows.extraction.meta.extractor import MetaKnowledgeExtractor
from opendxa.knows.extraction.meta.categorizer import KnowledgeCategorizer
from opendxa.common.utils.logging import DXA_LOGGER


class Phase2Tester:
    """Human testing interface for Phase 2 meta knowledge extraction."""
    
    def __init__(self, docs_dir: str):
        """Initialize the tester with document directory."""
        self.docs_dir = Path(docs_dir)
        
        # Phase 1 components
        self.loader = DocumentLoader()
        self.parser = DocumentParser()
        self.extractor = TextExtractor()
        
        # Phase 2 components
        self.meta_extractor = MetaKnowledgeExtractor()
        self.categorizer = KnowledgeCategorizer()
        
        print("🔧 Phase 2 Tester Initialized")
        print(f"📁 Documents directory: {self.docs_dir}")
        print("=" * 80)
    
    def list_available_documents(self):
        """List all available documents for testing."""
        print("\n📋 Available Documents for Testing:")
        print("-" * 50)
        
        if not self.docs_dir.exists():
            print("❌ Documents directory not found!")
            return []
        
        docs = []
        for file_path in self.docs_dir.iterdir():
            if file_path.is_file():
                size = file_path.stat().st_size
                docs.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': size,
                    'format': file_path.suffix[1:] if file_path.suffix else 'unknown'
                })
                print(f"  📄 {file_path.name:<30} ({size:,} bytes, {file_path.suffix[1:] or 'no ext'})")
        
        print(f"\n✅ Found {len(docs)} documents")
        return docs
    
    def run_phase1_pipeline(self, file_path: str):
        """Run Phase 1 pipeline to get extracted text."""
        print(f"\n🔄 Running Phase 1 Pipeline: {Path(file_path).name}")
        print("-" * 60)
        
        try:
            # Step 1: Load document
            print("📥 Loading document...")
            document = self.loader.load_document(file_path)
            print(f"✅ Document loaded ({len(document.content):,} chars)")
            
            # Step 2: Parse document
            print("🔍 Parsing document...")
            parsed_doc = self.parser.process(document)
            print(f"✅ Document parsed ({len(parsed_doc.text_content):,} chars)")
            
            # Step 3: Extract text
            print("✂️  Extracting text...")
            extracted_text = self.extractor.process(parsed_doc)
            print(f"✅ Text extracted ({len(extracted_text):,} chars, {len(extracted_text.split()):,} words)")
            
            return extracted_text
            
        except Exception as e:
            print(f"❌ Phase 1 pipeline failed: {str(e)}")
            return None
    
    def test_meta_knowledge_extraction(self, document, document_name: str):
        """Test meta knowledge extraction functionality."""
        print(f"\n🔄 Testing Meta Knowledge Extraction")
        print("-" * 60)
        
        try:
            print("🧠 Extracting meta knowledge...")
            knowledge_points = self.meta_extractor.process(document)
            
            print("✅ Meta knowledge extracted successfully!")
            print(f"   📊 Total knowledge points: {len(knowledge_points)}")
            
            # Group by knowledge type for better display
            by_type = {}
            for kp in knowledge_points:
                kp_type = kp.type
                if kp_type not in by_type:
                    by_type[kp_type] = []
                by_type[kp_type].append(kp)
            
            print(f"   🏷️  Knowledge types found: {list(by_type.keys())}")
            
            # Show detailed breakdown
            print(f"\n📊 Knowledge Breakdown:")
            for kp_type, points in by_type.items():
                print(f"   {kp_type}: {len(points)} points")
            
            # Show sample knowledge points
            print(f"\n🔍 Sample Knowledge Points:")
            for i, kp in enumerate(knowledge_points[:5]):  # Show first 5
                print(f"   {i+1}. [{kp.type}] {kp.content[:100]}{'...' if len(kp.content) > 100 else ''}")
                print(f"      Confidence: {kp.confidence:.2f}")
                if kp.metadata:
                    print(f"      Metadata: {list(kp.metadata.keys())}")
                print()
            
            if len(knowledge_points) > 5:
                print(f"   ... and {len(knowledge_points) - 5} more knowledge points")
            
            return knowledge_points
            
        except Exception as e:
            print(f"❌ Meta knowledge extraction failed: {str(e)}")
            return None
    
    def test_knowledge_categorization(self, knowledge_points: list):
        """Test knowledge categorization functionality."""
        print(f"\n🔄 Testing Knowledge Categorization")
        print("-" * 60)
        
        try:
            print("🏷️  Categorizing knowledge...")
            categorization_result = self.categorizer.process(knowledge_points)
            
            print("✅ Knowledge categorized successfully!")
            
            # Extract categorized points and relationships
            categorized_points = categorization_result.get('categorized_points', [])
            relationships = categorization_result.get('category_relationships', [])
            summary = categorization_result.get('summary', {})
            
            print(f"   📊 Total knowledge points: {len(categorized_points)}")
            print(f"   🔗 Total relationships: {len(relationships)}")
            
            # Show categorization results by category
            print(f"\n📊 Categorization Results:")
            category_counts = {}
            for rel in relationships:
                cat_id = rel.category_id
                category_counts[cat_id] = category_counts.get(cat_id, 0) + 1
            
            for cat_id, count in category_counts.items():
                print(f"   📂 {cat_id}: {count} knowledge points")
                
                # Show sample from this category
                sample_rel = next((r for r in relationships if r.category_id == cat_id), None)
                if sample_rel:
                    # Find the corresponding knowledge point
                    sample_kp = next((cp['knowledge_point'] for cp in categorized_points 
                                    if cp['knowledge_point'].id == sample_rel.knowledge_point_id), None)
                    if sample_kp:
                        preview = sample_kp.content[:80] + "..." if len(sample_kp.content) > 80 else sample_kp.content
                        print(f"      Sample: {preview}")
                        print(f"      Confidence: {sample_rel.confidence:.2f}")
                print()
            
            print(f"✅ Total categorized points: {len(categorized_points)}")
            
            return categorization_result
            
        except Exception as e:
            print(f"❌ Knowledge categorization failed: {str(e)}")
            return None
    
    def test_complete_phase2_pipeline(self, file_path: str):
        """Test the complete Phase 2 pipeline including Phase 1."""
        print(f"\n🚀 Testing Complete Phase 2 Pipeline: {Path(file_path).name}")
        print("=" * 80)
        
        # Step 1: Load document (needed for Phase 2)
        try:
            document = self.loader.load_document(file_path)
            print(f"✅ Document loaded for Phase 2 processing")
        except Exception as e:
            print(f"❌ Failed to load document: {str(e)}")
            return False
        
        # Step 2: Extract meta knowledge
        knowledge_points = self.test_meta_knowledge_extraction(document, Path(file_path).name)
        if not knowledge_points:
            return False
        
        # Step 3: Categorize knowledge
        categorization_result = self.test_knowledge_categorization(knowledge_points)
        if not categorization_result:
            return False
        
        print(f"\n✅ Complete Phase 2 pipeline successful for {Path(file_path).name}!")
        
        # Summary statistics
        categorized_points = categorization_result.get('categorized_points', [])
        relationships = categorization_result.get('category_relationships', [])
        unique_categories = len(set(r.category_id for r in relationships))
        
        print(f"\n📈 Pipeline Summary:")
        print(f"   📄 Document: {Path(file_path).name}")
        print(f"   📝 Content length: {len(document.content):,} characters")
        print(f"   🧠 Knowledge points: {len(knowledge_points)}")
        print(f"   🏷️  Categories: {unique_categories}")
        print(f"   🔗 Relationships: {len(relationships)}")
        
        return True
    
    def test_knowledge_quality(self, knowledge_points: list):
        """Test and analyze knowledge quality metrics."""
        print(f"\n🔄 Testing Knowledge Quality Analysis")
        print("-" * 60)
        
        if not knowledge_points:
            print("❌ No knowledge points to analyze")
            return
        
        # Confidence analysis
        confidences = [kp.confidence for kp in knowledge_points]
        avg_confidence = sum(confidences) / len(confidences)
        high_confidence = len([c for c in confidences if c >= 0.8])
        medium_confidence = len([c for c in confidences if 0.5 <= c < 0.8])
        low_confidence = len([c for c in confidences if c < 0.5])
        
        print(f"📊 Confidence Analysis:")
        print(f"   Average confidence: {avg_confidence:.3f}")
        print(f"   High confidence (≥0.8): {high_confidence} points ({high_confidence/len(knowledge_points)*100:.1f}%)")
        print(f"   Medium confidence (0.5-0.8): {medium_confidence} points ({medium_confidence/len(knowledge_points)*100:.1f}%)")
        print(f"   Low confidence (<0.5): {low_confidence} points ({low_confidence/len(knowledge_points)*100:.1f}%)")
        
        # Content length analysis
        content_lengths = [len(kp.content) for kp in knowledge_points]
        avg_length = sum(content_lengths) / len(content_lengths)
        
        print(f"\n📏 Content Analysis:")
        print(f"   Average content length: {avg_length:.1f} characters")
        print(f"   Shortest content: {min(content_lengths)} characters")
        print(f"   Longest content: {max(content_lengths)} characters")
        
        # Knowledge type distribution
        type_counts = {}
        for kp in knowledge_points:
            kp_type = kp.type
            type_counts[kp_type] = type_counts.get(kp_type, 0) + 1
        
        print(f"\n🏷️  Knowledge Type Distribution:")
        for kp_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / len(knowledge_points) * 100
            print(f"   {kp_type}: {count} points ({percentage:.1f}%)")
    
    def test_error_handling(self):
        """Test error handling scenarios for Phase 2."""
        print(f"\n🧪 Testing Phase 2 Error Handling Scenarios")
        print("=" * 80)
        
        # Test 1: Empty document
        print("\n🔬 Test 1: Empty document content")
        try:
            from opendxa.knows.core.base import Document
            from datetime import datetime
            empty_doc = Document(
                id="test_empty",
                source="test",
                content="",
                format="txt",
                metadata={},
                created_at=datetime.now()
            )
            result = self.meta_extractor.process(empty_doc)
            print(f"✅ Handled empty document: {len(result)} knowledge points")
        except Exception as e:
            print(f"✅ Correctly handled error: {str(e)}")
        
        # Test 2: Very short document
        print("\n🔬 Test 2: Very short document")
        try:
            from opendxa.knows.core.base import Document
            from datetime import datetime
            short_doc = Document(
                id="test_short",
                source="test",
                content="Hello world.",
                format="txt",
                metadata={},
                created_at=datetime.now()
            )
            result = self.meta_extractor.process(short_doc)
            print(f"✅ Handled short document: {len(result)} knowledge points")
        except Exception as e:
            print(f"✅ Correctly handled error: {str(e)}")
        
        # Test 3: Invalid input types
        print("\n🔬 Test 3: Invalid input types")
        try:
            self.meta_extractor.process(None)
            print("❌ Should have failed!")
        except Exception as e:
            print(f"✅ Correctly handled error: {str(e)}")
        
        try:
            self.categorizer.process("not_a_list")
            print("❌ Should have failed!")
        except Exception as e:
            print(f"✅ Correctly handled error: {str(e)}")
    
    def interactive_testing_menu(self):
        """Interactive menu for testing Phase 2 functionality."""
        while True:
            print(f"\n🎯 Phase 2 Interactive Testing Menu")
            print("=" * 50)
            print("1. List available documents")
            print("2. Test individual document (complete Phase 2 pipeline)")
            print("3. Test meta knowledge extraction only")
            print("4. Test knowledge categorization only")
            print("5. Test knowledge quality analysis")
            print("6. Test error handling scenarios")
            print("7. Test all documents (batch)")
            print("8. Exit")
            
            try:
                choice = input(f"\nSelect option (1-8): ").strip()
                
                if choice == "1":
                    self.list_available_documents()
                    
                elif choice == "2":
                    docs = self.list_available_documents()
                    if docs:
                        file_name = input(f"\nEnter filename to test: ").strip()
                        file_path = self.docs_dir / file_name
                        if file_path.exists():
                            self.test_complete_phase2_pipeline(str(file_path))
                        else:
                            print(f"❌ File not found: {file_name}")
                
                elif choice == "3":
                    docs = self.list_available_documents()
                    if docs:
                        file_name = input(f"\nEnter filename to test: ").strip()
                        file_path = self.docs_dir / file_name
                        if file_path.exists():
                            document = self.loader.load_document(str(file_path))
                            self.test_meta_knowledge_extraction(document, file_name)
                        else:
                            print(f"❌ File not found: {file_name}")
                
                elif choice == "4":
                    docs = self.list_available_documents()
                    if docs:
                        file_name = input(f"\nEnter filename to test: ").strip()
                        file_path = self.docs_dir / file_name
                        if file_path.exists():
                            document = self.loader.load_document(str(file_path))
                            knowledge_points = self.test_meta_knowledge_extraction(document, file_name)
                            if knowledge_points:
                                self.test_knowledge_categorization(knowledge_points)
                        else:
                            print(f"❌ File not found: {file_name}")
                
                elif choice == "5":
                    docs = self.list_available_documents()
                    if docs:
                        file_name = input(f"\nEnter filename to test: ").strip()
                        file_path = self.docs_dir / file_name
                        if file_path.exists():
                            document = self.loader.load_document(str(file_path))
                            knowledge_points = self.test_meta_knowledge_extraction(document, file_name)
                            if knowledge_points:
                                self.test_knowledge_quality(knowledge_points)
                        else:
                            print(f"❌ File not found: {file_name}")
                
                elif choice == "6":
                    self.test_error_handling()
                
                elif choice == "7":
                    docs = self.list_available_documents()
                    if docs:
                        print(f"\n🚀 Testing all {len(docs)} documents...")
                        success_count = 0
                        for doc in docs:
                            success = self.test_complete_phase2_pipeline(doc['path'])
                            if success:
                                success_count += 1
                        print(f"\n📊 Batch Test Results: {success_count}/{len(docs)} successful")
                
                elif choice == "8":
                    print("👋 Exiting Phase 2 testing...")
                    break
                    
                else:
                    print("❌ Invalid choice. Please select 1-8.")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting Phase 2 testing...")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")


def main():
    """Main function to run Phase 2 testing."""
    print("🧪 OpenDXA KNOWS Phase 2 Testing Suite")
    print("🧠 Meta Knowledge Extraction & Categorization Test")
    print("=" * 80)
    
    # Set up paths
    script_dir = Path(__file__).parent
    docs_dir = script_dir / "docs"
    
    print(f"📍 Testing script location: {script_dir}")
    print(f"📁 Documents directory: {docs_dir}")
    
    # Check if documents directory exists
    if not docs_dir.exists():
        print(f"❌ Documents directory not found: {docs_dir}")
        print(f"Please create the directory and add some test documents.")
        return False
    
    # Initialize tester
    tester = Phase2Tester(str(docs_dir))
    
    # Show available documents
    docs = tester.list_available_documents()
    if not docs:
        print(f"❌ No documents found in {docs_dir}")
        return False
    
    # Start interactive testing
    tester.interactive_testing_menu()
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Testing interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 