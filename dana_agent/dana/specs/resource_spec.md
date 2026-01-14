# Resource Abstraction Specification

## Overview

Resources are higher-level capabilities that provide access to external systems, data sources, and services. They are the primary interface through which agents interact with the outside world, including web access, databases, RAG systems, IoT devices, and more.

## Core Resource Class

```python
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
import json
import asyncio
from abc import ABC, abstractmethod

class Resource(ABC):
    """
    Abstract base class for all resources.
    
    Resources provide capabilities to agents through a standardized interface
    with adaptive metadata and multiple query methods.
    """
    
    def __init__(self, 
                 name: str, 
                 description: str, 
                 methods: Dict[str, 'MethodInfo'],
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the resource.
        
        Args:
            name: Unique name for the resource
            description: Human-readable description of the resource
            methods: Dictionary of available methods
            config: Optional configuration dictionary
        """
        self.name = name
        self.description = description
        self.methods = methods
        self.config = config or {}
        
        # Adaptive metadata system
        self.metadata = {
            'adaptive_docstrings': {method: info.docstring for method, info in methods.items()},
            'usage_stats': {method: {'calls': 0, 'successes': 0, 'errors': 0} for method in methods},
            'performance_metrics': {method: {'avg_time': 0, 'last_time': 0} for method in methods},
            'feedback_history': [],
            'learning_data': {},
            'capability_discoveries': []
        }
        
        # Resource state
        self.state = {
            'initialized': True,
            'last_activity': datetime.now().isoformat(),
            'connection_status': 'unknown',
            'rate_limits': {},
            'quotas': {}
        }
    
    @abstractmethod
    def query(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Primary query method - delegates to specific method.
        
        Args:
            method: Name of the method to call
            params: Parameters for the method
        
        Returns:
            Method execution result
        """
        pass
    
    def get_method_docstring(self, method: str) -> str:
        """Get adaptive docstring for method."""
        if method not in self.methods:
            raise ValueError(f"Method '{method}' not found")
        
        return self.metadata['adaptive_docstrings'].get(method, self.methods[method].docstring)
    
    def update_metadata(self, feedback: Dict[str, Any]) -> None:
        """Update adaptive metadata based on feedback."""
        self.metadata['feedback_history'].append({
            'timestamp': datetime.now().isoformat(),
            'feedback': feedback
        })
        
        # Process feedback for learning
        self._process_feedback(feedback)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get current resource capabilities."""
        return {
            'name': self.name,
            'description': self.description,
            'methods': list(self.methods.keys()),
            'metadata': self.metadata,
            'state': self.state
        }
```

## Method Information Class

```python
class MethodInfo:
    """Information about a resource method."""
    
    def __init__(self, 
                 name: str, 
                 docstring: str, 
                 parameters: Dict[str, Any], 
                 handler: Callable,
                 return_type: str = 'dict',
                 is_async: bool = False,
                 rate_limit: Optional[int] = None):
        """
        Initialize method information.
        
        Args:
            name: Method name
            docstring: Method description
            parameters: Parameter schema
            handler: Method implementation
            return_type: Expected return type
            is_async: Whether method is asynchronous
            rate_limit: Optional rate limit (calls per minute)
        """
        self.name = name
        self.docstring = docstring
        self.parameters = parameters
        self.handler = handler
        self.return_type = return_type
        self.is_async = is_async
        self.rate_limit = rate_limit
        self.last_called = None
        self.call_count = 0
```

## Concrete Resource Implementations

### File System Resource

```python
class FileSystemResource(Resource):
    """Resource for file system operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        methods = {
            'read_file': MethodInfo(
                name='read_file',
                docstring='Read contents of a file',
                parameters={
                    'type': 'object',
                    'properties': {
                        'file_path': {'type': 'string', 'description': 'Path to file'},
                        'offset': {'type': 'integer', 'description': 'Line offset'},
                        'limit': {'type': 'integer', 'description': 'Number of lines'}
                    },
                    'required': ['file_path']
                },
                handler=self._read_file
            ),
            'write_file': MethodInfo(
                name='write_file',
                docstring='Write content to a file',
                parameters={
                    'type': 'object',
                    'properties': {
                        'file_path': {'type': 'string', 'description': 'Path to file'},
                        'content': {'type': 'string', 'description': 'Content to write'}
                    },
                    'required': ['file_path', 'content']
                },
                handler=self._write_file
            ),
            'list_directory': MethodInfo(
                name='list_directory',
                docstring='List contents of a directory',
                parameters={
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'Directory path'},
                        'ignore_patterns': {'type': 'array', 'description': 'Patterns to ignore'}
                    },
                    'required': ['path']
                },
                handler=self._list_directory
            )
        }
        
        super().__init__('file_system', 'File system operations', methods, config)
    
    def query(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file system operation."""
        if method not in self.methods:
            raise ValueError(f"Method '{method}' not found")
        
        method_info = self.methods[method]
        start_time = datetime.now()
        
        try:
            # Update usage stats
            self.metadata['usage_stats'][method]['calls'] += 1
            
            # Execute method
            if method_info.is_async:
                result = asyncio.run(method_info.handler(params))
            else:
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
        """Read file implementation."""
        file_path = params['file_path']
        offset = params.get('offset')
        limit = params.get('limit')
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if offset is not None:
            start = offset - 1
            end = start + limit if limit else len(lines)
            lines = lines[start:end]
        
        return ''.join(lines)
    
    def _write_file(self, params: Dict[str, Any]) -> str:
        """Write file implementation."""
        file_path = params['file_path']
        content = params['content']
        
        # Create directory if needed
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        return f"Successfully wrote to {file_path}"
    
    def _list_directory(self, params: Dict[str, Any]) -> List[str]:
        """List directory implementation."""
        path = params['path']
        ignore_patterns = params.get('ignore_patterns', [])
        
        import os
        import fnmatch
        
        items = []
        for item in os.listdir(path):
            # Check ignore patterns
            skip = False
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(item, pattern):
                    skip = True
                    break
            
            if not skip:
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    items.append(f"{item}/")
                else:
                    items.append(item)
        
        return items
```

