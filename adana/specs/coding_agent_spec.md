# CodingAgent Implementation Specification

## Overview

The CodingAgent is a specialized agent implementation for software engineering tasks. It demonstrates how the agentic architecture can be used to create domain-specific agents with tailored resources, workflows, and prompts.

## CodingAgent Class

```python
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import subprocess
import json
from ..core.agent import Agent
from ..core.resource import Resource, MethodInfo
from ..core.workflow import Workflow, WorkflowStep
from ..core.prompt_engineer import PromptEngineer

class CodingAgent(Agent):
    """
    Specialized agent for software engineering tasks.
    
    Provides capabilities for:
    - Code analysis and debugging
    - File system operations
    - Git version control
    - Terminal command execution
    - Web search for technical information
    - Code generation and refactoring
    """
    
    def __init__(self, 
                 llm_provider: str | None = None,
                 model: str | None = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CodingAgent.
        
        Args:
            llm_provider: LLM provider name (e.g., 'anthropic', 'openai')
            model: Model name to use (defaults to provider's default)
            config: Optional configuration dictionary
        """
        # Initialize base agent
        super().__init__('coding', llm_provider, model, config)
        
        # Set up coding-specific configuration
        self._setup_coding_config()
        
        # Register coding resources
        self._setup_coding_resources()
        
        # Register coding workflows
        self._setup_coding_workflows()
        
        # Initialize coding-specific state
        self._initialize_coding_state()
    
    def _setup_coding_config(self) -> None:
        """Set up coding-specific configuration."""
        coding_config = {
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'allowed_extensions': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.md', '.txt', '.json', '.yaml', '.yml'],
            'backup_enabled': True,
            'auto_save': True,
            'code_style': 'pep8',
            'testing_framework': 'pytest',
            'version_control': 'git',
            'linter_enabled': True,
            'formatter_enabled': True
        }
        
        # Merge with existing config
        self.config.update(coding_config)
    
    def _initialize_coding_state(self) -> None:
        """Initialize coding-specific state."""
        coding_state = {
            'current_project': None,
            'open_files': [],
            'recent_files': [],
            'git_status': {},
            'linter_errors': [],
            'test_results': {},
            'code_metrics': {},
            'dependencies': {},
            'environment': {
                'python_version': None,
                'node_version': None,
                'git_version': None
            }
        }
        
        self.update_state({'coding': coding_state})
    
    def _setup_coding_resources(self) -> None:
        """Register coding-specific resources."""
        # File System Resource
        self.register_resource('file_system', FileSystemResource(self.config))
        
        # Git Resource
        self.register_resource('git', GitResource(self.config))
        
        # Terminal Resource
        self.register_resource('terminal', TerminalResource(self.config))
        
        # Web Search Resource
        self.register_resource('web_search', WebSearchResource(self.config))
        
        # Code Analysis Resource
        self.register_resource('code_analysis', CodeAnalysisResource(self.config))
        
        # Package Manager Resource
        self.register_resource('package_manager', PackageManagerResource(self.config))
    
    def _setup_coding_workflows(self) -> None:
        """Register coding-specific workflows."""
        # Debug Code Workflow
        self.register_workflow('debug_code', DebugCodeWorkflow(self.config))
        
        # Refactor Code Workflow
        self.register_workflow('refactor_code', RefactorCodeWorkflow(self.config))
        
        # Add Feature Workflow
        self.register_workflow('add_feature', AddFeatureWorkflow(self.config))
        
        # Write Tests Workflow
        self.register_workflow('write_tests', WriteTestsWorkflow(self.config))
        
        # Setup Project Workflow
        self.register_workflow('setup_project', SetupProjectWorkflow(self.config))
        
        # Deploy Code Workflow
        self.register_workflow('deploy_code', DeployCodeWorkflow(self.config))
```

## Coding Resources

### File System Resource

