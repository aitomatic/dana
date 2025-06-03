# Workflow Agent Recipe

*Build intelligent workflow automation agents with OpenDXA*

---

## Overview

This recipe demonstrates how to build sophisticated workflow automation agents using OpenDXA. Learn to create agents that can orchestrate complex business processes, make intelligent decisions, and adapt to changing conditions.

## 🎯 What You'll Build

A comprehensive workflow automation system that can:
- **Orchestrate** multi-step business processes
- **Make** intelligent decisions at workflow branches
- **Handle** errors and exceptions gracefully
- **Adapt** workflows based on real-time conditions
- **Monitor** and report on workflow performance

## 🚀 Quick Start

### Basic Workflow Agent

```dana
# Configure workflow agent
llm = create_llm_resource(provider="openai", model="gpt-4")
workflow_memory = create_memory_resource()

# Simple workflow definition
def create_order_workflow(order_data):
    """Basic order processing workflow."""
    
    # Step 1: Validate order
    validation_result = reason(f"""
    Validate this order data:
    {order_data}
    
    Check:
    - Required fields are present
    - Data formats are correct
    - Business rules are satisfied
    
    Return validation status and any issues.
    """)
    
    if not validation_result["valid"]:
        return {
            "status": "failed",
            "step": "validation",
            "errors": validation_result["issues"]
        }
    
    # Step 2: Check inventory
    inventory_check = check_inventory(order_data["items"])
    
    if not inventory_check["available"]:
        return {
            "status": "failed",
            "step": "inventory_check",
            "message": "Insufficient inventory",
            "shortfall": inventory_check["shortfall"]
        }
    
    # Step 3: Process payment
    payment_result = process_payment(order_data["payment_info"])
    
    if not payment_result["success"]:
        return {
            "status": "failed",
            "step": "payment_processing",
            "error": payment_result["error"]
        }
    
    # Step 4: Create order record
    order_id = create_order_record(order_data, payment_result["transaction_id"])
    
    # Step 5: Schedule fulfillment
    fulfillment_scheduled = schedule_fulfillment(order_id, order_data["items"])
    
    # Log workflow completion
    log(f"Order workflow completed successfully: {order_id}", level="INFO")
    
    return {
        "status": "completed",
        "order_id": order_id,
        "payment_transaction": payment_result["transaction_id"],
        "fulfillment_date": fulfillment_scheduled["estimated_date"]
    }

# Execute workflow
order_data = {
    "customer_id": "12345",
    "items": [{"product_id": "ABC123", "quantity": 2}],
    "payment_info": {"method": "credit_card", "amount": 99.99}
}

result = create_order_workflow(order_data)
log(f"Workflow result: {result}", level="INFO")
```

### Advanced Workflow Engine