### Web Search Resource

```python
class WebSearchResource(Resource):
    """Resource for web search operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        methods = {
            'search': MethodInfo(
                name='search',
                docstring='Search the web for information',
                parameters={
                    'type': 'object',
                    'properties': {
                        'query': {'type': 'string', 'description': 'Search query'},
                        'num_results': {'type': 'integer', 'description': 'Number of results'},
                        'language': {'type': 'string', 'description': 'Search language'},
                        'region': {'type': 'string', 'description': 'Search region'}
                    },
                    'required': ['query']
                },
                handler=self._search_web
            ),
            'get_page_content': MethodInfo(
                name='get_page_content',
                docstring='Get content from a specific URL',
                parameters={
                    'type': 'object',
                    'properties': {
                        'url': {'type': 'string', 'description': 'URL to fetch'},
                        'timeout': {'type': 'integer', 'description': 'Request timeout'}
                    },
                    'required': ['url']
                },
                handler=self._get_page_content
            )
        }
        
        super().__init__('web_search', 'Web search and content retrieval', methods, config)
        self.api_key = config.get('api_key') if config else None
    
    def query(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web search operation."""
        if method not in self.methods:
            raise ValueError(f"Method '{method}' not found")
        
        method_info = self.methods[method]
        start_time = datetime.now()
        
        try:
            # Check rate limits
            if not self._check_rate_limit(method):
                raise Exception("Rate limit exceeded")
            
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
    
    def _search_web(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Web search implementation."""
        query = params['query']
        num_results = params.get('num_results', 10)
        
        # This would integrate with actual search API
        # For now, return mock results
        return [
            {
                'title': f"Search result for: {query}",
                'url': f"https://example.com/search?q={query}",
                'snippet': f"This is a search result for the query: {query}",
                'rank': i + 1
            }
            for i in range(min(num_results, 5))
        ]
    
    def _get_page_content(self, params: Dict[str, Any]) -> str:
        """Get page content implementation."""
        url = params['url']
        timeout = params.get('timeout', 30)
        
        # This would use requests or similar
        # For now, return mock content
        return f"Content from {url} (mock implementation)"
```

### Database Resource

```python
class DatabaseResource(Resource):
    """Resource for database operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        methods = {
            'query': MethodInfo(
                name='query',
                docstring='Execute SQL query',
                parameters={
                    'type': 'object',
                    'properties': {
                        'sql': {'type': 'string', 'description': 'SQL query'},
                        'params': {'type': 'array', 'description': 'Query parameters'}
                    },
                    'required': ['sql']
                },
                handler=self._execute_query
            ),
            'get_schema': MethodInfo(
                name='get_schema',
                docstring='Get database schema information',
                parameters={
                    'type': 'object',
                    'properties': {
                        'table': {'type': 'string', 'description': 'Table name (optional)'}
                    }
                },
                handler=self._get_schema
            )
        }
        
        super().__init__('database', 'Database operations', methods, config)
        self.connection_string = config.get('connection_string') if config else None
    
    def query(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database operation."""
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
    
    def _execute_query(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute SQL query implementation."""
        sql = params['sql']
        query_params = params.get('params', [])
        
        # This would use actual database connection
        # For now, return mock results
        return [
            {'id': 1, 'name': 'Example', 'value': 100},
            {'id': 2, 'name': 'Test', 'value': 200}
        ]
    
    def _get_schema(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get schema implementation."""
        table = params.get('table')
        
        # This would query actual database schema
        # For now, return mock schema
        return {
            'tables': ['users', 'orders', 'products'],
            'columns': {
                'users': ['id', 'name', 'email'],
                'orders': ['id', 'user_id', 'total'],
                'products': ['id', 'name', 'price']
            }
        }
```

## Adaptive Learning System

