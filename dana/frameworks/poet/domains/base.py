"""
Base classes for POET domain templates.

Domain templates define how functions are enhanced with the P→O→E→T pattern:
- Perceive: Input validation and preprocessing
- Operate: Enhanced execution with reliability features
- Enforce: Output validation and quality assurance
- Train: Learning from feedback (optional, when optimize_for is specified)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dana.common.utils.logging import DANA_LOGGER


@dataclass
class FunctionInfo:
    """Information about a function being enhanced"""

    name: str
    source_code: str
    signature: str
    docstring: str | None
    annotations: dict[str, Any]
    file_path: Path | None

    # POET configuration
    domain: str
    retries: int
    timeout: int | None
    optimize_for: str | None
    enable_monitoring: bool
    cache_strategy: str
    fallback_strategy: str


@dataclass
class CodeBlock:
    """A generated code block with metadata"""

    code: str
    dependencies: list[str]
    imports: list[str]
    metadata: dict[str, Any]


class DomainTemplate(ABC):
    """
    Base class for domain templates that define P→O→E→T enhancement patterns.

    Supports inheritance - child domains can extend parent domains by calling
    parent methods and adding their own enhancements.
    """

    def __init__(self, parent: "DomainTemplate | None" = None):
        self.parent = parent
        self.name = self.__class__.__name__.replace("Domain", "").lower()

    def generate_enhanced_function(self, func_info: FunctionInfo) -> str:
        """
        Generate complete enhanced function with P→O→E(→T) pattern.

        This is the main entry point that orchestrates all phases.
        """
        DANA_LOGGER.info(f"Generating enhanced function for domain '{self.name}'")

        # Generate individual phases
        perceive_block = self.generate_perceive(func_info)
        operate_block = self.generate_operate(func_info)
        enforce_block = self.generate_enforce(func_info)

        # Generate train phase if learning is enabled
        train_block = None
        if func_info.optimize_for:
            train_block = self.generate_train(func_info)

        # Orchestrate all phases into complete function
        return self._generate_orchestrator(func_info, perceive_block, operate_block, enforce_block, train_block)

    def generate_perceive(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate Perceive phase with inheritance support"""
        parent_block = None
        if self.parent:
            parent_block = self.parent.generate_perceive(func_info)

        own_block = self._generate_perceive(func_info)
        merged = self._merge_code_blocks(parent_block, own_block, "perceive")
        assert merged is not None  # _merge_code_blocks never returns None
        return merged

    def generate_operate(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate Operate phase with inheritance support"""
        parent_block = None
        if self.parent:
            parent_block = self.parent.generate_operate(func_info)

        own_block = self._generate_operate(func_info)
        merged = self._merge_code_blocks(parent_block, own_block, "operate")
        assert merged is not None  # _merge_code_blocks never returns None
        return merged

    def generate_enforce(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate Enforce phase with inheritance support"""
        parent_block = None
        if self.parent:
            parent_block = self.parent.generate_enforce(func_info)

        own_block = self._generate_enforce(func_info)
        merged = self._merge_code_blocks(parent_block, own_block, "enforce")
        assert merged is not None  # _merge_code_blocks never returns None
        return merged

    def generate_train(self, func_info: FunctionInfo) -> CodeBlock | None:
        """Generate Train phase with inheritance support (only if optimize_for specified)"""
        if not func_info.optimize_for:
            return None

        parent_block = None
        if self.parent:
            parent_block = self.parent.generate_train(func_info)

        own_block = self._generate_train(func_info)
        if own_block is None and parent_block is None:
            return None

        return self._merge_code_blocks(parent_block, own_block, "train")

    # Abstract methods that child classes must implement
    @abstractmethod
    def _generate_perceive(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate domain-specific Perceive phase"""
        pass

    @abstractmethod
    def _generate_operate(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate domain-specific Operate phase"""
        pass

    @abstractmethod
    def _generate_enforce(self, func_info: FunctionInfo) -> CodeBlock:
        """Generate domain-specific Enforce phase"""
        pass

    def _generate_train(self, func_info: FunctionInfo) -> CodeBlock | None:
        """Generate domain-specific Train phase (optional, override if needed)"""
        return None

    def _merge_code_blocks(self, parent: CodeBlock | None, child: CodeBlock | None, phase: str) -> CodeBlock:
        """Merge parent and child code blocks intelligently"""
        if parent is None and child is None:
            return CodeBlock(code=f"# No {phase} logic defined", dependencies=[], imports=[], metadata={"phase": phase, "source": "empty"})

        if parent is None:
            assert child is not None  # child cannot be None here since both None case was handled above
            return child

        if child is None:
            assert parent is not None  # We already checked parent and child can't both be None
            return parent

        # Merge code with clear separation
        merged_code = f"""
# === {phase.title()} Phase: Parent Domain Logic ===
{parent.code}

# === {phase.title()} Phase: Child Domain Logic ===  
{child.code}
""".strip()

        # Merge dependencies and imports (remove duplicates)
        merged_dependencies = list(set(parent.dependencies + child.dependencies))
        merged_imports = list(set(parent.imports + child.imports))

        # Merge metadata
        merged_metadata = {**parent.metadata, **child.metadata}
        merged_metadata["inheritance"] = True
        merged_metadata["parent_domain"] = self.parent.name if self.parent else None

        return CodeBlock(code=merged_code, dependencies=merged_dependencies, imports=merged_imports, metadata=merged_metadata)

    def _generate_orchestrator(
        self, func_info: FunctionInfo, perceive: CodeBlock, operate: CodeBlock, enforce: CodeBlock, train: CodeBlock | None
    ) -> str:
        """Generate the main orchestrator function that coordinates all phases"""

        # Collect all imports
        all_imports = set()
        for block in [perceive, operate, enforce]:
            all_imports.update(block.imports)
        if train:
            all_imports.update(train.imports)

        imports_section = "\n".join(sorted(all_imports)) if all_imports else ""

        # Generate function signature
        signature = func_info.signature

        # Generate orchestrator
        train_section = ""
        if train:
            train_section = f"""
    # === TRAIN PHASE ===
    # Learn from execution and feedback
    try:
        {self._indent_code(train.code, 8)}
    except Exception as train_error:
        log(f"Train phase failed: {{train_error}}")
"""

        orchestrator = f"""
{imports_section}

def enhanced_{func_info.name}{signature}:
    \"\"\"
    Enhanced version of {func_info.name} with POET domain: {func_info.domain}
    
    Original docstring: {func_info.docstring or "None"}
    
    Enhancement includes:
    - Perceive: Input validation and preprocessing
    - Operate: Enhanced execution with reliability  
    - Enforce: Output validation and quality assurance{" - Train: Learning from feedback" if train else ""}
    \"\"\"
    import time
    import uuid
    from ..core.types import POETResult
    
    # Generate execution ID for tracking
    execution_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # === PERCEIVE PHASE ===
        # Validate and preprocess inputs
        {self._indent_code(perceive.code, 8)}
        
        # === OPERATE PHASE ===  
        # Execute with enhanced reliability
        {self._indent_code(operate.code, 8)}
        
        # === ENFORCE PHASE ===
        # Validate and process outputs
        {self._indent_code(enforce.code, 8)}
        
        {train_section}
        
        # Return enhanced result
        execution_time = time.time() - start_time
        return POETResult(
            value=final_result,
            execution_id=execution_id,
            function_name="{func_info.name}",
            domain="{func_info.domain}",
            enhanced=True,
            metadata={{
                "execution_time": execution_time,
                "retries_used": getattr(locals(), 'retries_used', 0),
                "domain": "{func_info.domain}",
                "phases_executed": ["perceive", "operate", "enforce"{', "train"' if train else ""}]
            }}
        )
        
    except Exception as e:
        # Fallback handling
        execution_time = time.time() - start_time
        log(f"POET enhancement failed: {{e}}")
        
        if "{func_info.fallback_strategy}" == "original":
            # Execute original function
            {self._indent_code(func_info.source_code, 12)}
            return POETResult(
                value=result,
                execution_id=execution_id,
                function_name="{func_info.name}",
                domain="{func_info.domain}",
                enhanced=False,
                metadata={{
                    "execution_time": execution_time,
                    "fallback_used": True,
                    "error": str(e)
                }}
            )
        else:
            raise RuntimeError(f"POET enhancement failed: {{e}}") from e

# Main enhanced function
result = enhanced_{func_info.name}({", ".join(f"{p}={p}" for p in self._extract_parameter_names(func_info.signature))})
""".strip()

        return orchestrator

    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code block by specified number of spaces"""
        indent = " " * spaces
        return "\n".join(indent + line if line.strip() else line for line in code.split("\n"))

    def _extract_parameter_names(self, signature: str) -> list[str]:
        """Extract parameter names from function signature"""
        # Simple extraction - could be made more robust
        if "(" not in signature or ")" not in signature:
            return []

        params_str = signature.split("(")[1].split(")")[0]
        if not params_str.strip():
            return []

        params = []
        for param in params_str.split(","):
            param = param.strip()
            if ":" in param:
                param = param.split(":")[0].strip()
            if "=" in param:
                param = param.split("=")[0].strip()
            if param and not param.startswith("*"):
                params.append(param)

        return params


class BaseDomainTemplate(DomainTemplate):
    """
    Minimal base implementation that provides basic P→O→E pattern.
    Other domains can inherit from this for basic functionality.
    """

    def _generate_perceive(self, func_info: FunctionInfo) -> CodeBlock:
        return CodeBlock(
            code="""
# Basic input validation
if not all(param is not None for param in locals().values()):
    raise ValueError("All parameters must be non-None")
""".strip(),
            dependencies=[],
            imports=[],
            metadata={"phase": "perceive", "domain": "base"},
        )

    def _generate_operate(self, func_info: FunctionInfo) -> CodeBlock:
        retry_logic = f"""
# Execute with retry logic
retries_used = 0
max_retries = {func_info.retries}

for attempt in range(max_retries + 1):
    try:
        # Execute original function logic
        {self._indent_code(func_info.source_code, 8)}
        break
    except Exception as e:
        retries_used = attempt + 1
        if attempt == max_retries:
            raise RuntimeError(f"Function failed after {{max_retries}} retries: {{e}}") from e
        
        # Exponential backoff
        import time
        time.sleep(0.1 * (2 ** attempt))
        log(f"Retry {{attempt + 1}}/{{max_retries}} after error: {{e}}")
""".strip()

        return CodeBlock(
            code=retry_logic,
            dependencies=[],
            imports=["import time"],
            metadata={"phase": "operate", "domain": "base", "retries": func_info.retries},
        )

    def _generate_enforce(self, func_info: FunctionInfo) -> CodeBlock:
        return CodeBlock(
            code="""
# Basic output validation
if result is None:
    raise ValueError("Function returned None - this may indicate an error")

final_result = result
""".strip(),
            dependencies=[],
            imports=[],
            metadata={"phase": "enforce", "domain": "base"},
        )