```dana
# Advanced workflow engine with dynamic routing
class WorkflowEngine:
    def __init__(self):
        self.workflows = {}
        self.active_instances = {}
        self.workflow_memory = create_memory_resource()
    
    def register_workflow(self, workflow_id, workflow_definition):
        """Register a new workflow definition."""
        self.workflows[workflow_id] = workflow_definition
        log(f"Registered workflow: {workflow_id}", level="INFO")
    
    def start_workflow(self, workflow_id, input_data, instance_id=None):
        """Start a workflow instance."""
        
        if workflow_id not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        
        instance_id = instance_id or generate_unique_id()
        
        # Initialize workflow context
        context = {
            "instance_id": instance_id,
            "workflow_id": workflow_id,
            "input_data": input_data,
            "current_step": 0,
            "step_results": [],
            "status": "running",
            "started_at": get_current_time(),
            "variables": {}
        }
        
        # Store active instance
        self.active_instances[instance_id] = context
        
        # Execute workflow
        return self.execute_workflow(instance_id)
    
    def execute_workflow(self, instance_id):
        """Execute workflow steps."""
        
        context = self.active_instances[instance_id]
        workflow_def = self.workflows[context["workflow_id"]]
        
        try:
            while context["current_step"] < len(workflow_def["steps"]):
                step = workflow_def["steps"][context["current_step"]]
                
                # Execute step
                step_result = self.execute_step(step, context)
                
                # Store result
                context["step_results"].append({
                    "step_name": step["name"],
                    "result": step_result,
                    "timestamp": get_current_time()
                })
                
                # Check for workflow control
                if step_result.get("action") == "terminate":
                    context["status"] = "terminated"
                    break
                elif step_result.get("action") == "branch":
                    # Handle conditional branching
                    next_step = self.determine_branch(step_result, context)
                    context["current_step"] = next_step
                    continue
                elif step_result.get("action") == "wait":
                    # Handle waiting conditions
                    context["status"] = "waiting"
                    context["wait_condition"] = step_result["wait_condition"]
                    break
                
                # Move to next step
                context["current_step"] += 1
            
            # Complete workflow if all steps finished
            if context["current_step"] >= len(workflow_def["steps"]):
                context["status"] = "completed"
                context["completed_at"] = get_current_time()
            
        except Exception as e:
            context["status"] = "failed"
            context["error"] = str(e)
            log(f"Workflow {instance_id} failed: {e}", level="ERROR")
        
        return context
    
    def execute_step(self, step, context):
        """Execute individual workflow step."""
        
        step_type = step["type"]
        
        if step_type == "decision":
            return self.execute_decision_step(step, context)
        elif step_type == "action":
            return self.execute_action_step(step, context)
        elif step_type == "ai_analysis":
            return self.execute_ai_step(step, context)
        elif step_type == "parallel":
            return self.execute_parallel_step(step, context)
        elif step_type == "loop":
            return self.execute_loop_step(step, context)
        else:
            raise ValueError(f"Unknown step type: {step_type}")
    
    def execute_decision_step(self, step, context):
        """Execute decision step with AI-powered analysis."""
        
        decision_prompt = step["decision_prompt"].format(
            context=context,
            variables=context["variables"]
        )
        
        decision = reason(decision_prompt)
        
        # Parse decision result
        if "branch" in decision:
            return {
                "action": "branch",
                "branch": decision["branch"],
                "reasoning": decision["reasoning"]
            }
        else:
            return {
                "action": "continue",
                "decision": decision
            }
    
    def execute_action_step(self, step, context):
        """Execute action step."""
        
        action_type = step["action_type"]
        parameters = step.get("parameters", {})
        
        # Substitute variables in parameters
        resolved_params = self.resolve_parameters(parameters, context)
        
        if action_type == "api_call":
            return self.execute_api_action(resolved_params)
        elif action_type == "database_operation":
            return self.execute_database_action(resolved_params)
        elif action_type == "notification":
            return self.execute_notification_action(resolved_params)
        elif action_type == "file_operation":
            return self.execute_file_action(resolved_params)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def execute_ai_step(self, step, context):
        """Execute AI analysis step."""
        
        analysis_prompt = step["prompt"].format(
            context=context,
            input_data=context["input_data"],
            variables=context["variables"]
        )
        
        analysis_result = reason(analysis_prompt)
        
        # Update context variables if specified
        if "output_variables" in step:
            for var_name in step["output_variables"]:
                if var_name in analysis_result:
                    context["variables"][var_name] = analysis_result[var_name]
        
        return {
            "action": "continue",
            "analysis": analysis_result
        }
    
    def execute_parallel_step(self, step, context):
        """Execute parallel workflow branches."""
        
        parallel_results = []
        
        for branch in step["branches"]:
            # Create sub-context for branch
            branch_context = context.copy()
            branch_context["branch_name"] = branch["name"]
            
            # Execute branch
            branch_result = self.execute_step_sequence(branch["steps"], branch_context)
            parallel_results.append({
                "branch": branch["name"],
                "result": branch_result
            })
        
        # Merge results based on merge strategy
        merge_strategy = step.get("merge_strategy", "all_complete")
        merged_result = self.merge_parallel_results(parallel_results, merge_strategy)
        
        return {
            "action": "continue",
            "parallel_results": parallel_results,
            "merged_result": merged_result
        }
    
    def resolve_parameters(self, parameters, context):
        """Resolve parameter values using context variables."""
        
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("${"):
                # Variable substitution
                var_name = value[2:-1]  # Remove ${ and }
                if var_name in context["variables"]:
                    resolved[key] = context["variables"][var_name]
                else:
                    resolved[key] = value  # Keep original if variable not found
            else:
                resolved[key] = value
        
        return resolved

# Create workflow engine instance
workflow_engine = WorkflowEngine()
```