```python
class FileSystemResource(Resource):
    """Resource for file system operations."""
    
    def __init__(self, config: Dict[str, Any]):
        methods = {
            'read_file': MethodInfo(
                name='read_file',
                docstring='Read contents of a file with line numbers and syntax highlighting',
                parameters={
                    'type': 'object',
                    'properties': {
                        'file_path': {'type': 'string', 'description': 'Absolute path to file'},
                        'offset': {'type': 'integer', 'description': 'Line offset to start reading'},
                        'limit': {'type': 'integer', 'description': 'Number of lines to read'},
                        'syntax_highlight': {'type': 'boolean', 'description': 'Enable syntax highlighting'}
                    },
                    'required': ['file_path']
                },
                handler=self._read_file
            ),
            'write_file': MethodInfo(
                name='write_file',
                docstring='Write content to a file with automatic backup',
                parameters={
                    'type': 'object',
                    'properties': {
                        'file_path': {'type': 'string', 'description': 'Absolute path to file'},
                        'content': {'type': 'string', 'description': 'Content to write'},
                        'create_backup': {'type': 'boolean', 'description': 'Create backup before writing'}
                    },
                    'required': ['file_path', 'content']
                },
                handler=self._write_file
            ),
            'list_directory': MethodInfo(
                name='list_directory',
                docstring='List contents of a directory with file metadata',
                parameters={
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'Directory path'},
                        'ignore_patterns': {'type': 'array', 'description': 'Patterns to ignore'},
                        'show_hidden': {'type': 'boolean', 'description': 'Show hidden files'},
                        'sort_by': {'type': 'string', 'enum': ['name', 'size', 'modified'], 'description': 'Sort order'}
                    },
                    'required': ['path']
                },
                handler=self._list_directory
            ),
            'search_files': MethodInfo(
                name='search_files',
                docstring='Search for files by name pattern',
                parameters={
                    'type': 'object',
                    'properties': {
                        'pattern': {'type': 'string', 'description': 'File name pattern'},
                        'directory': {'type': 'string', 'description': 'Directory to search in'},
                        'recursive': {'type': 'boolean', 'description': 'Search recursively'}
                    },
                    'required': ['pattern']
                },
                handler=self._search_files
            )
        }
        
        super().__init__('file_system', 'File system operations for code files', methods, config)
    
    def query(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file system operation."""
        if method not in self.methods:
            raise ValueError(f"Method '{method}' not found")
        
        method_info = self.methods[method]
        start_time = datetime.now()
        
        try:
            # Validate file path if provided
            if 'file_path' in params:
                self._validate_file_path(params['file_path'])
            
            # Update usage stats
            self.metadata['usage_stats'][method]['calls'] += 1
            
            # Execute method
            result = method_info.handler(params)
            
            # Update success stats
            self.metadata['usage_stats'][method]['successes'] += 1
            
            # Update performance metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(method, execution_time)
            
            return {
                'success': True,
                'result': result,
                'method': method,
                'execution_time': execution_time
            }
            
        except Exception as e:
            # Update error stats
            self.metadata['usage_stats'][method]['errors'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'method': method,
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
    
    def _read_file(self, params: Dict[str, Any]) -> str:
        """Read file with line numbers and optional syntax highlighting."""
        file_path = params['file_path']
        offset = params.get('offset')
        limit = params.get('limit')
        syntax_highlight = params.get('syntax_highlight', False)
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.config.get('max_file_size', 10 * 1024 * 1024):
            raise ValueError(f"File too large: {file_size} bytes")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Apply offset and limit
        if offset is not None:
            start = max(0, offset - 1)
            end = start + limit if limit else len(lines)
            lines = lines[start:end]
        
        # Format with line numbers
        result = []
        for i, line in enumerate(lines):
            line_num = (offset or 1) + i
            result.append(f"{line_num:6d}\t{line.rstrip()}")
        
        content = '\n'.join(result)
        
        # Apply syntax highlighting if requested
        if syntax_highlight:
            content = self._apply_syntax_highlighting(content, file_path)
        
        return content
    
    def _write_file(self, params: Dict[str, Any]) -> str:
        """Write file with optional backup."""
        file_path = params['file_path']
        content = params['content']
        create_backup = params.get('create_backup', True)
        
        # Create backup if requested and file exists
        if create_backup and os.path.exists(file_path):
            backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
        
        # Create directory if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully wrote to {file_path}"
    
    def _list_directory(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List directory with file metadata."""
        path = params['path']
        ignore_patterns = params.get('ignore_patterns', [])
        show_hidden = params.get('show_hidden', False)
        sort_by = params.get('sort_by', 'name')
        
        import fnmatch
        
        items = []
        for item in os.listdir(path):
            # Skip hidden files if not requested
            if not show_hidden and item.startswith('.'):
                continue
            
            # Check ignore patterns
            skip = False
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(item, pattern):
                    skip = True
                    break
            
            if skip:
                continue
            
            full_path = os.path.join(path, item)
            stat = os.stat(full_path)
            
            items.append({
                'name': item,
                'type': 'directory' if os.path.isdir(full_path) else 'file',
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:]
            })
        
        # Sort items
        if sort_by == 'name':
            items.sort(key=lambda x: x['name'])
        elif sort_by == 'size':
            items.sort(key=lambda x: x['size'], reverse=True)
        elif sort_by == 'modified':
            items.sort(key=lambda x: x['modified'], reverse=True)
        
        return items
    
    def _search_files(self, params: Dict[str, Any]) -> List[str]:
        """Search for files by name pattern."""
        pattern = params['pattern']
        directory = params.get('directory', '.')
        recursive = params.get('recursive', True)
        
        import glob
        
        if recursive:
            search_pattern = os.path.join(directory, '**', pattern)
        else:
            search_pattern = os.path.join(directory, pattern)
        
        matches = glob.glob(search_pattern, recursive=recursive)
        return [match for match in matches if os.path.isfile(match)]
    
    def _validate_file_path(self, file_path: str) -> None:
        """Validate file path for security."""
        # Check for path traversal
        if '..' in file_path or file_path.startswith('/'):
            raise ValueError("Invalid file path: path traversal not allowed")
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext and ext not in self.config.get('allowed_extensions', []):
            raise ValueError(f"File extension {ext} not allowed")
    
    def _apply_syntax_highlighting(self, content: str, file_path: str) -> str:
        """Apply basic syntax highlighting."""
        # This would implement syntax highlighting
        # For now, return content as-is
        return content
```

