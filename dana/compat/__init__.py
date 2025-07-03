"""Compatibility layer for smooth migration from opendxa to dana."""

import sys
import warnings
from typing import Any, Optional


def setup_dual_imports() -> None:
    """Allow imports from both old and new paths during migration."""
    # Phase 1: Core Dana Language mappings
    mappings = [
        # Parser mappings
        ('opendxa.dana.sandbox.parser', 'dana.core.lang.parser'),
        ('opendxa.dana.sandbox.parser.dana_parser', 'dana.core.lang.parser.dana_parser'),
        ('opendxa.dana.sandbox.parser.strict_dana_parser', 'dana.core.lang.parser.strict_dana_parser'),
        ('opendxa.dana.sandbox.parser.ast', 'dana.core.lang.ast'),
        
        # Interpreter mappings
        ('opendxa.dana.sandbox.interpreter', 'dana.core.lang.interpreter'),
        ('opendxa.dana.sandbox.interpreter.dana_interpreter', 'dana.core.lang.interpreter.dana_interpreter'),
        
        # Sandbox mappings
        ('opendxa.dana.sandbox.dana_sandbox', 'dana.core.lang.dana_sandbox'),
        ('opendxa.dana.sandbox.context_manager', 'dana.core.lang.context_manager'),
        ('opendxa.dana.sandbox.sandbox_context', 'dana.core.lang.sandbox_context'),
        ('opendxa.dana.sandbox.execution_status', 'dana.core.lang.execution_status'),
        ('opendxa.dana.sandbox.exceptions', 'dana.core.lang.exceptions'),
        ('opendxa.dana.sandbox.log_manager', 'dana.core.lang.log_manager'),
    ]
    
    # Phase 2: Runtime and Module System mappings
    phase2_mappings = [
        # Module system mappings
        ('opendxa.dana.module', 'dana.core.runtime.modules'),
        ('opendxa.dana.module.core', 'dana.core.runtime.modules.core'),
        ('opendxa.dana.module.core.registry', 'dana.core.runtime.modules.core.registry'),
        ('opendxa.dana.module.core.loader', 'dana.core.runtime.modules.core.loader'),
        ('opendxa.dana.module.core.types', 'dana.core.runtime.modules.core.types'),
        ('opendxa.dana.module.core.errors', 'dana.core.runtime.modules.core.errors'),
        
        # REPL mappings
        ('opendxa.dana.exec', 'dana.core.repl'),
        ('opendxa.dana.exec.dana', 'dana.core.repl.dana'),
        ('opendxa.dana.exec.repl', 'dana.core.repl.repl'),
    ]
    
    mappings.extend(phase2_mappings)
    
    # Phase 3: Standard Library Functions mappings
    phase3_mappings = [
        # Function system mappings
        ('opendxa.dana.sandbox.interpreter.functions', 'dana.core.stdlib'),
        ('opendxa.dana.sandbox.interpreter.functions.function_registry', 'dana.core.stdlib.function_registry'),
        ('opendxa.dana.sandbox.interpreter.functions.dana_function', 'dana.core.stdlib.dana_function'),
        ('opendxa.dana.sandbox.interpreter.functions.core', 'dana.core.stdlib.core'),
        ('opendxa.dana.sandbox.interpreter.functions.core.register_core_functions', 'dana.core.stdlib.core.register_core_functions'),
        
        # Individual core functions
        ('opendxa.dana.sandbox.interpreter.functions.core.log_function', 'dana.core.stdlib.core.log_function'),
        ('opendxa.dana.sandbox.interpreter.functions.core.reason_function', 'dana.core.stdlib.core.reason_function'),
        ('opendxa.dana.sandbox.interpreter.functions.core.str_function', 'dana.core.stdlib.core.str_function'),
        ('opendxa.dana.sandbox.interpreter.functions.core.print_function', 'dana.core.stdlib.core.print_function'),
        ('opendxa.dana.sandbox.interpreter.functions.core.agent_function', 'dana.core.stdlib.core.agent_function'),
        ('opendxa.dana.sandbox.interpreter.functions.core.poet_function', 'dana.core.stdlib.core.poet_function'),
        ('opendxa.dana.sandbox.interpreter.functions.core.knows_functions', 'dana.core.stdlib.core.knows_functions'),
    ]
    
    mappings.extend(phase3_mappings)
    
    # Phase 4: Common Utilities mappings
    phase4_mappings = [
        # Common utilities mappings
        ('opendxa.common', 'dana.common'),
        ('opendxa.common.utils.logging', 'dana.common.utils.logging'),
        ('opendxa.common.utils.logging.dxa_logger', 'dana.common.utils.logging.dana_logger'),
        ('opendxa.common.mixins', 'dana.common.mixins'),
        ('opendxa.common.resource', 'dana.common.resource'),
        ('opendxa.common.graph', 'dana.common.graph'),
        ('opendxa.common.io', 'dana.common.io'),
        ('opendxa.common.config', 'dana.common.config'),
        ('opendxa.common.capability', 'dana.common.capability'),
        
        # Specific component mappings
        ('opendxa.common.mixins.loggable', 'dana.common.mixins.loggable'),
        ('opendxa.common.mixins.configurable', 'dana.common.mixins.configurable'),
        ('opendxa.common.mixins.identifiable', 'dana.common.mixins.identifiable'),
        ('opendxa.common.resource.llm_resource', 'dana.common.resource.llm_resource'),
        ('opendxa.common.resource.memory_resource', 'dana.common.resource.memory_resource'),
        ('opendxa.common.graph.directed_graph', 'dana.common.graph.directed_graph'),
        ('opendxa.common.io.console_io', 'dana.common.io.console_io'),
    ]
    
    mappings.extend(phase4_mappings)
    
    # Phase 5: POET Framework mappings
    phase5_mappings = [
        # POET framework mappings
        ('opendxa.dana.poet', 'dana.frameworks.poet'),
        ('opendxa.dana.poet.decorator', 'dana.frameworks.poet.decorator'),
        ('opendxa.dana.poet.types', 'dana.frameworks.poet.types'),
        ('opendxa.dana.poet.enhancer', 'dana.frameworks.poet.enhancer'),
        ('opendxa.dana.poet.client', 'dana.frameworks.poet.client'),
        ('opendxa.dana.poet.storage', 'dana.frameworks.poet.storage'),
        ('opendxa.dana.poet.feedback', 'dana.frameworks.poet.feedback'),
        ('opendxa.dana.poet.errors', 'dana.frameworks.poet.errors'),
        
        # POET domains mappings
        ('opendxa.dana.poet.domains', 'dana.frameworks.poet.domains'),
        ('opendxa.dana.poet.domains.base', 'dana.frameworks.poet.domains.base'),
        ('opendxa.dana.poet.domains.computation', 'dana.frameworks.poet.domains.computation'),
        ('opendxa.dana.poet.domains.llm_optimization', 'dana.frameworks.poet.domains.llm_optimization'),
        ('opendxa.dana.poet.domains.ml_monitoring', 'dana.frameworks.poet.domains.ml_monitoring'),
        ('opendxa.dana.poet.domains.prompt_optimization', 'dana.frameworks.poet.domains.prompt_optimization'),
        ('opendxa.dana.poet.domains.registry', 'dana.frameworks.poet.domains.registry'),
        
        # POET phases mappings
        ('opendxa.dana.poet.phases', 'dana.frameworks.poet.phases'),
        ('opendxa.dana.poet.phases.perceive', 'dana.frameworks.poet.phases.perceive'),
        ('opendxa.dana.poet.phases.operate', 'dana.frameworks.poet.phases.operate'),
        ('opendxa.dana.poet.phases.enforce', 'dana.frameworks.poet.phases.enforce'),
    ]
    
    mappings.extend(phase5_mappings)
    
    # Phase 6: KNOWS Framework mappings
    phase6_mappings = [
        # KNOWS framework mappings
        ('opendxa.knows', 'dana.frameworks.knows'),
        ('opendxa.knows.core', 'dana.frameworks.knows.core'),
        ('opendxa.knows.core.base', 'dana.frameworks.knows.core.base'),
        ('opendxa.knows.core.registry', 'dana.frameworks.knows.core.registry'),
        
        # Document processing mappings
        ('opendxa.knows.document', 'dana.frameworks.knows.document'),
        ('opendxa.knows.document.loader', 'dana.frameworks.knows.document.loader'),
        ('opendxa.knows.document.parser', 'dana.frameworks.knows.document.parser'),
        ('opendxa.knows.document.extractor', 'dana.frameworks.knows.document.extractor'),
        
        # Knowledge extraction mappings
        ('opendxa.knows.extraction', 'dana.frameworks.knows.extraction'),
        ('opendxa.knows.extraction.meta', 'dana.frameworks.knows.extraction.meta'),
        ('opendxa.knows.extraction.meta.extractor', 'dana.frameworks.knows.extraction.meta.extractor'),
        ('opendxa.knows.extraction.meta.categorizer', 'dana.frameworks.knows.extraction.meta.categorizer'),
        ('opendxa.knows.extraction.context', 'dana.frameworks.knows.extraction.context'),
        ('opendxa.knows.extraction.context.expander', 'dana.frameworks.knows.extraction.context.expander'),
        ('opendxa.knows.extraction.context.similarity', 'dana.frameworks.knows.extraction.context.similarity'),
    ]
    
    mappings.extend(phase6_mappings)
    
    # Phase 7: Agent Framework mappings
    phase7_mappings = [
        # Agent framework mappings
        ('opendxa.agent', 'dana.frameworks.agent'),
        ('opendxa.agent.agent', 'dana.frameworks.agent.agent'),
        ('opendxa.agent.agent_factory', 'dana.frameworks.agent.agent_factory'),
        ('opendxa.agent.agent_config', 'dana.frameworks.agent.agent_config'),
        ('opendxa.agent.agent_runtime', 'dana.frameworks.agent.agent_runtime'),
        
        # Agent capability mappings
        ('opendxa.agent.capability', 'dana.frameworks.agent.capability'),
        ('opendxa.agent.capability.domain_expertise', 'dana.frameworks.agent.capability.domain_expertise'),
        ('opendxa.agent.capability.memory_capability', 'dana.frameworks.agent.capability.memory_capability'),
        ('opendxa.agent.capability.capability_factory', 'dana.frameworks.agent.capability.capability_factory'),
        
        # Agent resource mappings
        ('opendxa.agent.resource', 'dana.frameworks.agent.resource'),
        ('opendxa.agent.resource.agent_resource', 'dana.frameworks.agent.resource.agent_resource'),
        ('opendxa.agent.resource.expert_resource', 'dana.frameworks.agent.resource.expert_resource'),
        ('opendxa.agent.resource.resource_factory', 'dana.frameworks.agent.resource.resource_factory'),
    ]
    
    mappings.extend(phase7_mappings)
    
    # Phase 8: External Integrations mappings
    phase8_mappings = [
        # Python integration mappings
        ('opendxa.integrations.python', 'dana.integrations.python'),
        ('opendxa.integrations.python.core', 'dana.integrations.python.core'),
        ('opendxa.integrations.python.core.module_importer', 'dana.integrations.python.core.module_importer'),
        ('opendxa.integrations.python.dana_module', 'dana.integrations.python.dana_module'),
        
        # RAG integration mappings
        ('opendxa.integrations.rag', 'dana.integrations.rag'),
        ('opendxa.integrations.rag.common', 'dana.integrations.rag.common'),
        
        # MCP integration mappings
        ('opendxa.integrations.mcp', 'dana.integrations.mcp'),
        ('opendxa.integrations.mcp.core', 'dana.integrations.mcp.core'),
        ('opendxa.integrations.mcp.core.mcp_resource', 'dana.integrations.mcp.core.mcp_resource'),
        ('opendxa.integrations.mcp.a2a', 'dana.integrations.mcp.a2a'),
        ('opendxa.integrations.mcp.a2a.resource', 'dana.integrations.mcp.a2a.resource'),
        ('opendxa.integrations.mcp.a2a.resource.a2a', 'dana.integrations.mcp.a2a.resource.a2a'),
        ('opendxa.integrations.mcp.a2a.resource.a2a.a2a_agent', 'dana.integrations.mcp.a2a.resource.a2a.a2a_agent'),
        
        # LLM integration mappings
        ('opendxa.integrations.llm', 'dana.integrations.llm'),
        
        # Generic integration mappings
        ('opendxa.integrations', 'dana.integrations'),
    ]
    
    mappings.extend(phase8_mappings)
    
    # Add all mappings to the compatibility importer
    for old_path, new_path in mappings:
        _compat_importer.add_mapping(old_path, new_path)