## 📋 Implementation Steps

### Step 1: Define Workflow Structure

```dana
# Workflow definition format
def create_workflow_definition(workflow_config):
    """Create structured workflow definition."""
    
    return {
        "id": workflow_config["id"],
        "name": workflow_config["name"],
        "description": workflow_config["description"],
        "version": workflow_config.get("version", "1.0"),
        "input_schema": workflow_config["input_schema"],
        "output_schema": workflow_config["output_schema"],
        "steps": workflow_config["steps"],
        "error_handling": workflow_config.get("error_handling", {}),
        "timeout": workflow_config.get("timeout", 3600),  # 1 hour default
        "retry_policy": workflow_config.get("retry_policy", {})
    }

# Example: Customer onboarding workflow
customer_onboarding_workflow = create_workflow_definition({
    "id": "customer_onboarding",
    "name": "Customer Onboarding Process",
    "description": "Automated customer onboarding with verification and setup",
    "input_schema": {
        "customer_data": "object",
        "account_type": "string",
        "initial_deposit": "number"
    },
    "output_schema": {
        "customer_id": "string",
        "account_id": "string",
        "onboarding_status": "string"
    },
    "steps": [
        {
            "name": "validate_customer_data",
            "type": "ai_analysis",
            "prompt": """
            Validate customer data for onboarding:
            {input_data}
            
            Check:
            - Required fields completeness
            - Data format validity
            - Compliance requirements
            - Risk indicators
            
            Return validation result with any issues found.
            """,
            "output_variables": ["validation_status", "risk_score"]
        },
        {
            "name": "risk_assessment_decision",
            "type": "decision",
            "decision_prompt": """
            Based on risk score {variables[risk_score]}, determine onboarding path:
            
            - If risk_score < 30: proceed with standard onboarding
            - If 30 <= risk_score < 70: require additional verification
            - If risk_score >= 70: escalate to manual review
            
            Return the appropriate branch decision.
            """,
            "branches": {
                "standard": 1,
                "verification": 2,
                "manual_review": 3
            }
        },
        {
            "name": "create_customer_account",
            "type": "action",
            "action_type": "api_call",
            "parameters": {
                "endpoint": "/customers",
                "method": "POST",
                "data": "${customer_data}"
            }
        },
        {
            "name": "setup_initial_services",
            "type": "parallel",
            "branches": [
                {
                    "name": "create_banking_account",
                    "steps": [
                        {
                            "name": "create_account",
                            "type": "action",
                            "action_type": "api_call",
                            "parameters": {
                                "endpoint": "/accounts",
                                "method": "POST",
                                "data": {
                                    "customer_id": "${customer_id}",
                                    "account_type": "${account_type}",
                                    "initial_deposit": "${initial_deposit}"
                                }
                            }
                        }
                    ]
                },
                {
                    "name": "setup_digital_access",
                    "steps": [
                        {
                            "name": "create_login_credentials",
                            "type": "action",
                            "action_type": "api_call",
                            "parameters": {
                                "endpoint": "/auth/setup",
                                "method": "POST",
                                "data": {
                                    "customer_id": "${customer_id}",
                                    "email": "${customer_data.email}"
                                }
                            }
                        }
                    ]
                }
            ],
            "merge_strategy": "all_complete"
        },
        {
            "name": "send_welcome_notification",
            "type": "action",
            "action_type": "notification",
            "parameters": {
                "type": "email",
                "recipient": "${customer_data.email}",
                "template": "welcome_new_customer",
                "data": {
                    "customer_name": "${customer_data.name}",
                    "account_id": "${account_id}"
                }
            }
        }
    ],
    "error_handling": {
        "retry_failed_steps": True,
        "max_retries": 3,
        "escalation_on_failure": True
    }
})

# Register workflow
workflow_engine.register_workflow(
    "customer_onboarding", 
    customer_onboarding_workflow
)
```

