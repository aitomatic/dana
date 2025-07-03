#!/usr/bin/env python3
"""
Phase 1 Human Testing Script: Document Processing

This script allows you to manually test and verify the document processing functionality
of OpenDXA KNOWS Phase 1 components:
- DocumentLoader: Loading documents from various formats
- DocumentParser: Parsing document structure 
- TextExtractor: Extracting clean text content

Usage: python test_phase1_document_processing.py
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
from opendxa.common.utils.logging import DXA_LOGGER


class Phase1Tester:
    """Human testing interface for Phase 1 document processing."""
    
    def __init__(self, docs_dir: str):
        """Initialize the tester with document directory."""
        self.docs_dir = Path(docs_dir)
        self.loader = DocumentLoader()
        self.parser = DocumentParser()
        self.extractor = TextExtractor()
        
        print("🔧 Phase 1 Tester Initialized")
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
    
    def test_document_loading(self, file_path: str):
        """Test document loading functionality."""
        print(f"\n🔄 Testing Document Loading: {Path(file_path).name}")
        print("-" * 60)
        
        try:
            # Test document loading
            print("📥 Loading document...")
            document = self.loader.load_document(file_path)
            
            print("✅ Document loaded successfully!")
            print(f"   📋 ID: {document.id}")
            print(f"   📁 Source: {document.source}")
            print(f"   📝 Format: {document.format}")
            print(f"   📊 Content length: {len(document.content):,} characters")
            print(f"   🕐 Created: {document.created_at}")
            print(f"   🏷️  Metadata keys: {list(document.metadata.keys())}")
            
            # Show content preview
            content_preview = document.content[:200] + "..." if len(document.content) > 200 else document.content
            print(f"\n📖 Content Preview:")
            print(f"   {repr(content_preview)}")
            
            return document
            
        except Exception as e:
            print(f"❌ Loading failed: {str(e)}")
            return None
    
    def test_document_parsing(self, document):
        """Test document parsing functionality."""
        print(f"\n🔄 Testing Document Parsing")
        print("-" * 60)
        
        try:
            print("🔍 Parsing document structure...")
            parsed_doc = self.parser.process(document)
            
            print("✅ Document parsed successfully!")
            print(f"   📄 Original document ID: {parsed_doc.document.id}")
            print(f"   📝 Text content length: {len(parsed_doc.text_content):,} characters")
            print(f"   🏗️  Structured data keys: {list(parsed_doc.structured_data.keys())}")
            print(f"   🏷️  Metadata keys: {list(parsed_doc.metadata.keys())}")
            
            # Show structured data preview if available
            if parsed_doc.structured_data:
                print(f"\n🏗️  Structured Data Preview:")
                for key, value in list(parsed_doc.structured_data.items())[:3]:
                    if isinstance(value, (dict, list)):
                        print(f"   {key}: {type(value).__name__} with {len(value)} items")
                    else:
                        preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                        print(f"   {key}: {preview}")
            
            # Show text content preview
            text_preview = parsed_doc.text_content[:300] + "..." if len(parsed_doc.text_content) > 300 else parsed_doc.text_content
            print(f"\n📝 Parsed Text Preview:")
            print(f"   {repr(text_preview)}")
            
            return parsed_doc
            
        except Exception as e:
            print(f"❌ Parsing failed: {str(e)}")
            return None
    
    def test_text_extraction(self, parsed_doc):
        """Test text extraction functionality."""
        print(f"\n🔄 Testing Text Extraction")
        print("-" * 60)
        
        try:
            print("✂️  Extracting clean text...")
            extracted_text = self.extractor.process(parsed_doc)
            
            print("✅ Text extracted successfully!")
            print(f"   📏 Extracted length: {len(extracted_text):,} characters")
            print(f"   📊 Word count: {len(extracted_text.split()):,} words")
            print(f"   📈 Line count: {len(extracted_text.splitlines()):,} lines")
            
            # Show extraction preview
            text_preview = extracted_text[:400] + "..." if len(extracted_text) > 400 else extracted_text
            print(f"\n✂️  Extracted Text Preview:")
            print("   " + "-" * 50)
            for line in text_preview.splitlines()[:10]:
                print(f"   {line}")
            if len(extracted_text.splitlines()) > 10:
                print("   ...")
            print("   " + "-" * 50)
            
            return extracted_text
            
        except Exception as e:
            print(f"❌ Text extraction failed: {str(e)}")
            return None
    
    def test_complete_pipeline(self, file_path: str):
        """Test the complete document processing pipeline."""
        print(f"\n🚀 Testing Complete Pipeline: {Path(file_path).name}")
        print("=" * 80)
        
        # Step 1: Load document
        document = self.test_document_loading(file_path)
        if not document:
            return False
        
        # Step 2: Parse document
        parsed_doc = self.test_document_parsing(document)
        if not parsed_doc:
            return False
        
        # Step 3: Extract text
        extracted_text = self.test_text_extraction(parsed_doc)
        if not extracted_text:
            return False
        
        print(f"\n✅ Complete pipeline successful for {Path(file_path).name}!")
        return True
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        print(f"\n🧪 Testing Error Handling Scenarios")
        print("=" * 80)
        
        # Test 1: Non-existent file
        print("\n🔬 Test 1: Non-existent file")
        try:
            self.loader.load_document("nonexistent_file.txt")
            print("❌ Should have failed!")
        except Exception as e:
            print(f"✅ Correctly handled error: {str(e)}")
        
        # Test 2: Invalid document format
        print("\n🔬 Test 2: Unsupported format")
        try:
            # Create a temporary file with unsupported extension
            temp_file = self.docs_dir / "test.xyz"
            temp_file.write_text("test content")
            self.loader.load_document(str(temp_file))
            temp_file.unlink()  # Clean up
            print("❌ Should have failed!")
        except Exception as e:
            print(f"✅ Correctly handled error: {str(e)}")
            if temp_file.exists():
                temp_file.unlink()
        
        # Test 3: Invalid input types
        print("\n🔬 Test 3: Invalid input types")
        try:
            self.parser.process("not_a_document")
            print("❌ Should have failed!")
        except Exception as e:
            print(f"✅ Correctly handled error: {str(e)}")
        
        try:
            self.extractor.process("not_a_parsed_document")
            print("❌ Should have failed!")
        except Exception as e:
            print(f"✅ Correctly handled error: {str(e)}")
    
    def interactive_testing_menu(self):
        """Interactive menu for testing individual documents."""
        while True:
            print(f"\n🎯 Phase 1 Interactive Testing Menu")
            print("=" * 50)
            print("1. List available documents")
            print("2. Test individual document (full pipeline)")
            print("3. Test document loading only")
            print("4. Test error handling scenarios")
            print("5. Test all documents (batch)")
            print("6. Exit")
            
            try:
                choice = input(f"\nSelect option (1-6): ").strip()
                
                if choice == "1":
                    self.list_available_documents()
                    
                elif choice == "2":
                    docs = self.list_available_documents()
                    if docs:
                        file_name = input(f"\nEnter filename to test: ").strip()
                        file_path = self.docs_dir / file_name
                        if file_path.exists():
                            self.test_complete_pipeline(str(file_path))
                        else:
                            print(f"❌ File not found: {file_name}")
                
                elif choice == "3":
                    docs = self.list_available_documents()
                    if docs:
                        file_name = input(f"\nEnter filename to test: ").strip()
                        file_path = self.docs_dir / file_name
                        if file_path.exists():
                            self.test_document_loading(str(file_path))
                        else:
                            print(f"❌ File not found: {file_name}")
                
                elif choice == "4":
                    self.test_error_handling()
                
                elif choice == "5":
                    docs = self.list_available_documents()
                    if docs:
                        print(f"\n🚀 Testing all {len(docs)} documents...")
                        success_count = 0
                        for doc in docs:
                            success = self.test_complete_pipeline(doc['path'])
                            if success:
                                success_count += 1
                        print(f"\n📊 Batch Test Results: {success_count}/{len(docs)} successful")
                
                elif choice == "6":
                    print("👋 Exiting Phase 1 testing...")
                    break
                    
                else:
                    print("❌ Invalid choice. Please select 1-6.")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting Phase 1 testing...")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")


def main():
    """Main function to run Phase 1 testing."""
    print("🧪 OpenDXA KNOWS Phase 1 Testing Suite")
    print("📄 Document Processing Components Test")
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
    tester = Phase1Tester(str(docs_dir))
    
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