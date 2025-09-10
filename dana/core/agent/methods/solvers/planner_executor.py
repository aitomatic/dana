from typing import Any
from collections.abc import Callable

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.workflow.workflow_system import WorkflowInstance
from .base import BaseSolverMixin


class PlannerExecutorSolverMixin(BaseSolverMixin):
    """
    Planner–Executor that prefers KNOWN WORKFLOWS and attaches RESOURCE PACKS.

    How it works (sync, single call):
      1) Attach a ResourcePack early (if a ResourceIndex is provided).
      2) If input is a WorkflowInstance -> execute it directly.
      3) Else try to MATCH a known workflow from a WorkflowCatalog for the goal text.
      4) If no direct match, draft a plan (steps). For each step:
           - Try to EXPAND the step into a known workflow from the catalog.
           - If found, execute it; else treat as a simple "action" (no-op or sandbox hook).
      5) Return deliverable + telemetry + updated artifacts/state.

    Pass these (optionally) via kwargs or set them as attributes on self:
      - workflow_catalog: object with .match(text, entities)->(score, WorkflowInstance|None)
                                      and .expand_step(step_text, entities)->WorkflowInstance|None
      - resource_index:   object with .pack(entities)->dict (docs/kb/specs)
    """

    MIXIN_NAME = "planner_executor"

    # ---------------------------
    # Public entry point
    # ---------------------------
    def plan_sync(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        **kwargs: Any,
    ) -> WorkflowInstance | None:
        """Implementation of plan functionality."""
        if isinstance(problem_or_workflow, str):
            # Create new workflow for string problem
            print("🏗️  PLANNING - Creating new workflow for string problem")
            workflow = self._create_new_workflow(problem_or_workflow, artifacts=artifacts, sandbox_context=sandbox_context, **kwargs)
            return workflow
        else:
            # Use existing workflow
            print(f"♻️  PLANNING - Reusing existing workflow: {type(problem_or_workflow).__name__}")
            return problem_or_workflow

    def _create_new_workflow(
        self, problem: str, artifacts: dict[str, Any] | None = None, sandbox_context: SandboxContext | None = None, **kwargs
    ) -> WorkflowInstance:
        """Create a new workflow for a string problem using auto strategy selection."""
        from dana.core.workflow.workflow_system import WorkflowInstance

        print("🎲 STRATEGY SELECTION - Auto-selecting strategy for problem")
        workflow = WorkflowInstance.create_with_strategy(
            problem=problem, strategy_type="auto", agent_instance=self, artifacts=artifacts, sandbox_context=sandbox_context, **kwargs
        )
        print(f"✅ WORKFLOW CREATED - {type(workflow).__name__}")

        return workflow

    def solve_sync(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        *,
        dry_run: bool = False,
        max_steps: int = 8,
        known_match_threshold: float = 0.75,
        force_replan: bool = False,
        delegate: Callable[[str, dict[str, Any]], Any] | None = None,  # for subgoals if you want
        workflow_catalog: Any | None = None,
        resource_index: Any | None = None,
        **kwargs: Any,
    ) -> Any:
        # Check for conversation termination commands first
        if isinstance(problem_or_workflow, str) and self._is_conversation_termination(problem_or_workflow):
            self._log_solver_phase("PLANNER", f"Conversation termination command detected: '{problem_or_workflow}'")
            return "Goodbye! Have a great day!"

        print(f"🔍 [SOLVER] Starting solve_sync for: {problem_or_workflow}")
        artifacts = artifacts or {}

        # Create sandbox context if none provided
        if sandbox_context is None:
            sandbox_context = SandboxContext()

        st = self._initialize_solver_state(artifacts, "_planner")
        entities = self._extract_entities(artifacts)

        # Check recursion depth to prevent infinite loops
        recursion_depth = st.get("recursion_depth", 0)
        print(f"🔄 [SOLVER] Recursion depth: {recursion_depth}")
        if recursion_depth > 3:  # Limit recursion depth
            print("⚠️ [SOLVER] Recursion limit reached, returning early")
            return self._create_answer_response(
                "planner",
                artifacts,
                "recursion_limit",
                goal=str(problem_or_workflow),
                plan=[],
                results=[],
                deliverable=f"Recursion limit reached for: {problem_or_workflow}",
                steps=0,
            )
        st["recursion_depth"] = recursion_depth + 1

        # Inject dependencies using base class method
        wc, ri, _ = self._inject_dependencies(workflow_catalog=workflow_catalog, resource_index=resource_index)

        # (1) Attach resource pack EARLY
        self._attach_resource_pack(ri, entities, artifacts)

        # (2) Direct workflow execution
        print("🔍 [SOLVER] Checking for direct workflow execution...")
        direct_result = self._handle_direct_workflow_execution(problem_or_workflow, sandbox_context, artifacts, "workflow")
        if direct_result:
            print("✅ [SOLVER] Direct workflow execution found, returning result")
            return direct_result

        # (3) Goal string → try KNOWN WORKFLOW match
        goal: str = str(problem_or_workflow).strip()
        print(f"🎯 [SOLVER] Processing goal: '{goal}'")
        if not goal:
            print("❌ [SOLVER] Empty goal, asking for clarification")
            return self._create_ask_response("Please provide a goal to plan (one sentence is fine).")

        # Use base class method for workflow matching
        print("🔍 [SOLVER] Checking for known workflow match...")
        score, wf = self._match_known_workflow(goal, entities, wc, known_match_threshold)
        if wf is not None:
            print(f"✅ [SOLVER] Found known workflow (score: {score}), executing...")
            result = self._run_workflow_instance(wf, sandbox_context)
            st.update(
                {
                    "mode": "planner",
                    "goal": goal,
                    "phase": "delivered",
                    "used_known_workflow": True,
                    "known_match_score": float(score),
                    "known_workflow_name": getattr(wf, "name", "<unknown>"),
                    "last_result": result,
                }
            )
            return self._create_answer_response(
                "planner",
                artifacts,
                "known_workflow",
                goal=goal,
                plan=[f"(known workflow) {getattr(wf, 'name', 'workflow')}"],
                results=[result],
                deliverable=self._summarize(goal, [{"type": "known", "wf": getattr(wf, "name", "workflow")}], [result], dry_run),
                score=float(score),
            )

        # (4) No direct match → PLAN
        print("📋 [SOLVER] No known workflow found, drafting plan...")
        if force_replan or "plan_struct" not in st or st.get("goal") != goal:
            raw_steps = self._draft_plan(goal, max_steps=max_steps, sandbox_context=sandbox_context)
            print(f"📋 [SOLVER] Drafted {len(raw_steps)} raw steps: {raw_steps}")
            plan_struct = self._structure_plan(raw_steps)  # [{"type": "action"|"subgoal", ...}]
            print(f"📋 [SOLVER] Structured plan: {plan_struct}")
            st.update({"goal": goal, "plan_struct": plan_struct, "phase": "planned"})

        plan = st["plan_struct"]

        # (5) EXECUTE plan; try to EXPAND steps via catalog if available
        if st.get("phase") == "planned":
            print(f"🚀 [SOLVER] Executing plan with {len(plan)} steps...")
            results: list[dict[str, Any]] = []
            exec_log: list[str] = []
            for i, step in enumerate(plan):
                print(f"🔄 [SOLVER] Executing step {i + 1}/{len(plan)}: {step}")
                # Expand to known workflow if possible
                wf = None
                if wc is not None:
                    try:
                        wf = wc.expand_step(step.get("do") or step.get("goal") or "", entities)  # type: ignore[attr-defined]
                    except Exception:
                        wf = None

                if wf is not None:
                    print(f"🔧 [SOLVER] Step {i + 1}: Using workflow {getattr(wf, 'name', 'workflow')}")
                    res = self._run_workflow_instance(wf, sandbox_context)
                    results.append({"index": i, "status": "ok" if res.get("status") == "ok" else "error", "step": step, "result": res})
                    exec_log.append(f"[wf] step {i}: {getattr(wf, 'name', 'workflow')} -> {res.get('status')}")
                    continue

                # Fallback to plain action/subgoal execution
                if step["type"] == "action":
                    print(f"⚡ [SOLVER] Step {i + 1}: Executing action '{step['do']}'")
                    res = self._exec_action(step["do"], sandbox_context, dry_run)
                    print(f"✅ [SOLVER] Step {i + 1} result: {res.get('status', 'unknown')}")
                    results.append({"index": i, "status": res["status"], "step": step, "result": res})
                    exec_log.append(f"[action] step {i}: {step['do']} -> {res['status']}")
                else:  # "subgoal"
                    sub_goal = step["goal"]
                    if delegate:
                        out = delegate(sub_goal, {"parent_goal": goal})
                        status = "ok" if out and out.get("type") != "error" else "error"
                        results.append({"index": i, "status": status, "step": step, "result": out})
                        exec_log.append(f"[delegate] step {i}: {sub_goal} -> {status}")
                    else:
                        # Lightweight recursive call (no deep state sharing)
                        child_artifacts = {"_entities": entities}
                        # Pass recursion depth to prevent infinite loops
                        child_artifacts["_planner"] = {"recursion_depth": st.get("recursion_depth", 0)}
                        out = self.solve_sync(
                            sub_goal,
                            artifacts=child_artifacts,
                            sandbox_context=sandbox_context,
                            dry_run=dry_run,
                            max_steps=max_steps,
                            known_match_threshold=known_match_threshold,
                            workflow_catalog=wc,
                            resource_index=ri,
                        )
                        status = "ok" if out and out.get("type") != "error" else "error"
                        results.append({"index": i, "status": status, "step": step, "result": out})
                        exec_log.append(f"[subgoal] step {i}: {sub_goal} -> {status}")

            st.update({"results": results, "exec_log": exec_log, "phase": "executed"})

        # (6) DELIVER
        deliverable = self._summarize(goal, plan, st.get("results", []), dry_run=dry_run)
        st["deliverable"] = deliverable
        st["phase"] = "delivered"

        # For planning tasks, create a comprehensive summary
        results = st.get("results", [])
        print(f"📊 [SOLVER] Final results: {len(results)} results")
        if len(results) > 0:
            # For planning tasks, create a comprehensive summary instead of just the first message
            if "plan" in goal.lower() or "trip" in goal.lower() or "itinerary" in goal.lower():
                print("💬 [SOLVER] Creating comprehensive planning summary...")
                return self._create_planning_summary(goal, plan, results)
            else:
                # For non-planning tasks, return the first successful result message
                for result in results:
                    if result.get("status") == "ok" and "message" in result.get("result", {}):
                        print(f"💬 [SOLVER] Returning message: {result['result']['message'][:100]}...")
                        return result["result"]["message"]

        return self._create_answer_response(
            "planner",
            artifacts,
            "plan+expand",
            goal=goal,
            plan=plan,
            results=st.get("results", []),
            deliverable=deliverable,
            steps=len(plan),
        )

    # ---------------------------
    # Helpers
    # ---------------------------
    def _draft_plan(self, goal: str, max_steps: int = 8, sandbox_context: SandboxContext | None = None) -> list[str]:
        """
        Generate a plan using LLM - NO FALLBACKS to see errors clearly.
        """
        # Try to get LLM resource for planning
        if sandbox_context is not None:
            try:
                # Try to get LLM resource from sandbox context
                llm_resource = sandbox_context.get_resource("system_llm")
                if llm_resource is not None:
                    return self._llm_draft_plan(goal, max_steps, llm_resource)
            except KeyError:
                pass

        # Try to get LLM resource from agent if available
        if hasattr(self, "get_llm_resource") and sandbox_context is not None:
            llm_resource = self.get_llm_resource(sandbox_context)
            if llm_resource is not None:
                return self._llm_draft_plan(goal, max_steps, llm_resource)

        # Try direct access as fallback
        if hasattr(self, "_llm_resource") and self._llm_resource is not None:
            return self._llm_draft_plan(goal, max_steps, self._llm_resource)

        # No fallback - raise error to see what's wrong
        raise RuntimeError(f"No LLM resource available for planning. Goal: {goal}")

    def _llm_draft_plan(self, goal: str, max_steps: int, llm_resource: Any = None) -> list[str]:
        """Generate plan using LLM - NO FALLBACKS to see errors clearly."""
        self._log_solver_phase("LLM-PLAN", f"Generating plan for: '{goal}'", "🤖")

        if llm_resource is None:
            raise RuntimeError(f"No LLM resource provided for planning. Goal: {goal}")

        # Get conversation context from timeline
        conversation_context = self._get_conversation_context(max_turns=3)

        prompt = f"""Create a step-by-step plan to achieve this goal: "{goal}"

Requirements:
- Maximum {max_steps} steps
- Each step should be actionable and specific
- Steps should be in logical order
- Use imperative mood (e.g., "Analyze the problem", "Implement solution")
{conversation_context}

Format: Return only the steps, one per line, without numbering or bullets."""

        try:
            # Create request directly with the provided LLM resource
            from dana.common.types import BaseRequest

            request = BaseRequest(
                arguments={
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an AI planning assistant. Create step-by-step plans to achieve goals. Be specific and actionable."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )

            response = llm_resource.query_sync(request)

            if response is None:
                raise RuntimeError(f"LLM query failed for goal: {goal}")


            # Extract text from response
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'content'):
                # Handle BaseResponse with content field
                content = response.content
                if isinstance(content, dict):
                    # Handle OpenAI-style response format
                    if 'choices' in content and len(content['choices']) > 0:
                        choice = content['choices'][0]
                        if 'message' in choice and 'content' in choice['message']:
                            response_text = choice['message']['content']
                        else:
                            response_text = str(choice)
                    else:
                        response_text = str(content)
                else:
                    response_text = str(content)
            elif isinstance(response, str):
                response_text = response
            elif isinstance(response, dict):
                # Handle dictionary response - look for common text fields
                if 'text' in response:
                    response_text = response['text']
                elif 'content' in response:
                    response_text = response['content']
                elif 'response' in response:
                    response_text = response['response']
                elif 'message' in response:
                    response_text = response['message']
                else:
                    # If it's a dict but no obvious text field, convert to string
                    response_text = str(response)
            else:
                response_text = str(response)

        except Exception as e:
            raise RuntimeError(f"LLM query failed for goal: {goal}. Error: {str(e)}")

        steps = [step.strip() for step in response_text.split("\n") if step.strip()]
        self._log_solver_phase("LLM-PLAN", f"LLM returned {len(steps)} steps: {steps}", "🤖")

        if not steps:
            raise RuntimeError(f"LLM returned empty plan for goal: {goal}")

        return steps[:max_steps]

    def _heuristic_draft_plan(self, goal: str, max_steps: int) -> list[str]:
        """Fallback heuristic planning approach."""
        tokens = [s.strip(" -*\t") for s in _split_on_delims(goal)]
        user_steps = [s for s in tokens if len(s.split()) > 3]
        if user_steps:
            return user_steps[:max_steps]
        # Create simple, non-recursive steps that can be executed directly
        return [
            f"Analyze the request: {goal}",
            f"Provide a helpful response for: {goal}",
        ][:max_steps]

    def _structure_plan(self, steps: list[str]) -> list[dict[str, Any]]:
        """
        Enhanced classification of steps into actions vs subgoals.
        """
        # More comprehensive verb classification
        subgoal_verbs = {
            "identify",
            "solve",
            "research",
            "draft",
            "design",
            "investigate",
            "analyze",
            "evaluate",
            "assess",
            "examine",
            "explore",
            "discover",
            "plan",
            "strategize",
            "brainstorm",
            "conceptualize",
            "formulate",
        }
        action_verbs = {
            "implement",
            "execute",
            "run",
            "perform",
            "apply",
            "deploy",
            "create",
            "build",
            "construct",
            "generate",
            "produce",
            "develop",
            "test",
            "validate",
            "verify",
            "check",
            "confirm",
            "review",
        }

        plan: list[dict[str, Any]] = []
        for s in steps:
            lower = s.lower()
            first_word = lower.split()[0] if lower.split() else ""

            # Check for explicit subgoal indicators
            if any(indicator in lower for indicator in ["subproblem", "subgoal", "break down", "decompose"]):
                plan.append({"type": "action", "do": s})  # Treat as action to avoid recursion
            # Check for subgoal verbs - but avoid recursion by treating as actions
            elif first_word in subgoal_verbs:
                plan.append({"type": "action", "do": s})  # Treat as action to avoid recursion
            # Check for action verbs
            elif first_word in action_verbs:
                plan.append({"type": "action", "do": s})
            # Default classification - treat everything as actions to avoid recursion
            else:
                plan.append({"type": "action", "do": s})

        return plan

    def _exec_action(self, action: str, sandbox_context: SandboxContext | None, dry_run: bool) -> dict[str, Any]:
        """Execute an action using LLM - NO FALLBACKS to see errors clearly."""
        self._log_solver_phase("LLM-ACTION", f"Executing action: '{action}'", "🤖")
        if dry_run:
            return {"status": "ok (dry-run)", "action": action, "message": "Action would be executed in real mode"}

        # Use LLM to execute the action
        llm_resource = None
        if sandbox_context is not None:
            try:
                llm_resource = sandbox_context.get_resource("system_llm")
            except KeyError:
                pass

        if llm_resource is None:
            raise RuntimeError(f"No LLM resource available for action execution. Action: {action}")

        # Get conversation context from timeline
        conversation_context = self._get_conversation_context(max_turns=5)

        # Create a prompt for the LLM to execute the action
        prompt = f"""Execute this action: "{action}"

Provide a helpful, direct response that accomplishes what the user is asking for.
Be concise but informative. If it's a question, answer it directly.
If it's a request for help, provide useful guidance.
{conversation_context}

Response:"""

        try:
            # Create request directly with the provided LLM resource
            from dana.common.types import BaseRequest

            request = BaseRequest(
                arguments={
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an AI assistant that executes actions and provides helpful responses. Be direct and helpful."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )

            response = llm_resource.query_sync(request)

            if response is None:
                raise RuntimeError(f"LLM query failed for action: {action}")

            # Extract text from response (same logic as in _llm_draft_plan)
            if hasattr(response, 'content'):
                content = response.content
                if isinstance(content, dict):
                    if 'choices' in content and len(content['choices']) > 0:
                        choice = content['choices'][0]
                        if 'message' in choice and 'content' in choice['message']:
                            response_text = choice['message']['content']
                        else:
                            response_text = str(choice)
                    else:
                        response_text = str(content)
                else:
                    response_text = str(content)
            elif hasattr(response, 'text'):
                response_text = response.text
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)

            self._log_solver_phase("LLM-ACTION", f"LLM response: {response_text[:100]}...", "🤖")
            return {"status": "ok", "action": action, "message": response_text}
        except Exception as e:
            self._log_solver_phase("LLM-ACTION", f"Error: {e}", "❌")
            raise RuntimeError(f"LLM failed to execute action '{action}': {e}")

    def _handle_math_action(self, action: str) -> dict[str, Any]:
        """Handle math problems safely."""
        try:
            import re

            # Extract numbers and operators
            numbers = re.findall(r"\d+\.?\d*", action)
            if len(numbers) >= 2:
                # Try to evaluate simple expressions
                if "+" in action or "plus" in action.lower():
                    result = sum(float(n) for n in numbers)
                    return {"status": "ok", "action": action, "message": f"The answer is {result}"}
                elif "-" in action or "minus" in action.lower():
                    if len(numbers) == 2:
                        result = float(numbers[0]) - float(numbers[1])
                        return {"status": "ok", "action": action, "message": f"The answer is {result}"}
                elif "*" in action or "times" in action.lower() or "×" in action:
                    result = 1
                    for n in numbers:
                        result *= float(n)
                    return {"status": "ok", "action": action, "message": f"The answer is {result}"}
                elif "/" in action or "divided" in action.lower() or "÷" in action:
                    if len(numbers) == 2:
                        result = float(numbers[0]) / float(numbers[1])
                        return {"status": "ok", "action": action, "message": f"The answer is {result}"}

            # If we can't solve it directly, provide helpful guidance
            return {
                "status": "ok",
                "action": action,
                "message": f"I can see you're asking about a math problem: '{action}'. I can help with basic arithmetic (addition, subtraction, multiplication, division). Could you rephrase the problem in a simpler format? For example: 'What is 5 + 3?' or 'Calculate 10 * 7'.",
            }

        except Exception:
            return {
                "status": "ok",
                "action": action,
                "message": f"I can see you're asking about a math problem: '{action}'. I can help with basic arithmetic. Could you rephrase it in a simpler format? For example: 'What is 5 + 3?' or 'Calculate 10 * 7'.",
            }

    def _try_execute_action_patterns(self, action: str, sandbox_context: SandboxContext) -> dict[str, Any] | None:
        """Try to execute common action patterns."""
        action_lower = action.lower()

        # File operations
        if any(cmd in action_lower for cmd in ["create file", "write file", "save file"]):
            return self._handle_file_action(action, sandbox_context, "write")
        elif any(cmd in action_lower for cmd in ["read file", "load file", "open file"]):
            return self._handle_file_action(action, sandbox_context, "read")

        # API calls
        elif any(cmd in action_lower for cmd in ["call api", "request", "fetch", "get data"]):
            return self._handle_api_action(action, sandbox_context)

        # Database operations
        elif any(cmd in action_lower for cmd in ["query", "database", "sql", "insert", "update"]):
            return self._handle_db_action(action, sandbox_context)

        # System commands
        elif any(cmd in action_lower for cmd in ["run command", "execute", "shell", "terminal"]):
            return self._handle_system_action(action, sandbox_context)

        return None

    def _handle_file_action(self, action: str, sandbox_context: SandboxContext, operation: str) -> dict[str, Any]:
        """Handle file-related actions."""
        sandbox_context.record_event("planner.file_action", {"operation": operation, "action": action})
        return {"status": "ok", "action": action, "type": "file_operation", "operation": operation}

    def _handle_api_action(self, action: str, sandbox_context: SandboxContext) -> dict[str, Any]:
        """Handle API-related actions."""
        sandbox_context.record_event("planner.api_action", {"action": action})
        return {"status": "ok", "action": action, "type": "api_call"}

    def _handle_db_action(self, action: str, sandbox_context: SandboxContext) -> dict[str, Any]:
        """Handle database-related actions."""
        sandbox_context.record_event("planner.db_action", {"action": action})
        return {"status": "ok", "action": action, "type": "database_operation"}

    def _handle_system_action(self, action: str, sandbox_context: SandboxContext) -> dict[str, Any]:
        """Handle system command actions."""
        sandbox_context.record_event("planner.system_action", {"action": action})
        return {"status": "ok", "action": action, "type": "system_command"}

    def _create_planning_summary(self, goal: str, plan: list[dict[str, Any]], results: list[dict[str, Any]]) -> str:
        """Create a comprehensive summary for planning tasks."""
        summary_parts = [f"# {goal.title()}\n"]

        # Add overview
        summary_parts.append("## Overview")
        summary_parts.append(f"I've created a comprehensive plan with {len(plan)} steps to help you {goal.lower()}.\n")

        # Add each step with its result
        summary_parts.append("## Detailed Plan")
        for i, (step, result) in enumerate(zip(plan, results, strict=True), 1):
            step_desc = step.get("do", f"Step {i}")
            summary_parts.append(f"### Step {i}: {step_desc}")

            if result.get("status") == "ok" and "message" in result.get("result", {}):
                message = result["result"]["message"]
                # Clean up the message and format it nicely
                if len(message) > 200:
                    message = message[:200] + "..."
                summary_parts.append(f"{message}\n")
            else:
                summary_parts.append("✅ Completed\n")

        # Add next steps
        summary_parts.append("## Next Steps")
        summary_parts.append("Review this plan and let me know if you'd like me to:")
        summary_parts.append("- Modify any specific steps")
        summary_parts.append("- Add more details to particular areas")
        summary_parts.append("- Help you execute any of these steps")
        summary_parts.append("- Create a more detailed itinerary")

        return "\n".join(summary_parts)

    def _summarize(self, goal: str, plan: list[dict[str, Any]], results: list[dict[str, Any]], dry_run: bool) -> str:
        total = len(plan)
        ok = sum(1 for r in results if str(r.get("status", "")).startswith("ok"))
        failed = sum(1 for r in results if str(r.get("status", "")).startswith("error"))
        mode = "DRY RUN" if dry_run else "EXECUTED"
        return (
            f"{mode} summary for: {goal}\n"
            f"- Steps: {total}, Completed: {ok}, Failed: {failed}\n"
            f"- See results for per-step outputs. Refine plan or export deliverable next."
        )


# ---------------------------
# Local utility
# ---------------------------
def _split_on_delims(text: str) -> list[str]:
    for d in ["\n", ".", ";", "•", "·", "-", "—", "->", "→", "|", "/"]:
        text = text.replace(d, "|")
    return [p for p in (t.strip() for t in text.split("|")) if p]