### Step 2: Advanced Workflow Controls

```dana
# Conditional branching and loops
def execute_conditional_workflow(workflow_config, input_data):
    """Execute workflow with advanced control structures."""
    
    # Initialize workflow context
    context = {
        "input": input_data,
        "variables": {},
        "loop_counters": {},
        "branch_history": []
    }
    
    # Execute workflow with control flow
    result = execute_workflow_with_controls(workflow_config, context)
    return result

def execute_workflow_with_controls(workflow_config, context):
    """Execute workflow supporting loops and complex branching."""
    
    step_index = 0
    
    while step_index < len(workflow_config["steps"]):
        step = workflow_config["steps"][step_index]
        
        try:
            if step["type"] == "loop":
                step_index = execute_loop_workflow(step, context, step_index)
            elif step["type"] == "conditional_branch":
                step_index = execute_conditional_branch(step, context, step_index)
            elif step["type"] == "while_loop":
                step_index = execute_while_loop(step, context, step_index)
            else:
                # Regular step execution
                step_result = execute_regular_step(step, context)
                context["variables"].update(step_result.get("variables", {}))
                step_index += 1
                
        except Exception as e:
            # Handle step execution errors
            error_handled = handle_step_error(step, e, context, workflow_config)
            if not error_handled:
                raise e
            step_index += 1
    
    return context

def execute_loop_workflow(loop_step, context, current_index):
    """Execute loop workflow structure."""
    
    loop_config = loop_step["loop_config"]
    loop_variable = loop_config["variable"]
    loop_items = resolve_loop_items(loop_config["items"], context)
    
    # Initialize loop counter
    loop_id = loop_step["name"]
    context["loop_counters"][loop_id] = 0
    
    for item in loop_items:
        # Set loop variable
        context["variables"][loop_variable] = item
        
        # Execute loop body
        for body_step in loop_step["body"]:
            step_result = execute_regular_step(body_step, context)
            context["variables"].update(step_result.get("variables", {}))
        
        # Increment counter
        context["loop_counters"][loop_id] += 1
        
        # Check break condition
        if "break_condition" in loop_config:
            break_condition = evaluate_condition(
                loop_config["break_condition"], 
                context
            )
            if break_condition:
                break
    
    # Continue to next step after loop
    return current_index + 1

def execute_conditional_branch(branch_step, context, current_index):
    """Execute conditional branching."""
    
    # Evaluate condition
    condition = branch_step["condition"]
    condition_result = evaluate_condition(condition, context)
    
    # Record branch decision
    context["branch_history"].append({
        "step": branch_step["name"],
        "condition": condition,
        "result": condition_result,
        "timestamp": get_current_time()
    })
    
    # Execute appropriate branch
    if condition_result:
        # Execute true branch
        for step in branch_step["true_branch"]:
            step_result = execute_regular_step(step, context)
            context["variables"].update(step_result.get("variables", {}))
    else:
        # Execute false branch (if exists)
        if "false_branch" in branch_step:
            for step in branch_step["false_branch"]:
                step_result = execute_regular_step(step, context)
                context["variables"].update(step_result.get("variables", {}))
    
    return current_index + 1

def evaluate_condition(condition, context):
    """Evaluate workflow condition."""
    
    if condition["type"] == "ai_decision":
        # Use AI to evaluate complex conditions
        decision = reason(f"""
        Evaluate this condition based on current context:
        
        Condition: {condition["description"]}
        Context variables: {context["variables"]}
        
        Return true or false with reasoning.
        """)
        return decision["result"]
    
    elif condition["type"] == "expression":
        # Evaluate mathematical or logical expression
        return evaluate_expression(condition["expression"], context["variables"])
    
    elif condition["type"] == "comparison":
        # Simple value comparison
        left_value = resolve_value(condition["left"], context)
        right_value = resolve_value(condition["right"], context)
        operator = condition["operator"]
        
        if operator == "==":
            return left_value == right_value
        elif operator == "!=":
            return left_value != right_value
        elif operator == ">":
            return left_value > right_value
        elif operator == "<":
            return left_value < right_value
        elif operator == ">=":
            return left_value >= right_value
        elif operator == "<=":
            return left_value <= right_value
        elif operator == "in":
            return left_value in right_value
        elif operator == "contains":
            return right_value in left_value
    
    return False
```

