#!/bin/bash
# Verify completion of migration phases

PHASE=${1:-0}
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Verifying Phase $PHASE completion...${NC}"

case $PHASE in
  0) # Pre-Migration Setup
    echo "Testing existing functionality..."
    
    # Check if dana directory exists
    if [ -d "dana" ]; then
      echo -e "${GREEN}✓ Dana directory structure created${NC}"
    else
      echo -e "${RED}✗ Dana directory not found${NC}"
      exit 1
    fi
    
    # Check if compatibility layer exists
    if [ -f "dana/compat/__init__.py" ]; then
      echo -e "${GREEN}✓ Compatibility layer created${NC}"
    else
      echo -e "${RED}✗ Compatibility layer not found${NC}"
      exit 1
    fi
    
    # Run basic tests to ensure nothing is broken
    echo "Running existing tests..."
    if uv run pytest tests/dana/test_basic.py -v -q; then
      echo -e "${GREEN}✓ Existing tests pass${NC}"
    else
      echo -e "${RED}✗ Some tests failed${NC}"
      exit 1
    fi
    ;;
    
  1) # Core Dana Language
    echo "Testing Core Dana Language migration..."
    
    # Test parser import from new location
    uv run python -c "from dana.core.lang.parser import DanaParser" 2>/dev/null
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✓ New parser import works${NC}"
    else
      echo -e "${RED}✗ New parser import failed${NC}"
      exit 1
    fi
    
    # Test old import still works
    uv run python -c "from opendxa.dana.sandbox.parser import DanaParser" 2>/dev/null
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✓ Old parser import still works${NC}"
    else
      echo -e "${RED}✗ Old parser import failed${NC}"
      exit 1
    fi
    
    # Run parser tests
    uv run pytest tests/dana/test_parser.py -v -q
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✓ Parser tests pass${NC}"
    else
      echo -e "${RED}✗ Parser tests failed${NC}"
      exit 1
    fi
    
    # Test Dana execution
    dana examples/dana/na/basic_math_pipeline.na
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✓ Dana execution works${NC}"
    else
      echo -e "${RED}✗ Dana execution failed${NC}"
      exit 1
    fi
    ;;
    
  2) # Runtime and Module System
    echo "Testing Runtime and Module System migration..."
    
    # Test module system
    dana examples/dana/na/module_import_example.na
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✓ Module imports work${NC}"
    else
      echo -e "${RED}✗ Module imports failed${NC}"
      exit 1
    fi
    
    # Test REPL
    echo "exit()" | dana
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✓ REPL works${NC}"
    else
      echo -e "${RED}✗ REPL failed${NC}"
      exit 1
    fi
    ;;
    
  3) # Standard Library Functions
    echo "Testing Standard Library migration..."
    
    # Run function tests
    for category in core math string ai; do
      if uv run pytest tests/dana/functions/test_${category}_functions.py -v -q; then
        echo -e "${GREEN}✓ ${category} functions pass${NC}"
      else
        echo -e "${RED}✗ ${category} functions failed${NC}"
        exit 1
      fi
    done
    ;;
    
  *) 
    echo -e "${RED}Unknown phase: $PHASE${NC}"
    exit 1
    ;;
esac

echo -e "${GREEN}Phase $PHASE verification complete!${NC}"