### Git Resource

```python
class GitResource(Resource):
    """Resource for Git version control operations."""
    
    def __init__(self, config: Dict[str, Any]):
        methods = {
            'status': MethodInfo(
                name='status',
                docstring='Get Git repository status',
                parameters={
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'Repository path'}
                    },
                    'required': ['path']
                },
                handler=self._git_status
            ),
            'commit': MethodInfo(
                name='commit',
                docstring='Create a Git commit',
                parameters={
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'Repository path'},
                        'message': {'type': 'string', 'description': 'Commit message'},
                        'files': {'type': 'array', 'description': 'Files to commit'},
                        'all': {'type': 'boolean', 'description': 'Commit all changes'}
                    },
                    'required': ['path', 'message']
                },
                handler=self._git_commit
            ),
            'log': MethodInfo(
                name='log',
                docstring='Get Git commit log',
                parameters={
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'Repository path'},
                        'limit': {'type': 'integer', 'description': 'Number of commits to show'},
                        'oneline': {'type': 'boolean', 'description': 'Show one line per commit'}
                    },
                    'required': ['path']
                },
                handler=self._git_log
            ),
            'diff': MethodInfo(
                name='diff',
                docstring='Get Git diff',
                parameters={
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'Repository path'},
                        'cached': {'type': 'boolean', 'description': 'Show staged changes'},
                        'file': {'type': 'string', 'description': 'Specific file to diff'}
                    },
                    'required': ['path']
                },
                handler=self._git_diff
            )
        }
        
        super().__init__('git', 'Git version control operations', methods, config)
    
    def query(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Git operation."""
        if method not in self.methods:
            raise ValueError(f"Method '{method}' not found")
        
        method_info = self.methods[method]
        start_time = datetime.now()
        
        try:
            # Update usage stats
            self.metadata['usage_stats'][method]['calls'] += 1
            
            # Execute method
            result = method_info.handler(params)
            
            # Update success stats
            self.metadata['usage_stats'][method]['successes'] += 1
            
            # Update performance metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(method, execution_time)
            
            return {
                'success': True,
                'result': result,
                'method': method,
                'execution_time': execution_time
            }
            
        except Exception as e:
            # Update error stats
            self.metadata['usage_stats'][method]['errors'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'method': method,
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
    
    def _git_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Git status."""
        path = params['path']
        
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Git status failed: {result.stderr}")
        
        # Parse status output
        status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        status = {
            'clean': len(status_lines) == 0,
            'staged': [],
            'modified': [],
            'untracked': []
        }
        
        for line in status_lines:
            if line.startswith('M '):
                status['staged'].append(line[3:])
            elif line.startswith(' M'):
                status['modified'].append(line[3:])
            elif line.startswith('??'):
                status['untracked'].append(line[3:])
        
        return status
    
    def _git_commit(self, params: Dict[str, Any]) -> str:
        """Create Git commit."""
        path = params['path']
        message = params['message']
        files = params.get('files', [])
        all_files = params.get('all', False)
        
        # Add files if specified
        if all_files:
            subprocess.run(['git', 'add', '.'], cwd=path, check=True)
        elif files:
            for file in files:
                subprocess.run(['git', 'add', file], cwd=path, check=True)
        
        # Create commit
        result = subprocess.run(
            ['git', 'commit', '-m', message],
            cwd=path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Git commit failed: {result.stderr}")
        
        return f"Commit created: {message}"
    
    def _git_log(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get Git commit log."""
        path = params['path']
        limit = params.get('limit', 10)
        oneline = params.get('oneline', False)
        
        cmd = ['git', 'log', f'--max-count={limit}']
        if oneline:
            cmd.append('--oneline')
        
        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Git log failed: {result.stderr}")
        
        # Parse log output
        commits = []
        if oneline:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(' ', 1)
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1] if len(parts) > 1 else ''
                    })
        else:
            # Parse full log format
            # This would implement full log parsing
            pass
        
        return commits
    
    def _git_diff(self, params: Dict[str, Any]) -> str:
        """Get Git diff."""
        path = params['path']
        cached = params.get('cached', False)
        file = params.get('file')
        
        cmd = ['git', 'diff']
        if cached:
            cmd.append('--cached')
        if file:
            cmd.append(file)
        
        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Git diff failed: {result.stderr}")
        
        return result.stdout
```