### Step 3: Error Handling and Recovery

```dana
# Comprehensive error handling
def implement_workflow_error_handling(workflow_engine):
    """Implement sophisticated error handling for workflows."""
    
    def handle_workflow_error(instance_id, error, step_context):
        """Handle workflow execution errors intelligently."""
        
        context = workflow_engine.active_instances[instance_id]
        workflow_def = workflow_engine.workflows[context["workflow_id"]]
        error_policy = workflow_def.get("error_handling", {})
        
        # Analyze error with AI
        error_analysis = reason(f"""
        Analyze this workflow error and recommend recovery action:
        
        Error: {error}
        Step context: {step_context}
        Workflow context: {context}
        Available recovery options: {error_policy}
        
        Consider:
        - Error type and severity
        - Step importance and dependencies
        - Recovery feasibility
        - Business impact
        
        Recommend: retry, skip, compensate, or escalate
        """)
        
        recovery_action = error_analysis["recommended_action"]
        
        if recovery_action == "retry":
            return retry_failed_step(instance_id, step_context, error_policy)
        elif recovery_action == "skip":
            return skip_failed_step(instance_id, step_context)
        elif recovery_action == "compensate":
            return execute_compensation(instance_id, step_context, error_policy)
        elif recovery_action == "escalate":
            return escalate_workflow_error(instance_id, error, step_context)
        else:
            return False  # Cannot handle error
    
    def retry_failed_step(instance_id, step_context, error_policy):
        """Retry failed step with backoff strategy."""
        
        max_retries = error_policy.get("max_retries", 3)
        retry_delay = error_policy.get("retry_delay", 5)
        backoff_factor = error_policy.get("backoff_factor", 2)
        
        step_name = step_context["step"]["name"]
        retry_count = context.get("retry_counts", {}).get(step_name, 0)
        
        if retry_count < max_retries:
            # Increment retry count
            if "retry_counts" not in context:
                context["retry_counts"] = {}
            context["retry_counts"][step_name] = retry_count + 1
            
            # Calculate delay
            delay = retry_delay * (backoff_factor ** retry_count)
            
            log(f"Retrying step {step_name} (attempt {retry_count + 1}) after {delay}s", level="INFO")
            
            # Wait and retry
            wait(delay)
            return True
        else:
            log(f"Max retries exceeded for step {step_name}", level="ERROR")
            return False
    
    def execute_compensation(instance_id, step_context, error_policy):
        """Execute compensation logic for failed steps."""
        
        compensation_steps = error_policy.get("compensation_steps", [])
        
        for comp_step in compensation_steps:
            try:
                # Execute compensation step
                comp_result = workflow_engine.execute_step(comp_step, context)
                log(f"Executed compensation: {comp_step['name']}", level="INFO")
            except Exception as comp_error:
                log(f"Compensation failed: {comp_error}", level="ERROR")
                return False
        
        return True
    
    def escalate_workflow_error(instance_id, error, step_context):
        """Escalate workflow error to human operators."""
        
        escalation_data = {
            "instance_id": instance_id,
            "error": str(error),
            "step_context": step_context,
            "workflow_context": context,
            "timestamp": get_current_time(),
            "priority": determine_escalation_priority(error, context)
        }
        
        # Send escalation notification
        send_escalation_notification(escalation_data)
        
        # Mark workflow as requiring human intervention
        context["status"] = "escalated"
        context["escalation_data"] = escalation_data
        
        return True
    
    # Attach error handler to workflow engine
    workflow_engine.error_handler = handle_workflow_error
    
    return workflow_engine
```

