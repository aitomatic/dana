# OpenDXA TODOs

This document tracks improvement opportunities and refactoring recommendations for the OpenDXA codebase.

## AST Refactoring Opportunities

### Context
Review of `opendxa/dana/sandbox/parser/ast.py` revealed several opportunities for simplification and consistency improvements. Analysis shows 62 Python files import from the AST module, so changes need careful consideration.

### Recommendations by Priority

#### ✅ **Phase 1: Safe & Valuable (LOW IMPACT)**
**Effort**: 1-2 hours, 5-10 files affected

1. **Fix Assignment.value Union Type** ⭐
   ```python
   # Current: Massive inline union with 15+ types
   value: Union[LiteralExpression, Identifier, BinaryExpression, ...]
   
   # Better: Use existing Expression type alias
   value: Expression
   ```
   **Impact**: Only affects files that construct Assignment nodes (~5 files)

2. **Add StatementBody Type Alias** ⭐
   ```python
   StatementBody = list[Statement]
   
   # Use in Conditional, WhileLoop, ForLoop, etc.
   body: StatementBody
   else_body: StatementBody = field(default_factory=list)
   ```
   **Impact**: Pure addition, no breaking changes

#### ⚠️ **Phase 2: Evaluate Impact (MEDIUM IMPACT)** 
**Effort**: 1-2 days, 40+ files affected

3. **Add Base Classes for Location Field**
   ```python
   @dataclass
   class BaseNode:
       location: Location | None = None
   
   @dataclass  
   class BaseExpression(BaseNode):
       pass
   
   @dataclass
   class BaseStatement(BaseNode):
       pass
   ```
   **Benefits**: Eliminates repetitive `location: Location | None = None` in 30+ classes
   **Risk**: Dataclass inheritance can be tricky; need thorough testing

4. **Consolidate Collection Literals**
   ```python
   @dataclass
   class CollectionLiteral(BaseExpression):
       collection_type: Literal["list", "set", "tuple"]
       items: list[Expression]
   ```
   **Benefits**: Reduces TupleLiteral, ListLiteral, SetLiteral to single class
   **Risk**: Affects transformers, executors, type checkers (~15 files)

#### ❌ **Phase 3: Not Recommended (HIGH IMPACT, LOW VALUE)**

5. **Control Flow Statement Consolidation**
   ```python
   @dataclass
   class ControlFlowStatement(BaseStatement):
       statement_type: Literal["break", "continue", "pass"]
   ```
   **Reasoning**: Complexity > benefit, affects every executor/transformer

### Type Consistency Issues to Address

- `FunctionDefinition.name` is `Identifier` but `StructDefinition.name` is `str`
- `WithStatement.as_var` is `str` but could be `Identifier`
- Consider standardizing naming patterns

### Implementation Notes

- **Files most affected by changes**: 
  - All transformer classes (`opendxa/dana/sandbox/parser/transformer/`)
  - All executor classes (`opendxa/dana/sandbox/interpreter/executor/`)
  - Type checker (`opendxa/dana/sandbox/parser/utils/type_checker.py`)
  - Test files (extensive AST node construction)

- **Testing strategy**: 
  - Run full test suite after each phase
  - Pay special attention to transformer tests
  - Test both parsing and execution paths

- **KISS/YAGNI guidance**: Start with Phase 1, evaluate results before proceeding

### Status
- ✅ **Duplications removed** (2025-01-15): Removed duplicate StructDefinition, StructField, StructLiteral, StructArgument classes
- ✅ **Statement transformer refactored** (2025-01-15): Extracted utility methods and decorator handling (1250 → 1067 lines)
- ⏳ **Phase 1 remaining**: Assignment.value simplification and StatementBody alias
- ⏳ **Phase 2 evaluation**: Base classes and collection consolidation
- ❌ **Phase 3 declined**: Control flow consolidation deemed too risky

---

## Other TODOs

<!-- Add other improvement opportunities here --> 