### Terminal Resource

```python
class TerminalResource(Resource):
    """Resource for terminal command execution."""
    
    def __init__(self, config: Dict[str, Any]):
        methods = {
            'execute': MethodInfo(
                name='execute',
                docstring='Execute terminal command',
                parameters={
                    'type': 'object',
                    'properties': {
                        'command': {'type': 'string', 'description': 'Command to execute'},
                        'working_dir': {'type': 'string', 'description': 'Working directory'},
                        'timeout': {'type': 'integer', 'description': 'Timeout in seconds'},
                        'shell': {'type': 'boolean', 'description': 'Use shell execution'}
                    },
                    'required': ['command']
                },
                handler=self._execute_command
            ),
            'run_script': MethodInfo(
                name='run_script',
                docstring='Run a script file',
                parameters={
                    'type': 'object',
                    'properties': {
                        'script_path': {'type': 'string', 'description': 'Path to script'},
                        'args': {'type': 'array', 'description': 'Script arguments'},
                        'working_dir': {'type': 'string', 'description': 'Working directory'}
                    },
                    'required': ['script_path']
                },
                handler=self._run_script
            )
        }
        
        super().__init__('terminal', 'Terminal command execution', methods, config)
    
    def query(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute terminal operation."""
        if method not in self.methods:
            raise ValueError(f"Method '{method}' not found")
        
        method_info = self.methods[method]
        start_time = datetime.now()
        
        try:
            # Update usage stats
            self.metadata['usage_stats'][method]['calls'] += 1
            
            # Execute method
            result = method_info.handler(params)
            
            # Update success stats
            self.metadata['usage_stats'][method]['successes'] += 1
            
            # Update performance metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(method, execution_time)
            
            return {
                'success': True,
                'result': result,
                'method': method,
                'execution_time': execution_time
            }
            
        except Exception as e:
            # Update error stats
            self.metadata['usage_stats'][method]['errors'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'method': method,
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
    
    def _execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute terminal command."""
        command = params['command']
        working_dir = params.get('working_dir', '.')
        timeout = params.get('timeout', 30)
        shell = params.get('shell', True)
        
        # Validate command for security
        self._validate_command(command)
        
        try:
            result = subprocess.run(
                command,
                shell=shell,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'command': command
            }
            
        except subprocess.TimeoutExpired:
            raise Exception(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")
    
    def _run_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a script file."""
        script_path = params['script_path']
        args = params.get('args', [])
        working_dir = params.get('working_dir', '.')
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        # Run script
        cmd = [script_path] + args
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True
        )
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'script': script_path
        }
    
    def _validate_command(self, command: str) -> None:
        """Validate command for security."""
        # List of dangerous commands to block
        dangerous_commands = [
            'rm -rf /',
            'format',
            'del /s',
            'shutdown',
            'reboot',
            'halt'
        ]
        
        for dangerous in dangerous_commands:
            if dangerous in command.lower():
                raise ValueError(f"Dangerous command blocked: {dangerous}")
```