### Step 4: Workflow Monitoring and Analytics

```dana
# Workflow monitoring and analytics
def implement_workflow_monitoring(workflow_engine):
    """Implement comprehensive workflow monitoring."""
    
    # Performance metrics tracking
    workflow_metrics = {}
    
    def track_workflow_metrics(instance_id, event_type, data=None):
        """Track workflow execution metrics."""
        
        if instance_id not in workflow_metrics:
            workflow_metrics[instance_id] = {
                "events": [],
                "performance": {},
                "errors": []
            }
        
        metrics = workflow_metrics[instance_id]
        
        # Record event
        event = {
            "type": event_type,
            "timestamp": get_current_time(),
            "data": data
        }
        metrics["events"].append(event)
        
        # Update performance metrics
        if event_type == "step_completed":
            step_name = data["step_name"]
            execution_time = data["execution_time"]
            
            if step_name not in metrics["performance"]:
                metrics["performance"][step_name] = []
            metrics["performance"][step_name].append(execution_time)
        
        # Track errors
        elif event_type == "step_failed":
            metrics["errors"].append({
                "step": data["step_name"],
                "error": data["error"],
                "timestamp": event["timestamp"]
            })
    
    def generate_workflow_analytics(time_period="last_24h"):
        """Generate workflow analytics and insights."""
        
        # Collect metrics for time period
        period_metrics = filter_metrics_by_time(workflow_metrics, time_period)
        
        # Generate analytics with AI
        analytics = reason(f"""
        Analyze these workflow metrics and generate insights:
        {period_metrics}
        
        Provide:
        1. Performance summary
        2. Bottleneck identification
        3. Error pattern analysis
        4. Optimization recommendations
        5. Capacity planning insights
        """)
        
        return analytics
    
    def monitor_workflow_health():
        """Monitor overall workflow system health."""
        
        active_workflows = len(workflow_engine.active_instances)
        failed_workflows = len([
            w for w in workflow_engine.active_instances.values() 
            if w["status"] == "failed"
        ])
        
        health_status = {
            "active_workflows": active_workflows,
            "failed_workflows": failed_workflows,
            "success_rate": calculate_success_rate(),
            "average_execution_time": calculate_average_execution_time(),
            "system_load": calculate_system_load()
        }
        
        # Generate health assessment
        health_analysis = reason(f"""
        Assess workflow system health:
        {health_status}
        
        Determine:
        - Overall system health (healthy/warning/critical)
        - Performance trends
        - Capacity concerns
        - Recommended actions
        """)
        
        return {
            "metrics": health_status,
            "analysis": health_analysis,
            "timestamp": get_current_time()
        }
    
    # Attach monitoring functions
    workflow_engine.track_metrics = track_workflow_metrics
    workflow_engine.generate_analytics = generate_workflow_analytics
    workflow_engine.monitor_health = monitor_workflow_health
    
    return workflow_engine
```

## 🔍 Advanced Features

### Dynamic Workflow Modification

```dana
# Dynamic workflow adaptation
def implement_adaptive_workflows(workflow_engine):
    """Implement workflows that adapt based on execution patterns."""
    
    def adapt_workflow_based_on_performance(workflow_id, performance_data):
        """Adapt workflow based on performance analysis."""
        
        adaptation_analysis = reason(f"""
        Analyze workflow performance and suggest optimizations:
        {performance_data}
        
        Consider:
        - Step execution times
        - Error patterns
        - Resource utilization
        - Success rates
        
        Suggest specific workflow modifications to improve performance.
        """)
        
        # Apply suggested modifications
        if "suggested_modifications" in adaptation_analysis:
            for modification in adaptation_analysis["suggested_modifications"]:
                apply_workflow_modification(workflow_id, modification)
        
        return adaptation_analysis
    
    def apply_workflow_modification(workflow_id, modification):
        """Apply modification to workflow definition."""
        
        workflow_def = workflow_engine.workflows[workflow_id]
        
        if modification["type"] == "add_parallel_execution":
            # Add parallel execution to compatible steps
            add_parallel_execution(workflow_def, modification["steps"])
        
        elif modification["type"] == "add_caching":
            # Add caching to expensive operations
            add_step_caching(workflow_def, modification["steps"])
        
        elif modification["type"] == "modify_retry_policy":
            # Adjust retry policies based on failure patterns
            modify_retry_policies(workflow_def, modification["new_policies"])
        
        elif modification["type"] == "add_early_exit":
            # Add early exit conditions for efficiency
            add_early_exit_conditions(workflow_def, modification["conditions"])
        
        log(f"Applied modification to {workflow_id}: {modification['type']}", level="INFO")
    
    # Attach adaptation functions
    workflow_engine.adapt_workflow = adapt_workflow_based_on_performance
    
    return workflow_engine
```