```python
class ResourceMetadataAdapter:
    """Handles adaptive learning for resource metadata."""
    
    def __init__(self, resource: Resource):
        self.resource = resource
        self.learning_models = {}
        self.feedback_processor = FeedbackProcessor()
    
    def adapt_docstrings(self, usage_feedback: Dict[str, Any]) -> None:
        """Adapt resource docstrings based on usage feedback."""
        for method, feedback in usage_feedback.items():
            if method in self.resource.metadata['adaptive_docstrings']:
                # Process feedback to improve docstring
                improved_docstring = self._improve_docstring(
                    self.resource.metadata['adaptive_docstrings'][method],
                    feedback
                )
                self.resource.metadata['adaptive_docstrings'][method] = improved_docstring
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> None:
        """Optimize resource parameters based on performance data."""
        for method, data in performance_data.items():
            if method in self.resource.methods:
                # Analyze performance patterns
                optimization = self._analyze_performance(data)
                
                # Apply optimizations
                if 'rate_limit' in optimization:
                    self.resource.methods[method].rate_limit = optimization['rate_limit']
    
    def discover_capabilities(self, usage_patterns: Dict[str, Any]) -> List[str]:
        """Discover new capabilities based on usage patterns."""
        discovered = []
        
        # Analyze usage patterns to find potential new methods
        for pattern, frequency in usage_patterns.items():
            if frequency > 0.8 and pattern not in self.resource.methods:
                discovered.append(pattern)
        
        return discovered
    
    def _improve_docstring(self, current_docstring: str, feedback: Dict[str, Any]) -> str:
        """Improve docstring based on feedback."""
        # This would use NLP to improve docstrings
        # For now, return enhanced version
        improvements = feedback.get('improvements', [])
        
        if improvements:
            enhanced = current_docstring
            for improvement in improvements:
                enhanced += f"\n\nNote: {improvement}"
            return enhanced
        
        return current_docstring
    
    def _analyze_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance data for optimizations."""
        avg_time = data.get('avg_time', 0)
        error_rate = data.get('error_rate', 0)
        
        optimizations = {}
        
        if avg_time > 5.0:  # If average time > 5 seconds
            optimizations['rate_limit'] = max(1, int(60 / avg_time))  # Adjust rate limit
        
        if error_rate > 0.1:  # If error rate > 10%
            optimizations['retry_count'] = 3  # Add retry logic
        
        return optimizations

class FeedbackProcessor:
    """Processes feedback for resource learning."""
    
    def process_usage_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Process usage feedback into actionable insights."""
        processed = {
            'improvements': [],
            'optimizations': {},
            'discoveries': []
        }
        
        # Extract improvement suggestions
        if 'suggestions' in feedback:
            processed['improvements'].extend(feedback['suggestions'])
        
        # Extract performance issues
        if 'performance' in feedback:
            processed['optimizations'].update(feedback['performance'])
        
        # Extract capability discoveries
        if 'discoveries' in feedback:
            processed['discoveries'].extend(feedback['discoveries'])
        
        return processed
```

## Resource Registry

```python
class ResourceRegistry:
    """Registry for managing resources."""
    
    def __init__(self):
        self.resources: Dict[str, Resource] = {}
        self.adapters: Dict[str, ResourceMetadataAdapter] = {}
    
    def register(self, resource: Resource) -> None:
        """Register a resource."""
        self.resources[resource.name] = resource
        self.adapters[resource.name] = ResourceMetadataAdapter(resource)
    
    def get(self, name: str) -> Optional[Resource]:
        """Get a resource by name."""
        return self.resources.get(name)
    
    def list_resources(self) -> List[str]:
        """List all registered resource names."""
        return list(self.resources.keys())
    
    def update_learning(self, resource_name: str, feedback: Dict[str, Any]) -> None:
        """Update learning for a specific resource."""
        if resource_name in self.adapters:
            self.adapters[resource_name].adapt_docstrings(feedback)
            self.adapters[resource_name].optimize_parameters(feedback)
```

## Error Handling

```python
class ResourceError(Exception):
    """Base exception for resource errors."""
    pass

class MethodNotFoundError(ResourceError):
    """Exception raised when method not found."""
    pass

class ParameterValidationError(ResourceError):
    """Exception raised when parameters are invalid."""
    pass

class RateLimitExceededError(ResourceError):
    """Exception raised when rate limit exceeded."""
    pass

class ResourceConnectionError(ResourceError):
    """Exception raised when resource connection fails."""
    pass
```

## Configuration Examples

```python
# File System Resource Configuration
file_system_config = {
    'base_path': '/home/user/projects',
    'allowed_extensions': ['.py', '.js', '.md', '.txt'],
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_enabled': True
}

# Web Search Resource Configuration
web_search_config = {
    'api_key': 'your_api_key',
    'search_engine': 'google',
    'rate_limit': 100,  # requests per minute
    'timeout': 30,
    'user_agent': 'Agent/1.0'
}

# Database Resource Configuration
database_config = {
    'connection_string': 'postgresql://user:pass@localhost/db',
    'pool_size': 10,
    'max_overflow': 20,
    'timeout': 30,
    'retry_count': 3
}
```
<promise>TASK COMPLETE</promise>