## Coding Workflows

### Debug Code Workflow

```python
class DebugCodeWorkflow(Workflow):
    """Workflow for debugging code issues."""
    
    def __init__(self, config: Dict[str, Any]):
        steps = [
            WorkflowStep(
                name='analyze_error',
                function=analyze_error_message,
                input_mapping={'error_message': 'error_message', 'code': 'code'},
                output_mapping={'error_type': 'error_type', 'suggestions': 'suggestions'}
            ),
            WorkflowStep(
                name='search_solutions',
                function=search_error_solutions,
                input_mapping={'error_type': 'error_type', 'language': 'language'},
                output_mapping={'solutions': 'solutions'}
            ),
            WorkflowStep(
                name='test_fix',
                function=test_code_fix,
                input_mapping={'code': 'code', 'suggestions': 'suggestions'},
                output_mapping={'fixed_code': 'fixed_code', 'test_results': 'test_results'}
            )
        ]
        
        super().__init__(
            name='debug_code',
            description='Debug code by analyzing errors and applying fixes',
            steps=steps,
            config=config
        )

def analyze_error_message(error_message: str, code: str) -> Dict[str, Any]:
    """Analyze error message to determine error type and suggestions."""
    # This would use NLP or pattern matching
    error_type = 'syntax_error'
    suggestions = []
    
    if 'SyntaxError' in error_message:
        error_type = 'syntax_error'
        suggestions = ['Check indentation', 'Verify parentheses', 'Check quotes']
    elif 'NameError' in error_message:
        error_type = 'name_error'
        suggestions = ['Check variable names', 'Verify imports', 'Check scope']
    elif 'TypeError' in error_message:
        error_type = 'type_error'
        suggestions = ['Check data types', 'Verify function arguments', 'Check return types']
    
    return {
        'error_type': error_type,
        'suggestions': suggestions
    }

def search_error_solutions(error_type: str, language: str) -> List[Dict[str, Any]]:
    """Search for solutions to the error type."""
    # This would search documentation or knowledge base
    solutions = []
    
    if error_type == 'syntax_error':
        solutions = [
            {'solution': 'Check indentation', 'confidence': 0.9},
            {'solution': 'Verify parentheses', 'confidence': 0.8}
        ]
    elif error_type == 'name_error':
        solutions = [
            {'solution': 'Check variable names', 'confidence': 0.9},
            {'solution': 'Verify imports', 'confidence': 0.7}
        ]
    
    return solutions

def test_code_fix(code: str, suggestions: List[str]) -> Dict[str, Any]:
    """Test the code fix and return results."""
    # This would execute the code and check for errors
    return {
        'fixed_code': code,  # Modified code
        'test_results': {'passed': True, 'errors': []}
    }
```