### Multi-Agent Workflow Coordination

```dana
# Multi-agent workflow coordination
def create_multi_agent_workflow(agent_configs, coordination_strategy):
    """Create workflow coordinated across multiple agents."""
    
    agents = {}
    
    # Initialize agents
    for agent_id, config in agent_configs.items():
        agents[agent_id] = create_agent(config)
    
    def execute_coordinated_workflow(workflow_steps, coordination_data):
        """Execute workflow across multiple agents."""
        
        coordination_results = {}
        
        for step in workflow_steps:
            assigned_agent = step["assigned_agent"]
            
            if assigned_agent not in agents:
                raise ValueError(f"Unknown agent: {assigned_agent}")
            
            # Prepare agent context
            agent_context = {
                "step_data": step["data"],
                "coordination_data": coordination_data,
                "previous_results": coordination_results
            }
            
            # Execute step on assigned agent
            step_result = agents[assigned_agent].execute_workflow_step(
                step["action"], 
                agent_context
            )
            
            # Store result for coordination
            coordination_results[step["name"]] = step_result
            
            # Update coordination data
            coordination_data = update_coordination_data(
                coordination_data, 
                step_result, 
                coordination_strategy
            )
        
        return coordination_results
    
    return execute_coordinated_workflow
```

## 📊 Testing and Validation

### Workflow Testing Framework

```dana
# Comprehensive workflow testing
def create_workflow_testing_framework():
    """Create framework for testing complex workflows."""
    
    def test_workflow_scenario(workflow_id, test_scenario):
        """Test workflow with specific scenario."""
        
        # Setup test environment
        test_context = setup_test_environment(test_scenario)
        
        # Execute workflow
        result = workflow_engine.start_workflow(
            workflow_id, 
            test_scenario["input_data"],
            instance_id=f"test_{generate_test_id()}"
        )
        
        # Validate results
        validation = validate_workflow_result(
            result, 
            test_scenario["expected_outcome"]
        )
        
        # Generate test report
        test_report = generate_test_report(
            test_scenario, 
            result, 
            validation
        )
        
        return test_report
    
    def validate_workflow_result(actual_result, expected_outcome):
        """Validate workflow result against expected outcome."""
        
        validation = reason(f"""
        Validate workflow execution result:
        
        Actual result: {actual_result}
        Expected outcome: {expected_outcome}
        
        Check:
        - Workflow completion status
        - Output data correctness
        - Business rule compliance
        - Performance criteria
        
        Return detailed validation report.
        """)
        
        return validation
    
    return {
        "test_scenario": test_workflow_scenario,
        "validate_result": validate_workflow_result
    }
```

## 🎯 Next Steps

### Enhancements
- Add visual workflow designer
- Implement workflow versioning
- Create workflow templates library
- Add real-time workflow monitoring dashboard
- Implement workflow performance optimization

### Integration Patterns
- Event-driven workflow triggers
- External system integrations
- Human-in-the-loop workflows
- Workflow composition patterns
- Microservices orchestration

---

*Ready to automate your workflows? Try the [Quick Start](#quick-start) example or explore more [OpenDXA Recipes](../README.md).*