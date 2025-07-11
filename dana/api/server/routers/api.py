from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import db, schemas, services
from ..schemas import RunNAFileRequest, RunNAFileResponse, AgentGenerationRequest, AgentGenerationResponse, DanaSyntaxCheckRequest, DanaSyntaxCheckResponse, CodeValidationRequest, CodeValidationResponse, CodeFixRequest, CodeFixResponse
from ..services import run_na_file_service
from ..agent_generator import generate_agent_code_from_messages
from dana.core.lang.dana_sandbox import DanaSandbox

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("/", response_model=list[schemas.AgentRead])
def list_agents(skip: int = 0, limit: int = 10, db: Session = Depends(db.get_db)):
    return services.get_agents(db, skip=skip, limit=limit)


@router.get("/{agent_id}", response_model=schemas.AgentRead)
def get_agent(agent_id: int, db: Session = Depends(db.get_db)):
    agent = services.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/", response_model=schemas.AgentRead)
def create_agent(agent: schemas.AgentCreate, db: Session = Depends(db.get_db)):
    return services.create_agent(db, agent)


@router.post("/run-na-file", response_model=RunNAFileResponse)
def run_na_file(request: RunNAFileRequest):
    return run_na_file_service(request)


@router.post("/generate", response_model=AgentGenerationResponse)
async def generate_agent(request: AgentGenerationRequest):
    """
    Generate Dana agent code from user conversation messages.
    
    This endpoint takes a list of conversation messages and generates
    appropriate Dana code for creating an agent based on the user's requirements.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Received agent generation request with {len(request.messages)} messages")
        
        # Convert Pydantic models to dictionaries
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        logger.info(f"Converted messages: {messages}")
        
        # Generate Dana code
        logger.info("Calling generate_agent_code_from_messages...")
        dana_code, syntax_error = await generate_agent_code_from_messages(messages, request.current_code or "")
        logger.info(f"Generated Dana code length: {len(dana_code)}")
        logger.debug(f"Generated Dana code: {dana_code[:500]}...")
        
        # Extract agent name and description from the generated code
        agent_name = None
        agent_description = None
        
        lines = dana_code.split('\n')
        for i, line in enumerate(lines):
            # Look for agent keyword syntax: agent AgentName:
            if line.strip().startswith('agent ') and line.strip().endswith(':'):
                # Next few lines should contain name and description
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if 'name : str =' in next_line:
                        agent_name = next_line.split('=')[1].strip().strip('"')
                        logger.info(f"Extracted agent name: {agent_name}")
                    elif 'description : str =' in next_line:
                        agent_description = next_line.split('=')[1].strip().strip('"')
                        logger.info(f"Extracted agent description: {agent_description}")
                    elif next_line.startswith('#'):  # Skip comments
                        continue
                    elif next_line == '':  # Skip empty lines
                        continue
                    elif not next_line.startswith('    '):  # Stop at non-indented lines
                        break
                break
            # Fallback: also check for old system: syntax
            elif 'system:agent_name' in line:
                agent_name = line.split('=')[1].strip().strip('"')
                logger.info(f"Extracted agent name (old format): {agent_name}")
            elif 'system:agent_description' in line:
                agent_description = line.split('=')[1].strip().strip('"')
                logger.info(f"Extracted agent description (old format): {agent_description}")
        
        response = AgentGenerationResponse(
            success=(syntax_error is None),
            dana_code=dana_code,
            agent_name=agent_name,
            agent_description=agent_description,
            error=syntax_error
        )
        
        logger.info(f"Returning response with success={response.success}, code_length={len(response.dana_code)}")
        return response
        
    except Exception as e:
        logger.error(f"Error in generate_agent endpoint: {e}", exc_info=True)
        return AgentGenerationResponse(
            success=False,
            dana_code="",
            error=f"Failed to generate agent code: {str(e)}"
        )

@router.post("/syntax-check", response_model=DanaSyntaxCheckResponse)
def syntax_check(request: DanaSyntaxCheckRequest):
    """
    Check the syntax of Dana code using DanaSandbox.eval.
    Returns success status and error message if any.
    """
    try:
        result = DanaSandbox.quick_eval(request.dana_code)
        if result.success:
            return DanaSyntaxCheckResponse(success=True, output=result.output)
        else:
            return DanaSyntaxCheckResponse(success=False, error=str(result.error), output=result.output)
    except Exception as e:
        return DanaSyntaxCheckResponse(success=False, error=str(e))


@router.post("/validate", response_model=CodeValidationResponse)
async def validate_code(request: CodeValidationRequest):
    """
    Validate Dana agent code and provide detailed feedback.
    Returns validation status, errors, warnings, and suggestions.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Validating code for agent: {request.agent_name}")
        print(request.code)
        print("--------------------------------")
        
        # Basic syntax validation
        syntax_result = DanaSandbox.quick_eval(request.code)

        print("--------------------------------")
        print(syntax_result)

        print("--------------------------------")
        
        errors = []
        warnings = []
        suggestions = []

        print("--------------------------------")
        print(syntax_result.success)
        print("--------------------------------")
        
        if not syntax_result.success:
            # Just return the raw error text
            error_text = str(syntax_result.error)
            errors.append({
                "line": 1,
                "column": 1,
                "message": error_text,
                "severity": "error",
                "code": error_text
            })
        
        # Check for common issues and provide suggestions
        lines = request.code.split('\n')
        for i, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # Check for missing agent definition
            if i == 1 and not stripped_line.startswith('agent ') and not stripped_line.startswith('system:'):
                suggestions.append({
                    "type": "syntax",
                    "message": "Consider adding an agent definition",
                    "code": "agent MyAgent:\n    name: str = \"My Agent\"\n    description: str = \"A custom agent\"",
                    "description": "Add a proper agent definition at the beginning of your code"
                })
            
            # Check for missing solve function
            if 'def solve(' in stripped_line:
                break
        else:
            suggestions.append({
                "type": "best_practice",
                "message": "Consider adding a solve function",
                "code": "def solve(query: str) -> str:\n    return reason(f\"Process query: {query}\")",
                "description": "Add a solve function to make your agent functional"
            })
        
        # Check for proper imports
        if 'reason(' in request.code and 'import' not in request.code:
            suggestions.append({
                "type": "syntax",
                "message": "Consider importing required modules",
                "code": "# Add imports if needed\n# import some_module",
                "description": "Make sure all required modules are imported"
            })
        
        is_valid = len(errors) == 0
        print(f"Validation result: is_valid={is_valid}, errors={len(errors)}")
        
        return CodeValidationResponse(
            success=True,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error in validate_code endpoint: {e}", exc_info=True)
        return CodeValidationResponse(
            success=False,
            is_valid=False,
            errors=[{
                "line": 1,
                "column": 1,
                "message": f"Validation failed: {str(e)}",
                "severity": "error",
                "code": ""
            }],
            warnings=[],
            suggestions=[]
        )


@router.post("/fix", response_model=CodeFixResponse)
async def fix_code(request: CodeFixRequest):
    """
    Automatically fix Dana code issues using iterative LLM approach.
    Returns fixed code and list of applied fixes.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Fixing code for agent: {request.agent_name}")
        
        # Prepare initial error messages
        error_messages = "\n".join([f"- {error.message}" for error in request.errors])
        
        # Iterative fix with feedback
        max_attempts = 4
        current_code = request.code
        applied_fixes = []
        attempt_history = []
        
        for attempt in range(max_attempts):
            logger.info(f"LLM fix attempt {attempt + 1}/{max_attempts}")
            
            # Build prompt with attempt history
            prompt = _build_iterative_prompt(
                original_code=request.code,
                current_code=current_code,
                error_messages=error_messages,
                attempt_history=attempt_history,
                attempt_number=attempt + 1,
                max_attempts=max_attempts
            )
            
            # Use LLM to fix the code
            try:
                from dana.common.resource.llm.llm_resource import LLMResource
                from dana.common.resource.llm.llm_configuration_manager import LLMConfigurationManager
                from dana.common.types import BaseRequest
                
                # Initialize LLM resource
                llm_config = LLMConfigurationManager().get_model_config()
                llm_resource = LLMResource(
                    name="code_fix_llm",
                    description="LLM for fixing Dana code errors",
                    config=llm_config
                )
                
                # Create request for LLM
                request_data = BaseRequest(
                    arguments={
                        "messages": [{"role": "user", "content": prompt}],
                        "system_messages": [
                            "You are an expert Dana programming language developer.",
                            "Your task is to fix syntax errors in Dana code iteratively.",
                            "Return ONLY the corrected code, no explanations or markdown formatting.",
                            "Learn from previous attempts and feedback to improve your fixes."
                        ]
                    }
                )
                
                # Get LLM response
                response = await llm_resource.query(request_data)
                
                if response.success and response.content:
                    # Extract the fixed code from response
                    fixed_code = _extract_code_from_response(response.content)
                    
                    if fixed_code and fixed_code.strip():
                        # Validate the fixed code
                        syntax_result = DanaSandbox.quick_eval(fixed_code)
                        
                        if syntax_result.success:
                            # Success! Code is valid
                            applied_fixes.append(f"LLM applied intelligent fixes (attempt {attempt + 1})")
                            return CodeFixResponse(
                                success=True,
                                fixed_code=fixed_code,
                                applied_fixes=applied_fixes,
                                remaining_errors=[]
                            )
                        else:
                            # Still has errors, add to history for next attempt
                            attempt_history.append({
                                "attempt": attempt + 1,
                                "code": fixed_code,
                                "errors": str(syntax_result.error),
                                "feedback": f"Attempt {attempt + 1} still has errors: {syntax_result.error}"
                            })
                            current_code = fixed_code
                            logger.info(f"Attempt {attempt + 1} failed, trying again with feedback")
                    else:
                        # Empty response, add to history
                        attempt_history.append({
                            "attempt": attempt + 1,
                            "code": current_code,
                            "errors": "LLM returned empty response",
                            "feedback": "LLM returned empty or invalid response"
                        })
                else:
                    # LLM failed, add to history
                    attempt_history.append({
                        "attempt": attempt + 1,
                        "code": current_code,
                        "errors": f"LLM failed: {response.error if hasattr(response, 'error') else 'Unknown error'}",
                        "feedback": "LLM request failed"
                    })
                    
            except Exception as llm_error:
                logger.error(f"LLM fix attempt {attempt + 1} failed: {llm_error}")
                attempt_history.append({
                    "attempt": attempt + 1,
                    "code": current_code,
                    "errors": str(llm_error),
                    "feedback": f"LLM exception: {llm_error}"
                })
        
        # All LLM attempts failed, fall back to rule-based fixes
        logger.warning("All LLM attempts failed, falling back to rule-based fixes")
        return await _apply_rule_based_fixes(request)
        
    except Exception as e:
        logger.error(f"Error in fix_code endpoint: {e}", exc_info=True)
        return CodeFixResponse(
            success=False,
            fixed_code=request.code,
            applied_fixes=[],
            remaining_errors=[{
                "line": 1,
                "column": 1,
                "message": f"Auto-fix failed: {str(e)}",
                "severity": "error",
                "code": ""
            }]
        )


def _build_iterative_prompt(
    original_code: str,
    current_code: str,
    error_messages: str,
    attempt_history: list,
    attempt_number: int,
    max_attempts: int
) -> str:
    """Build an iterative prompt that includes feedback from previous attempts."""
    
    # Reference Dana code examples
    reference_examples = """
REFERENCE DANA CODE EXAMPLES:

1. Basic Agent Structure:
```
agent WeatherAgent:
    name: str = "Weather Agent"
    description: str = "An agent that provides weather information"

def solve(query: str) -> str:
    return reason(f"Provide weather information for: {query}")
```

2. Agent with Variables:
```
agent CalculatorAgent:
    name: str = "Calculator Agent"
    description: str = "An agent that performs calculations"
    
    private:result = 0

def solve(query: str) -> str:
    private:calculation = reason(f"Calculate: {query}")
    return f"Result: {calculation}"
```

3. Agent with Imports:
```
# Import required modules
from dana.core.lang import reason
from dana.common.resource.llm import LLMResource

agent DataAnalyzer:
    name: str = "Data Analyzer"
    description: str = "An agent that analyzes data"

def solve(query: str) -> str:
    return reason(f"Analyze this data: {query}")
```

4. Agent with Functions:
```
agent TaskManager:
    name: str = "Task Manager"
    description: str = "An agent that manages tasks"
    
    private:task_list = []

def add_task(task: str):
    private:task_list.append(task)
    return f"Added task: {task}"

def solve(query: str) -> str:
    return reason(f"Manage tasks: {query}")
```

5. Agent with Error Handling:
```
agent SafeAgent:
    name: str = "Safe Agent"
    description: str = "An agent with error handling"
    
    private:error_count = 0

def solve(query: str) -> str:
    try:
        return reason(f"Process safely: {query}")
    except Exception as e:
        private:error_count += 1
        return f"Error occurred: {e}"
```

COMMON DANA SYNTAX RULES:
- Use `agent Name:` for agent definitions
- Use `name: str = "value"` for string variables
- Use `private:variable` for private variables
- Use `def function_name():` for function definitions
- Use proper indentation (4 spaces)
- Use `return` statements in functions
- Use `reason()` for AI reasoning
- Import modules with `from module import item`
- Use `try/except` for error handling
- Use `f"string {variable}"` for f-strings

COMMON ERROR PATTERNS AND FIXES:
- "No terminal matches" → Check for unclosed quotes, missing colons, or invalid syntax
- "expected ':'" → Add missing colon after function/class definitions
- "indentation" → Fix indentation (use 4 spaces, not tabs)
- "name 'reason' is not defined" → Add import: `from dana.core.lang import reason`
- "unexpected EOF" → Check for unclosed parentheses, brackets, or quotes
- "invalid syntax" → Check for missing colons, incorrect indentation, or malformed expressions
"""
    
    prompt = f"""You are an expert Dana programming language developer. Fix the following Dana code that has syntax errors.

{reference_examples}

ORIGINAL CODE:
```
{original_code}
```

CURRENT CODE (after {attempt_number - 1} previous attempts):
```
{current_code}
```

ORIGINAL ERRORS:
{error_messages}

ATTEMPT HISTORY:"""
    
    if attempt_history:
        for attempt in attempt_history:
            prompt += f"""

Attempt {attempt['attempt']}:
- Code: {attempt['code'][:200]}{'...' if len(attempt['code']) > 200 else ''}
- Errors: {attempt['errors']}
- Feedback: {attempt['feedback']}"""
    else:
        prompt += "\nNo previous attempts."
    
    prompt += f"""

CURRENT ATTEMPT ({attempt_number}/{max_attempts}):
Learn from the previous attempts and feedback above. Focus on:
1. Understanding why previous attempts failed
2. Addressing the specific error patterns shown
3. Making incremental improvements
4. Ensuring proper Dana syntax and structure

Return ONLY the corrected Dana code, no explanations:"""
    
    return prompt


def _extract_code_from_response(content) -> str:
    """Extract code from LLM response, handling various formats."""
    if isinstance(content, dict):
        if "choices" in content and content["choices"]:
            fixed_code = content["choices"][0]["message"]["content"]
        else:
            fixed_code = str(content)
    else:
        fixed_code = str(content)
    
    # Clean up the response (remove markdown if present)
    if "```" in fixed_code:
        # Extract code from markdown blocks
        start = fixed_code.find("```")
        if start != -1:
            start = fixed_code.find("\n", start) + 1
            end = fixed_code.find("```", start)
            if end != -1:
                fixed_code = fixed_code[start:end].strip()
    
    return fixed_code.strip()
        logger.error(f"Error in fix_code endpoint: {e}", exc_info=True)
        return CodeFixResponse(
            success=False,
            fixed_code=request.code,
            applied_fixes=[],
            remaining_errors=[{
                "line": 1,
                "column": 1,
                "message": f"Auto-fix failed: {str(e)}",
                "severity": "error",
                "code": ""
            }]
        )


async def _apply_rule_based_fixes(request: CodeFixRequest) -> CodeFixResponse:
    """Fallback rule-based fixes when LLM is not available"""
    fixed_code = request.code
    applied_fixes = []
    remaining_errors = []
    
    # Apply fixes based on error types
    for error in request.errors:
        error_msg = error.message.lower()
        
        # Fix unclosed strings
        if "no terminal matches" in error_msg and "in the current parser context" in error_msg:
            # Try to fix common string issues
            if '"' in fixed_code and fixed_code.count('"') % 2 != 0:
                # Add missing quote at the end
                fixed_code += '"'
                applied_fixes.append("Fixed unclosed string - added missing quote")
            elif "'" in fixed_code and fixed_code.count("'") % 2 != 0:
                # Add missing single quote at the end
                fixed_code += "'"
                applied_fixes.append("Fixed unclosed string - added missing single quote")
        
        # Fix missing agent definition
        elif "agent" in error_msg and "definition" in error_msg:
            if not fixed_code.strip().startswith('agent '):
                agent_name = request.agent_name or "CustomAgent"
                agent_def = f"""agent {agent_name}:
    name: str = "{agent_name}"
    description: str = "{request.description or 'A custom agent'}"

"""
                fixed_code = agent_def + fixed_code
                applied_fixes.append("Added agent definition")
        
        # Fix missing solve function
        elif "solve" in error_msg and "function" in error_msg:
            if "def solve(" not in fixed_code:
                solve_func = """

def solve(query: str) -> str:
    return reason(f"Process query: {query}")
"""
                fixed_code += solve_func
                applied_fixes.append("Added solve function")
        
        # Fix missing imports
        elif "import" in error_msg:
            if "import" not in fixed_code:
                imports = """# Add required imports
# import some_module

"""
                fixed_code = imports + fixed_code
                applied_fixes.append("Added import section")
        
        # Fix indentation issues
        elif "indentation" in error_msg or "expected an indented block" in error_msg:
            # Add basic indentation fix
            lines = fixed_code.split('\n')
            fixed_lines = []
            for line in lines:
                if line.strip() and not line.startswith(' ') and ':' in line:
                    # This line should be indented
                    fixed_lines.append('    ' + line)
                else:
                    fixed_lines.append(line)
            fixed_code = '\n'.join(fixed_lines)
            applied_fixes.append("Fixed indentation issues")
        
        # Fix missing colons
        elif "expected ':'" in error_msg:
            lines = fixed_code.split('\n')
            fixed_lines = []
            for line in lines:
                if line.strip() and not line.endswith(':') and ('def ' in line or 'if ' in line or 'for ' in line or 'while ' in line):
                    fixed_lines.append(line + ':')
                else:
                    fixed_lines.append(line)
            fixed_code = '\n'.join(fixed_lines)
            applied_fixes.append("Added missing colons")
        
        # Fix undefined variables
        elif "name" in error_msg and "is not defined" in error_msg:
            # Add basic imports for common functions
            if "reason(" in fixed_code and "import" not in fixed_code:
                imports = """# Import required functions
from dana.core.lang import reason

"""
                fixed_code = imports + fixed_code
                applied_fixes.append("Added missing imports for undefined functions")
        
        else:
            # Keep track of errors that couldn't be fixed
            remaining_errors.append(error)
    
    # Validate the fixed code
    syntax_result = DanaSandbox.quick_eval(fixed_code)
    if not syntax_result.success:
        remaining_errors.append({
            "line": 1,
            "column": 1,
            "message": f"Fixed code still has errors: {syntax_result.error}",
            "severity": "error",
            "code": ""
        })
    
    return CodeFixResponse(
        success=len(remaining_errors) == 0,
        fixed_code=fixed_code,
        applied_fixes=applied_fixes,
        remaining_errors=remaining_errors
    )