### Add Feature Workflow

```python
class AddFeatureWorkflow(Workflow):
    """Workflow for adding new features to code."""
    
    def __init__(self, config: Dict[str, Any]):
        steps = [
            WorkflowStep(
                name='analyze_requirements',
                function=analyze_feature_requirements,
                input_mapping={'feature_description': 'feature_description', 'codebase': 'codebase'},
                output_mapping={'requirements': 'requirements', 'impact_analysis': 'impact_analysis'}
            ),
            WorkflowStep(
                name='design_implementation',
                function=design_feature_implementation,
                input_mapping={'requirements': 'requirements', 'codebase': 'codebase'},
                output_mapping={'design': 'design', 'files_to_modify': 'files_to_modify'}
            ),
            WorkflowStep(
                name='implement_feature',
                function=implement_feature,
                input_mapping={'design': 'design', 'files_to_modify': 'files_to_modify'},
                output_mapping={'implementation': 'implementation', 'new_files': 'new_files'}
            ),
            WorkflowStep(
                name='test_feature',
                function=test_feature_implementation,
                input_mapping={'implementation': 'implementation', 'requirements': 'requirements'},
                output_mapping={'test_results': 'test_results', 'coverage': 'coverage'}
            )
        ]
        
        super().__init__(
            name='add_feature',
            description='Add new feature to existing codebase',
            steps=steps,
            config=config
        )

def analyze_feature_requirements(feature_description: str, codebase: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze feature requirements and impact."""
    return {
        'requirements': ['Requirement 1', 'Requirement 2'],
        'impact_analysis': 'Low impact on existing code'
    }

def design_feature_implementation(requirements: List[str], codebase: Dict[str, Any]) -> Dict[str, Any]:
    """Design the feature implementation."""
    return {
        'design': 'Feature design details',
        'files_to_modify': ['file1.py', 'file2.py']
    }

def implement_feature(design: str, files_to_modify: List[str]) -> Dict[str, Any]:
    """Implement the feature."""
    return {
        'implementation': 'Feature implementation',
        'new_files': ['new_feature.py']
    }

def test_feature_implementation(implementation: str, requirements: List[str]) -> Dict[str, Any]:
    """Test the feature implementation."""
    return {
        'test_results': {'passed': True, 'failed': 0},
        'coverage': 0.95
    }
```

## Usage Examples

```python
# Create a CodingAgent
from adana.core.agent import CodingAgent

coding_agent = CodingAgent(llm_provider='anthropic', model='claude-3-sonnet')

# Use the agent
response = await coding_agent.chat("Debug this Python code: print('Hello World'")

# The agent will:
# 1. Analyze the code
# 2. Identify any issues
# 3. Use appropriate resources and workflows
# 4. Provide debugging assistance

# Example workflow execution
result = coding_agent.execute_workflow('debug_code', {
    'error_message': 'SyntaxError: invalid syntax',
    'code': 'print("Hello World"',
    'language': 'python'
})

# Example resource usage
file_content = coding_agent.query_resource('file_system', 'read_file', {
    'file_path': '/path/to/file.py',
    'syntax_highlight': True
})
```

## Configuration

```python
# CodingAgent Configuration
coding_config = {
    'max_file_size': 10 * 1024 * 1024,
    'allowed_extensions': ['.py', '.js', '.ts', '.java', '.cpp'],
    'backup_enabled': True,
    'auto_save': True,
    'code_style': 'pep8',
    'testing_framework': 'pytest',
    'linter_enabled': True,
    'formatter_enabled': True,
    'git_integration': True,
    'web_search_enabled': True
}
```