def add_compatibility_mapping(old_path: str, new_path: str) -> None:
    """Add a compatibility mapping from old import path to new."""
    if new_path in sys.modules:
        sys.modules[old_path] = sys.modules[new_path]


def deprecation_warning(old_path: str, new_path: str, removal_version: str = "2.0.0") -> None:
    """Issue a deprecation warning for old import paths."""
    warnings.warn(
        f"Import from '{old_path}' is deprecated and will be removed in version {removal_version}. "
        f"Please use '{new_path}' instead.",
        DeprecationWarning,
        stacklevel=3
    )


class CompatibilityImporter:
    """Custom importer for handling old import paths."""
    
    def __init__(self):
        self.mappings = {}
    
    def add_mapping(self, old_path: str, new_path: str) -> None:
        """Add an import path mapping."""
        self.mappings[old_path] = new_path
    
    def find_module(self, fullname: str, path: Optional[Any] = None) -> Optional['CompatibilityImporter']:
        """Find module using compatibility mappings."""
        if fullname in self.mappings or fullname.startswith(tuple(self.mappings.keys())):
            return self
        return None
    
    def load_module(self, fullname: str) -> Any:
        """Load module from new path with deprecation warning."""
        # Check direct mapping
        if fullname in self.mappings:
            new_path = self.mappings[fullname]
            deprecation_warning(fullname, new_path)
            __import__(new_path)
            return sys.modules.setdefault(fullname, sys.modules[new_path])
        
        # Check prefix mapping
        for old_prefix, new_prefix in self.mappings.items():
            if fullname.startswith(old_prefix):
                new_path = fullname.replace(old_prefix, new_prefix, 1)
                deprecation_warning(fullname, new_path)
                __import__(new_path)
                return sys.modules.setdefault(fullname, sys.modules[new_path])
        
        raise ImportError(f"No module named {fullname}")


# Global compatibility importer instance
_compat_importer = CompatibilityImporter()


def install_compatibility_layer() -> None:
    """Install the compatibility import layer."""
    if _compat_importer not in sys.meta_path:
        sys.meta_path.insert(0, _compat_importer)


def uninstall_compatibility_layer() -> None:
    """Remove the compatibility import layer."""
    if _compat_importer in sys.meta_path:
        sys.meta_path.remove(_compat_importer)


# Convenience function to set up everything
def setup_migration_compatibility() -> None:
    """Set up all compatibility features for migration."""
    install_compatibility_layer()
    setup_dual_imports()