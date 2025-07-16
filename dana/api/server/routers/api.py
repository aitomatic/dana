from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import os
import tempfile
import zipfile
import io
from pathlib import Path

from .. import db, schemas, services
from ..schemas import RunNAFileRequest, RunNAFileResponse, AgentGenerationRequest, AgentGenerationResponse, DanaSyntaxCheckRequest, DanaSyntaxCheckResponse, CodeValidationRequest, CodeValidationResponse, CodeFixRequest, CodeFixResponse, MultiFileProject, AgentDeployRequest, AgentDeployResponse
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


@router.post("/deploy", response_model=AgentDeployResponse)
async def deploy_agent(request: AgentDeployRequest, db: Session = Depends(db.get_db)):
    """
    Deploy an agent by creating database record and storing .na files in organized folder structure.
    
    This endpoint:
    1. Creates agent folder: agents/{agent_id}_{sanitized_name}/
    2. Writes .na files to the folder
    3. Creates metadata.json with agent info  
    4. Creates database record with folder path
    5. Returns agent info + file paths
    """
    import logging
    import json
    import re
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Deploying agent: {request.name}")
        
        # Create the agent in database first to get ID
        agent_create_data = schemas.AgentCreate(
            name=request.name,
            description=request.description,
            config=request.config
        )
        
        # Create agent record
        agent = services.create_agent(db, agent_create_data)
        logger.info(f"Created agent record with ID: {agent.id}")
        
        # Create sanitized folder name
        sanitized_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', request.name.lower())
        folder_name = f"agent_{agent.id}_{sanitized_name}"
        
        # Create agents directory if it doesn't exist
        agents_dir = Path("agents")
        agents_dir.mkdir(exist_ok=True)
        
        # Create agent folder
        agent_folder = agents_dir / folder_name
        agent_folder.mkdir(exist_ok=True)
        logger.info(f"Created agent folder: {agent_folder}")
        
        # Store file paths
        file_paths = []
        
        # Handle single file deployment
        if request.dana_code:
            agent_file = agent_folder / "agent.na"
            with open(agent_file, 'w', encoding='utf-8') as f:
                f.write(request.dana_code)
            file_paths.append(str(agent_file))
            logger.info(f"Created agent.na file: {agent_file}")
        
        # Handle multi-file deployment
        elif request.multi_file_project:
            project = request.multi_file_project
            for file_info in project.files:
                # Ensure .na extension
                filename = file_info.filename
                if not filename.endswith('.na'):
                    filename += '.na'
                
                file_path = agent_folder / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_info.content)
                file_paths.append(str(file_path))
                logger.info(f"Created file: {file_path}")
        
        # Create metadata.json
        metadata = {
            "agent_id": agent.id,
            "name": request.name,
            "description": request.description,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "config": request.config,
            "files": [str(Path(p).name) for p in file_paths],  # Store relative filenames
            "folder_path": str(agent_folder),
            "deployment_type": "multi_file" if request.multi_file_project else "single_file"
        }
        
        metadata_file = agent_folder / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        file_paths.append(str(metadata_file))
        logger.info(f"Created metadata.json: {metadata_file}")
        
        # Note: These are temporary files for generation preview only
        # No database operations needed for generation auto-storage
        
        logger.info(f"Agent deployed successfully: {agent.name} at {agent.folder_path}")
        
        return AgentDeployResponse(
            success=True,
            agent=agent
        )
        
    except Exception as e:
        logger.error(f"Error deploying agent: {e}", exc_info=True)
        # Rollback database changes
        db.rollback()
        
        # Clean up created files if any
        try:
            if 'agent_folder' in locals() and agent_folder.exists():
                import shutil
                shutil.rmtree(agent_folder)
                logger.info(f"Cleaned up agent folder: {agent_folder}")
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up files: {cleanup_error}")
        
        return AgentDeployResponse(
            success=False,
            error=f"Failed to deploy agent: {str(e)}"
        )


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
        
        # Generate Dana code first
        logger.info("Calling generate_agent_code_from_messages...")
        dana_code, syntax_error, conversation_analysis, multi_file_project = await generate_agent_code_from_messages(messages, request.current_code or "", request.multi_file)
        logger.info(f"Generated Dana code length: {len(dana_code)}")
        logger.debug(f"Generated Dana code: {dana_code[:500]}...")
        
        # Log multi-file info
        if multi_file_project:
            logger.info(f"Generated multi-file project with {len(multi_file_project['files'])} files")
        else:
            logger.info("Generated single-file agent")
        
        if syntax_error:
            logger.error(f"Syntax error in generated code: {syntax_error}")
            return AgentGenerationResponse(
                success=False,
                dana_code="",
                error=syntax_error
            )
        
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
        
        # Skip detailed capabilities analysis for cleaner response
        
        # Auto-store generated agents now that we have the names
        auto_stored_files = []
        if multi_file_project:
            try:
                logger.info("Auto-storing multi-file project")
                auto_stored_files = await _auto_store_multi_file_agent(
                    agent_name or "Generated_Agent", 
                    agent_description or "Auto-generated agent",
                    multi_file_project
                )
                logger.info(f"Auto-stored files: {auto_stored_files}")
            except Exception as e:
                logger.warning(f"Auto-storage failed (non-critical): {e}", exc_info=True)
                # Continue with response even if auto-storage fails
        else:
            # Auto-store single-file agents too
            try:
                logger.info("Auto-storing single-file agent")
                auto_stored_files = await _auto_store_single_file_agent(
                    agent_name or "Generated_Agent",
                    agent_description or "Auto-generated agent", 
                    dana_code
                )
                logger.info(f"Auto-stored single-file: {auto_stored_files}")
            except Exception as e:
                logger.warning(f"Single-file auto-storage failed (non-critical): {e}", exc_info=True)
        
        # Check if we need more information and include follow-up questions
        needs_more_info = conversation_analysis.get("needs_more_info", False)
        follow_up_message = conversation_analysis.get("follow_up_message") if needs_more_info else None
        suggested_questions = conversation_analysis.get("suggested_questions", []) if needs_more_info else None
        
        # Create multi-file project object if available
        multi_file_project_obj = None
        if multi_file_project:
            from ..schemas import DanaFile, MultiFileProject
            dana_files = [
                DanaFile(
                    filename=file_info['filename'],
                    content=file_info['content'],
                    file_type=file_info['file_type'],
                    description=file_info.get('description'),
                    dependencies=file_info.get('dependencies', [])
                )
                for file_info in multi_file_project['files']
            ]
            
            multi_file_project_obj = MultiFileProject(
                name=multi_file_project['name'],
                description=multi_file_project['description'],
                files=dana_files,
                main_file=multi_file_project['main_file'],
                structure_type=multi_file_project.get('structure_type', 'complex')
            )
        
        # Build minimal response
        response_data = {
            "success": syntax_error is None,
            "dana_code": dana_code,
            "error": syntax_error,
            "agent_name": agent_name,
            "agent_description": agent_description,
            "auto_stored_files": auto_stored_files if auto_stored_files else None,
            "multi_file_project": multi_file_project_obj
        }
        
        # Only include conversation guidance if needed
        if needs_more_info:
            response_data.update({
                "needs_more_info": True,
                "follow_up_message": follow_up_message,
                "suggested_questions": suggested_questions
            })
        
        response = AgentGenerationResponse(**response_data)
        
        logger.info(f"Returning response with success={response.success}, code_length={len(response.dana_code)}, needs_more_info={needs_more_info}")
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
    Supports both single-file and multi-file validation.
    Returns validation status, errors, warnings, and suggestions.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Handle multi-file validation
        if request.multi_file_project:
            print("validate multi file project")
            logger.info(f"Validating multi-file project: {request.multi_file_project.name}")
            
            # Create temporary directory for multi-file validation
            temp_dir = tempfile.mkdtemp(prefix=f"dana_validation_{request.multi_file_project.name.replace(' ', '_')}_")
            print("temp_dir", temp_dir)
            
            try:
                # Set DANA_PATH to the temporary directory
                original_dana_path = os.environ.get('DANA_PATH')
                os.environ['DANA_PATH'] = temp_dir
                
                # Write all files to temporary directory
                for dana_file in request.multi_file_project.files:
                    file_path = Path(temp_dir) / dana_file.filename
                    logger.info(f"Writing file for validation: {file_path}")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(dana_file.content)
                
                # Run validation on the main file
                main_file_path = Path(temp_dir) / request.multi_file_project.main_file
                logger.info(f"Validating main file: {main_file_path}")
                
                with open(main_file_path, 'r', encoding='utf-8') as f:
                    main_file_content = f.read()
                
                # Basic syntax validation using DanaSandbox
                syntax_result = DanaSandbox.quick_eval(main_file_content)
                
                errors = []
                warnings = []
                suggestions = []
                
                if not syntax_result.success:
                    error_text = str(syntax_result.error)
                    errors.append({
                        "line": 1,
                        "column": 1,
                        "message": error_text,
                        "severity": "error",
                        "code": error_text
                    })
                
                # Call the multi-file validation function
                multi_file_result = await validate_multi_file_project(request.multi_file_project)
                
                # Combine results
                is_valid = len(errors) == 0 and multi_file_result.get('success', False)
                
                return CodeValidationResponse(
                    success=True,
                    is_valid=is_valid,
                    errors=errors,
                    warnings=warnings,
                    suggestions=suggestions,
                    file_results=multi_file_result.get('file_results', []),
                    dependency_errors=multi_file_result.get('dependency_errors', []),
                    overall_errors=multi_file_result.get('overall_errors', [])
                )
                
            finally:
                # Restore original DANA_PATH
                if original_dana_path is not None:
                    os.environ['DANA_PATH'] = original_dana_path
                elif 'DANA_PATH' in os.environ:
                    del os.environ['DANA_PATH']
                
                # Clean up temporary directory
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary directory {temp_dir}: {cleanup_error}")
        
        # Handle single-file validation (backward compatibility)
        elif request.code:
            logger.info(f"Validating single-file code for agent: {request.agent_name}")
            
            # Basic syntax validation
            syntax_result = DanaSandbox.quick_eval(request.code)
            
            errors = []
            warnings = []
            suggestions = []
            
            if not syntax_result.success:
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
            logger.info(f"Single-file validation result: is_valid={is_valid}, errors={len(errors)}")
            
            return CodeValidationResponse(
                success=True,
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
        
        else:
            # Neither code nor multi_file_project provided
            return CodeValidationResponse(
                success=False,
                is_valid=False,
                errors=[{
                    "line": 1,
                    "column": 1,
                    "message": "Either 'code' or 'multi_file_project' must be provided",
                    "severity": "error",
                    "code": ""
                }],
                warnings=[],
                suggestions=[]
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
        # logger.error(f"Error in fix_code endpoint: {e}", exc_info=True)
        # return CodeFixResponse(
        #     success=False,
        #     fixed_code=request.code,
        #     applied_fixes=[],
        #     remaining_errors=[{
        #         "line": 1,
        #         "column": 1,
        #         "message": f"Auto-fix failed: {str(e)}",
        #         "severity": "error",
        #         "code": ""
        #     }]
        # )


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


@router.post("/write-files")
async def write_multi_file_project(project: MultiFileProject):
    """
    Write multi-file Dana project to temporary directory and return as ZIP.
    
    Args:
        project: MultiFileProject containing files to write
        
    Returns:
        ZIP file containing all project files
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Creating ZIP for project: {project.name}")
        
        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add each file to the ZIP
            for dana_file in project.files:
                logger.info(f"Adding file to ZIP: {dana_file.filename}")
                zip_file.writestr(dana_file.filename, dana_file.content)
                
            # Add project metadata
            metadata = f"""# {project.name}

{project.description}

## Project Structure
Structure Type: {project.structure_type}
Main File: {project.main_file}

## Files
"""
            for dana_file in project.files:
                metadata += f"- **{dana_file.filename}** ({dana_file.file_type}): {dana_file.description or 'Dana code file'}\n"
                if dana_file.dependencies:
                    metadata += f"  Dependencies: {', '.join(dana_file.dependencies)}\n"
            
            zip_file.writestr("README.md", metadata)
            logger.info("Added README.md to ZIP")
        
        zip_buffer.seek(0)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={project.name.replace(' ', '_')}.zip"}
        )
        
    except Exception as e:
        logger.error(f"Error creating ZIP file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create project files: {str(e)}")


@router.post("/write-files-temp")
async def write_multi_file_project_temp(project: MultiFileProject):
    """
    Write multi-file Dana project to temporary directory and return paths.
    
    Args:
        project: MultiFileProject containing files to write
        
    Returns:
        Dictionary with temporary directory path and file paths
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Creating temporary directory for project: {project.name}")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"dana_project_{project.name.replace(' ', '_')}_")
        file_paths = []
        
        # Write each file
        for dana_file in project.files:
            file_path = Path(temp_dir) / dana_file.filename
            logger.info(f"Writing file: {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(dana_file.content)
            file_paths.append(str(file_path))
        
        # Write project metadata
        metadata_path = Path(temp_dir) / "README.md"
        metadata = f"""# {project.name}

{project.description}

## Project Structure
Structure Type: {project.structure_type}
Main File: {project.main_file}

## Files
"""
        for dana_file in project.files:
            metadata += f"- **{dana_file.filename}** ({dana_file.file_type}): {dana_file.description or 'Dana code file'}\n"
            if dana_file.dependencies:
                metadata += f"  Dependencies: {', '.join(dana_file.dependencies)}\n"
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(metadata)
        
        logger.info(f"Project written to: {temp_dir}")
        
        return {
            "success": True,
            "temp_directory": temp_dir,
            "file_paths": file_paths,
            "metadata_path": str(metadata_path),
            "main_file_path": str(Path(temp_dir) / project.main_file)
        }
        
    except Exception as e:
        logger.error(f"Error writing temporary files: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to write project files: {str(e)}")


@router.post("/validate-multi-file")
async def validate_multi_file_project(project: MultiFileProject):
    """
    Validate all files in a multi-file Dana project.
    
    Args:
        project: MultiFileProject containing files to validate
        
    Returns:
        Dictionary with validation results for each file
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Validating multi-file project: {project.name}")
        
        validation_results = {
            "success": True,
            "project_name": project.name,
            "file_results": [],
            "dependency_errors": [],
            "overall_errors": []
        }
        
        # Validate each file individually
        for dana_file in project.files:
            logger.info(f"Validating file: {dana_file.filename}")
            
            file_result = {
                "filename": dana_file.filename,
                "file_type": dana_file.file_type,
                "success": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }
            
            try:
                # Use Dana sandbox to validate syntax
                syntax_result = DanaSandbox.quick_eval(dana_file.content)
                
                if not syntax_result.success:
                    file_result["success"] = False
                    file_result["errors"].append({
                        "line": 1,
                        "column": 1,
                        "message": f"Syntax error: {syntax_result.error}",
                        "severity": "error",
                        "code": ""
                    })
                    validation_results["success"] = False
                    logger.error(f"Syntax error in {dana_file.filename}: {syntax_result.error}")
                else:
                    logger.info(f"Syntax validation passed for {dana_file.filename}")
                
                # Check for file-specific patterns
                content = dana_file.content
                
                # Check for missing imports
                if "import" in content and not any(line.strip().startswith("import") or line.strip().startswith("from") for line in content.split('\n')):
                    file_result["warnings"].append({
                        "line": 1,
                        "column": 1,
                        "message": "File may be missing import statements",
                        "suggestion": "Add required imports at the top of the file"
                    })
                
                # Check for dependency consistency
                declared_deps = set(dana_file.dependencies)
                actual_imports = set()
                
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('import ') and not line.endswith('.py'):
                        module = line.replace('import ', '').strip()
                        actual_imports.add(module)
                    elif line.startswith('from ') and ' import ' in line:
                        module = line.split(' import ')[0].replace('from ', '').strip()
                        if not module.endswith('.py'):
                            actual_imports.add(module)
                
                # Check for missing dependencies
                missing_deps = actual_imports - declared_deps
                if missing_deps:
                    file_result["warnings"].append({
                        "line": 1,
                        "column": 1,
                        "message": f"Missing dependencies: {', '.join(missing_deps)}",
                        "suggestion": "Update file dependencies in project structure"
                    })
                
                # Check for unused dependencies
                unused_deps = declared_deps - actual_imports
                if unused_deps:
                    file_result["warnings"].append({
                        "line": 1,
                        "column": 1,
                        "message": f"Unused dependencies: {', '.join(unused_deps)}",
                        "suggestion": "Remove unused dependencies from project structure"
                    })
                
                # File-type specific validation
                if dana_file.file_type == "agent":
                    # Check for agent definition
                    if "agent " not in content:
                        file_result["errors"].append({
                            "line": 1,
                            "column": 1,
                            "message": "Agent file must contain an agent definition",
                            "severity": "error",
                            "code": ""
                        })
                        validation_results["success"] = False
                    
                    # Check for solve function
                    if "def solve(" not in content:
                        file_result["suggestions"].append({
                            "type": "best_practice",
                            "message": "Agent should have a solve function",
                            "code": "def solve(problem: str) -> str:\n    return reason(f\"Handle: {problem}\")",
                            "description": "Add a solve function to make the agent functional"
                        })
                
                elif dana_file.file_type == "resources":
                    # Check for resource usage patterns
                    if "use(" not in content:
                        file_result["warnings"].append({
                            "line": 1,
                            "column": 1,
                            "message": "Resources file should define resource usage",
                            "suggestion": "Add resource definitions using use() function"
                        })
                
                elif dana_file.file_type == "workflow":
                    # Check for workflow patterns
                    if "def " not in content:
                        file_result["warnings"].append({
                            "line": 1,
                            "column": 1,
                            "message": "Workflow file should define workflow functions",
                            "suggestion": "Add workflow function definitions"
                        })
                
                elif dana_file.file_type == "methods":
                    # Check for method definitions
                    if "def " not in content:
                        file_result["warnings"].append({
                            "line": 1,
                            "column": 1,
                            "message": "Methods file should define utility functions",
                            "suggestion": "Add utility function definitions"
                        })
                
            except Exception as e:
                logger.error(f"Error validating {dana_file.filename}: {e}")
                file_result["success"] = False
                file_result["errors"].append({
                    "line": 1,
                    "column": 1,
                    "message": f"Validation error: {str(e)}",
                    "severity": "error",
                    "code": ""
                })
                validation_results["success"] = False
            
            validation_results["file_results"].append(file_result)
        
        # Validate project-level dependencies
        all_filenames = {f.filename.replace('.na', '') for f in project.files}
        
        for dana_file in project.files:
            for dep in dana_file.dependencies:
                if dep not in all_filenames:
                    validation_results["dependency_errors"].append({
                        "file": dana_file.filename,
                        "missing_dependency": dep,
                        "message": f"File {dana_file.filename} depends on {dep} but {dep}.na is not in the project"
                    })
                    validation_results["success"] = False
        
        # Check for circular dependencies
        def has_circular_deps(filename, visited=None, path=None):
            if visited is None:
                visited = set()
            if path is None:
                path = []
            
            if filename in path:
                return True
            
            if filename in visited:
                return False
            
            visited.add(filename)
            path.append(filename)
            
            # Find file and check its dependencies
            for f in project.files:
                if f.filename.replace('.na', '') == filename:
                    for dep in f.dependencies:
                        if has_circular_deps(dep, visited, path.copy()):
                            return True
            
            path.pop()
            return False
        
        for dana_file in project.files:
            filename = dana_file.filename.replace('.na', '')
            if has_circular_deps(filename):
                validation_results["overall_errors"].append({
                    "type": "circular_dependency",
                    "message": f"Circular dependency detected involving {dana_file.filename}",
                    "file": dana_file.filename
                })
                validation_results["success"] = False
        
        logger.info(f"Validation complete. Success: {validation_results['success']}")
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating multi-file project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to validate project: {str(e)}")


# Auto-storage helper functions for agent generation
async def _auto_store_single_file_agent(agent_name: str, agent_description: str, dana_code: str) -> list[str]:
    """
    Auto-store a single-file agent to temporary generation folder.
    
    Args:
        agent_name: Name of the agent
        agent_description: Description of the agent
        dana_code: Dana code content
        
    Returns:
        List of file paths created
    """
    import re
    import json
    import uuid
    import logging
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    # Create unique folder for this generation
    sanitized_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', agent_name.lower())
    unique_id = str(uuid.uuid4())[:8]
    folder_name = f"generated_{sanitized_name}_{unique_id}"
    
    # Create generation directory if it doesn't exist
    generation_dir = Path("generated")
    generation_dir.mkdir(exist_ok=True)
    
    # Create agent folder
    agent_folder = generation_dir / folder_name
    agent_folder.mkdir(exist_ok=True)
    
    file_paths = []
    
    # Create agent.na file
    agent_file = agent_folder / "agent.na"
    with open(agent_file, 'w', encoding='utf-8') as f:
        f.write(dana_code)
    file_paths.append(str(agent_file))
    logger.info(f"Created agent.na file: {agent_file}")
    
    # Create metadata.json
    metadata = {
        "agent_name": agent_name,
        "description": agent_description,
        "generated_at": datetime.now().isoformat(),
        "files": ["agent.na"],
        "folder_path": str(agent_folder),
        "generation_type": "single_file",
        "temporary": True
    }
    
    metadata_file = agent_folder / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    file_paths.append(str(metadata_file))
    logger.info(f"Created metadata.json: {metadata_file}")
    
    logger.info(f"Auto-storage completed. Created {len(file_paths)} files: {file_paths}")
    return file_paths


async def _auto_store_multi_file_agent(agent_name: str, agent_description: str, multi_file_project: dict) -> list[str]:
    """
    Auto-store a multi-file agent to temporary generation folder.
    
    Args:
        agent_name: Name of the agent
        agent_description: Description of the agent
        multi_file_project: Multi-file project data
        
    Returns:
        List of file paths created
    """
    import re
    import json
    import uuid
    import logging
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    # Create unique folder for this generation
    sanitized_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', agent_name.lower())
    unique_id = str(uuid.uuid4())[:8]
    folder_name = f"generated_{sanitized_name}_{unique_id}"
    
    # Create generation directory if it doesn't exist
    generation_dir = Path("generated")
    generation_dir.mkdir(exist_ok=True)
    
    # Create agent folder
    agent_folder = generation_dir / folder_name
    agent_folder.mkdir(exist_ok=True)
    logger.info(f"Created multi-file agent folder: {agent_folder}")
    
    file_paths = []
    
    # Create files from multi-file project
    for file_info in multi_file_project['files']:
        filename = file_info['filename']
        if not filename.endswith('.na'):
            filename += '.na'
        
        file_path = agent_folder / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_info['content'])
        file_paths.append(str(file_path))
        logger.info(f"Created file: {file_path}")
    
    # Create metadata.json
    metadata = {
        "agent_name": agent_name,
        "description": agent_description,
        "generated_at": datetime.now().isoformat(),
        "files": [Path(p).name for p in file_paths],
        "folder_path": str(agent_folder),
        "generation_type": "multi_file",
        "main_file": multi_file_project.get('main_file', 'agent.na'),
        "structure_type": multi_file_project.get('structure_type', 'modular'),
        "temporary": True
    }
    
    metadata_file = agent_folder / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    file_paths.append(str(metadata_file))
    logger.info(f"Created metadata.json: {metadata_file}")
    
    logger.info(f"Multi-file auto-storage completed. Created {len(file_paths)} files: {file_paths}")
    return file_paths


@router.get("/open-file/{file_path:path}")
async def open_file_location(file_path: str):
    """
    Open file location in Finder/Explorer.
    
    Args:
        file_path: Encoded file path to open
        
    Returns:
        Success status
    """
    import subprocess
    import platform
    import urllib.parse
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Decode the file path
        decoded_path = urllib.parse.unquote(file_path)
        file_path_obj = Path(decoded_path)
        
        # Security check - ensure path is within allowed directories
        allowed_dirs = [Path("agents"), Path("generated"), Path("tmp")]
        is_allowed = any(
            str(file_path_obj.resolve()).startswith(str((Path.cwd() / allowed_dir).resolve()))
            for allowed_dir in allowed_dirs
        )
        
        if not is_allowed:
            raise HTTPException(status_code=403, detail="Access to this file path is not allowed")
        
        # Check if file exists, if not try pattern matching
        if not file_path_obj.exists():
            # Try pattern matching for wildcard paths (e.g., generated_agent*/agent.na)
            import glob
            if '*' in decoded_path or '?' in decoded_path:
                logger.info(f"File not found, trying pattern matching for: {decoded_path}")
                matches = glob.glob(decoded_path)
                if matches:
                    # Use the first match
                    actual_file_path = matches[0]
                    file_path_obj = Path(actual_file_path)
                    logger.info(f"Pattern matched to: {actual_file_path}")
                    
                    # Re-validate security for the resolved path
                    is_allowed = any(
                        str(file_path_obj.resolve()).startswith(str((Path.cwd() / allowed_dir).resolve()))
                        for allowed_dir in allowed_dirs
                    )
                    if not is_allowed:
                        raise HTTPException(status_code=403, detail="Resolved file path is not allowed")
                else:
                    raise HTTPException(status_code=404, detail=f"No files match pattern: {decoded_path}")
            else:
                raise HTTPException(status_code=404, detail="File not found")
        
        # Get the directory containing the file
        directory = file_path_obj.parent if file_path_obj.is_file() else file_path_obj
        
        # Open based on platform
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(directory)], check=True)
        elif system == "Windows":
            subprocess.run(["explorer", str(directory)], check=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", str(directory)], check=True)
        else:
            raise HTTPException(status_code=501, detail=f"Opening files not supported on {system}")
        
        logger.info(f"Opened file location: {directory}")
        return {"success": True, "message": f"Opened {directory}"}
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to open file location: {e}")
        raise HTTPException(status_code=500, detail="Failed to open file location")
    except Exception as e:
        logger.error(f"Error opening file location: {e}")
        raise HTTPException(status_code=500, detail=str(e))
