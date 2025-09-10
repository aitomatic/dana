from __future__ import annotations

from typing import Any

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.workflow.workflow_system import WorkflowInstance
from .base import BaseSolverMixin


class ReactiveSupportSolverMixin(BaseSolverMixin):
    """
    Conversational, case-based troubleshooting mixin.

    Behavior (single-call, synchronous):
      1) Attach ResourcePack early (if ResourceIndex provided).
      2) If input is a WorkflowInstance -> execute it directly (diagnostic run).
      3) Else: try SignatureMatcher to short-circuit to a known issue.
      4) Else: if known diagnostic workflow matches, execute it.
      5) Else: collect missing artifacts; if not enough, ASK for them.
      6) Else: draft an actionable checklist and return ANSWER.

    Optional dependencies (pass via kwargs or set as attributes on self):
      - signature_matcher: object with .match(text, entities)->(score:float, match:dict|None)
      - workflow_catalog:  object with .match(text, entities)->(score:float, WorkflowInstance|None)
      - resource_index:    object with .pack(entities)->dict (docs/kb/specs)
    """

    MIXIN_NAME = "reactive_support"

    def solve_sync(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        *,
        # knobs
        known_match_threshold: float = 0.75,
        min_required: int = 1,
        required_artifacts: list[str] | None = None,
        # delegation / deps
        signature_matcher: Any | None = None,
        workflow_catalog: Any | None = None,
        resource_index: Any | None = None,
        **kwargs: Any,
    ) -> Any:
        # Check for conversation termination commands first
        if isinstance(problem_or_workflow, str) and self._is_conversation_termination(problem_or_workflow):
            self._log_solver_phase("REACTIVE-SUPPORT", f"Conversation termination command detected: '{problem_or_workflow}'")
            return "Goodbye! Have a great day!"

        print(f"🔧 [REACTIVE-SUPPORT] Starting solve_sync for: '{problem_or_workflow}'")
        artifacts = artifacts or {}
        assert artifacts is not None
        st = self._initialize_solver_state(artifacts, "_support")
        entities = self._extract_entities(artifacts)
        print(f"🔧 [REACTIVE-SUPPORT] Extracted entities: {entities}")

        # Inject dependencies using base class method
        wc, ri, sig = self._inject_dependencies(
            signature_matcher=signature_matcher, workflow_catalog=workflow_catalog, resource_index=resource_index
        )
        print(
            f"🔧 [REACTIVE-SUPPORT] Dependencies: workflow_catalog={wc is not None}, resource_index={ri is not None}, signature_matcher={sig is not None}"
        )

        # 1) Attach resources early
        self._attach_resource_pack(ri, entities, artifacts)

        # 2) Direct workflow execution (diagnostic workflow already chosen upstream)
        print("🔧 [REACTIVE-SUPPORT] Checking for direct workflow execution...")
        direct_result = self._handle_direct_workflow_execution(problem_or_workflow, sandbox_context, artifacts, "support")
        if direct_result:
            print(f"🔧 [REACTIVE-SUPPORT] Found direct workflow result: {direct_result}")
            return direct_result

        # 3) Interpret as a symptom/issue description
        message: str = str(problem_or_workflow).strip()
        print(f"🔧 [REACTIVE-SUPPORT] Processing message: '{message}'")
        if not message:
            print("🔧 [REACTIVE-SUPPORT] Empty message, asking for description")
            return self._create_ask_response("Could you describe the issue briefly (one sentence is fine)?")

        # 4) Signature-based short-circuit (known issue patterns)
        print("🔧 [REACTIVE-SUPPORT] Checking signature matching...")
        sig_match = None
        sig_score = 0.0
        if sig is not None:
            try:
                sig_score, sig_match = sig.match(message, entities)  # type: ignore[attr-defined]
                print(f"🔧 [REACTIVE-SUPPORT] Signature match score: {sig_score}, match: {sig_match}")
            except Exception as e:
                print(f"🔧 [REACTIVE-SUPPORT] Signature matching failed: {e}")
                sig_score, sig_match = 0.0, None
            if sig_match and sig_score >= known_match_threshold:
                print("🔧 [REACTIVE-SUPPORT] Found signature match, checking for LLM-powered workflow...")

                # Try to get the corresponding workflow and execute it with LLM
                if wc is not None and hasattr(wc, "get_workflow"):
                    workflow = wc.get_workflow(sig_match.workflow_id)
                    if (
                        workflow
                        and hasattr(workflow, "execute_with_llm")
                        and hasattr(self, "_llm_resource")
                        and self._llm_resource is not None
                    ):
                        print("🔧 [REACTIVE-SUPPORT] Executing LLM-powered workflow for signature match...")
                        try:
                            llm_result = workflow.execute_with_llm(message, artifacts, self._llm_resource)
                            print(f"🔧 [REACTIVE-SUPPORT] LLM workflow result: {llm_result}")

                            st.update(
                                {
                                    "mode": "support",
                                    "phase": "delivered",
                                    "used_llm_workflow": True,
                                    "signature_score": float(sig_score),
                                    "signature_id": sig_match.id,
                                    "llm_result": llm_result,
                                }
                            )

                            # Format the LLM result as a structured response
                            diagnosis = llm_result.get("diagnosis", sig_match.title or "Issue diagnosed")
                            checklist = llm_result.get("checklist", [])
                            solution = llm_result.get("solution", "Follow diagnostic steps")

                            return self._create_answer_response(
                                "support",
                                artifacts,
                                "llm_signature_workflow",
                                diagnosis=diagnosis,
                                checklist=checklist,
                                solution=solution,
                                score=float(sig_score),
                            )
                        except Exception as e:
                            print(f"⚠️ [REACTIVE-SUPPORT] LLM workflow failed: {e}")
                            # Fall back to regular signature response

                # Fallback to regular signature response
                print("🔧 [REACTIVE-SUPPORT] Using fallback signature response")
                checklist = self._checklist_from_signature(sig_match, resources=artifacts.get("_resources", {}))
                st.update(
                    {
                        "mode": "support",
                        "phase": "delivered",
                        "used_signature": True,
                        "signature_score": float(sig_score),
                        "signature_id": sig_match.id,
                    }
                )
                return {
                    "type": "answer",
                    "mode": "support",
                    "diagnosis": sig_match.title or "Matched known issue",
                    "checklist": checklist,
                    "telemetry": {"mixin": self.MIXIN_NAME, "selected": "signature", "score": float(sig_score)},
                    "artifacts": artifacts,
                }

        # 5) Known diagnostic workflow (catalog match)
        print("🔧 [REACTIVE-SUPPORT] Checking for known diagnostic workflow...")
        score, wf = self._match_known_workflow(f"diagnose: {message}", entities, wc, known_match_threshold)
        if wf is not None:
            print(f"🔧 [REACTIVE-SUPPORT] Found known workflow: {wf}, score: {score}")

            # Try LLM-powered workflow execution if available
            if hasattr(wf, "execute_with_llm") and hasattr(self, "_llm_resource") and self._llm_resource is not None:
                print("🔧 [REACTIVE-SUPPORT] Executing LLM-powered workflow...")
                try:
                    llm_result = wf.execute_with_llm(message, artifacts, self._llm_resource)
                    print(f"🔧 [REACTIVE-SUPPORT] LLM workflow result: {llm_result}")

                    st.update(
                        {
                            "mode": "support",
                            "phase": "delivered",
                            "used_llm_workflow": True,
                            "known_match_score": float(score),
                            "known_workflow_name": getattr(wf, "name", "<unknown>"),
                            "llm_result": llm_result,
                        }
                    )

                    # Format the LLM result as a structured response
                    diagnosis = llm_result.get("diagnosis", "Issue diagnosed")
                    checklist = llm_result.get("checklist", [])
                    solution = llm_result.get("solution", "Follow diagnostic steps")

                    return self._create_answer_response(
                        "support",
                        artifacts,
                        "llm_workflow",
                        diagnosis=diagnosis,
                        checklist=checklist,
                        solution=solution,
                        score=float(score),
                    )
                except Exception as e:
                    print(f"⚠️ [REACTIVE-SUPPORT] LLM workflow failed: {e}")
                    # Fall back to regular workflow execution

            # Regular workflow execution (fallback)
            result = self._run_workflow_instance(wf, sandbox_context)
            st.update(
                {
                    "mode": "support",
                    "phase": "delivered",
                    "used_known_workflow": True,
                    "known_match_score": float(score),
                    "known_workflow_name": getattr(wf, "name", "<unknown>"),
                    "last_result": result,
                }
            )
            return self._create_answer_response(
                "support",
                artifacts,
                "known_workflow",
                diagnosis=f"Ran known diagnostic: {getattr(wf, 'name', 'workflow')}",
                results=[result],
                checklist=self._checklist_from_result(result, artifacts.get("_resources", {})),
                score=float(score),
            )

        # 6) Artifact sufficiency check → ASK if missing (but be more helpful)
        print("🔧 [REACTIVE-SUPPORT] Checking artifact sufficiency...")
        required_list = required_artifacts or [
            "error messages or logs",
            "system configuration",
            "recent changes made",
            "expected vs actual behavior",
        ]
        missing = self._infer_missing(required_list, message, artifacts)
        print(f"🔧 [REACTIVE-SUPPORT] Required: {required_list}, Missing: {missing}")

        # Be more helpful: if we have at least 2 out of 4 pieces of information, provide analysis
        # Or if we have a signature match, be more lenient
        # Or if user indicates they've provided all available information
        has_signature_match = sig_match and sig_score >= known_match_threshold
        has_sufficient_info = len(missing) <= 2  # Allow up to 2 missing pieces
        user_says_that_is_all = self._user_indicates_no_more_info(message)

        if len(missing) > 0 and len(missing) >= min_required and not (has_signature_match or has_sufficient_info or user_says_that_is_all):
            print("🔧 [REACTIVE-SUPPORT] Missing artifacts, asking for more info")
            st.update({"phase": "collect", "missing": missing})
            ask = self._clarifying_question(missing, entities, artifacts.get("_resources", {}))
            return self._create_ask_response(ask, missing=missing, selected="collect")
        elif len(missing) > 0:
            reason = "signature_match" if has_signature_match else "sufficient_info" if has_sufficient_info else "user_says_that_is_all"
            print(f"🔧 [REACTIVE-SUPPORT] Some artifacts missing but proceeding with analysis (reason={reason})")

        # 7) Generic analysis → use LLM for helpful response
        print("🔧 [REACTIVE-SUPPORT] Starting generic analysis with LLM...")
        st["phase"] = "analyze"

        # Try to use LLM for a helpful response
        if hasattr(self, "_llm_resource") and self._llm_resource is not None:
            print("🔧 [REACTIVE-SUPPORT] LLM resource available, generating response...")
            try:
                llm_response = self._generate_llm_response(message, artifacts)
                print(f"🔧 [REACTIVE-SUPPORT] LLM response generated: {llm_response[:100]}...")
                st.update({"phase": "delivered", "llm_response": llm_response})
                return llm_response  # Return the LLM response directly as a string
            except Exception as e:
                print(f"⚠️ [REACTIVE-SUPPORT] LLM failed: {e}")
        else:
            print("🔧 [REACTIVE-SUPPORT] No LLM resource available")

        # Fallback to original analysis
        print("🔧 [REACTIVE-SUPPORT] Falling back to original analysis...")
        preliminary = self._preliminary_analysis(message, artifacts)
        checklist = self._draft_checklist(message, entities, artifacts.get("_resources", {}), preliminary)

        st.update({"phase": "delivered", "last_checklist": checklist, "preliminary": preliminary})
        return self._create_answer_response(
            "support",
            artifacts,
            "generic",
            diagnosis=preliminary.get("summary", "Preliminary diagnosis"),
            checklist=checklist,
        )

    # ---------------------------
    # Helpers
    # ---------------------------

    def _generate_llm_response(self, message: str, artifacts: dict[str, Any]) -> str:
        """Generate a helpful LLM response for general conversation."""
        self._log_solver_phase("REACTIVE-SUPPORT-LLM", f"Generating response for: '{message}'", "🤖")

        # Check if user indicates they've provided all available information
        user_says_that_is_all = self._user_indicates_no_more_info(message)

        if user_says_that_is_all:
            prompt = f"""You are a helpful technical support assistant. The user said: "{message}"

The user has indicated they've provided all available information. Be understanding and helpful - provide the best advice you can with the information given.
Don't ask for more information. Instead, give practical next steps and solutions based on what you know.
Be empathetic and acknowledge that you understand they've shared what they can.

Response:"""
        else:
            prompt = f"""You are a helpful technical support assistant. The user said: "{message}"

Provide a helpful, direct response that addresses what the user is asking for.
Be conversational and friendly. If this is a follow-up question, reference what was discussed earlier and provide next steps.
If it's a question, answer it directly with actionable advice.
If it's a greeting, respond appropriately.
If it's a request for help, provide useful guidance based on the conversation context.

Response:"""

        response_text = self._generate_llm_response_with_context(
            prompt=prompt,
            system_prompt="You are a helpful technical support assistant. Provide specific, actionable advice based on the conversation context. Be practical and solution-oriented.",
        )

        if response_text is None:
            return "I don't have access to an LLM resource to help with this question."

        self._log_solver_phase("REACTIVE-SUPPORT-LLM", f"Extracted response text: {response_text[:100]}...", "🤖")
        return response_text

    def _infer_missing(self, required_list: list[str], message: str, artifacts: dict[str, Any]) -> list[str]:
        """
        Heuristic: consider something 'present' if artifacts carry a plausible field,
        the message contains config-like tokens (=, :, {}, []), or it was mentioned in conversation history.
        """
        present_tokens = any(t in message for t in ("=", ":", "{", "}", "[", "]"))
        provided = set(k.lower() for k in artifacts.keys())

        # Build conversation text for analysis
        conversation_text = message.lower()

        # Get conversation context from agent state timeline
        conversation_context = self._get_conversation_context(max_turns=3)
        if conversation_context:
            conversation_text += " " + conversation_context.lower()

        missing: list[str] = []
        for need in required_list:
            key = self._canonical_key(need)
            if key in provided or present_tokens:
                continue

            # Check if this type of information was mentioned in conversation
            if self._mentioned_in_conversation(need, conversation_text):
                continue

            missing.append(need)
        return missing

    def _mentioned_in_conversation(self, need: str, conversation_text: str) -> bool:
        """Check if the required information type was mentioned in conversation."""
        need_lower = need.lower()

        # Define comprehensive keywords that indicate each type of information
        if "error" in need_lower or "log" in need_lower:
            error_keywords = [
                "error",
                "log",
                "exception",
                "failed",
                "timeout",
                "crash",
                "bug",
                "issue",
                "problem",
                "slow",
                "lagging",
                "hanging",
                "freezing",
                "stuck",
                "not working",
                "failing",
                "svchost",
                "process",
                "cpu",
                "memory",
                "performance",
                "troubleshooter",
            ]
            return any(keyword in conversation_text for keyword in error_keywords)

        if "config" in need_lower or "setting" in need_lower:
            config_keywords = [
                "config",
                "setting",
                "configured",
                "setup",
                "installed",
                "version",
                "system",
                "environment",
                "8gb",
                "ram",
                "memory",
                "cpu",
                "90%",
                "task manager",
                "windows",
                "arduino",
                "uno",
                "usb",
                "cable",
                "baud",
                "9600",
                "uart",
                "serial",
                "connection",
                "pin",
            ]
            return any(keyword in conversation_text for keyword in config_keywords)

        if "change" in need_lower or "recent" in need_lower:
            change_keywords = [
                "change",
                "recent",
                "updated",
                "modified",
                "installed",
                "upgraded",
                "yesterday",
                "today",
                "before",
                "restart",
                "restarted",
                "tried",
                "attempted",
                "loopback",
                "test",
                "worked",
                "working",
            ]
            return any(keyword in conversation_text for keyword in change_keywords)

        if "behavior" in need_lower or "expected" in need_lower:
            behavior_keywords = [
                "expected",
                "behavior",
                "should",
                "normally",
                "usually",
                "working",
                "not working",
                "failing",
                "slow",
                "timeout",
                "communication",
                "failing",
                "culprit",
                "main",
                "problem",
                "issue",
            ]
            return any(keyword in conversation_text for keyword in behavior_keywords)

        return False

    def _user_indicates_no_more_info(self, message: str) -> bool:
        """Check if user indicates they've provided all available information."""
        message_lower = message.lower()

        # Phrases that indicate user has provided all available information
        no_more_info_phrases = [
            "that's all i have",
            "that is all i have",
            "that's all",
            "that is all",
            "i don't have more",
            "i don't have any more",
            "no more information",
            "nothing else",
            "that's everything",
            "that is everything",
            "i've told you everything",
            "i have told you everything",
            "no other details",
            "no additional info",
            "no more details",
            "can't provide more",
            "cannot provide more",
            "don't know more",
            "don't have more details",
            "that's all i know",
            "that is all i know",
        ]

        return any(phrase in message_lower for phrase in no_more_info_phrases)

    def _canonical_key(self, need: str) -> str:
        n = need.lower()
        if "log" in n:
            return "logs"
        if "config" in n or "setting" in n:
            return "config"
        if "dump" in n:
            return "dump"
        if "screenshot" in n or "capture" in n:
            return "screenshot"
        return n.replace(" ", "_")

    def _clarifying_question(self, missing: list[str], entities: dict[str, Any], resources: dict[str, Any]) -> str:
        lines = ["To proceed, could you share the following:"]
        for m in missing:
            lines.append(f"- {m}")
        # Optional domain hint
        if entities:
            lines.append("")
            lines.append("Tip: include any identifiers you have (e.g., product/feature/version).")
        return "\n".join(lines)

    def _preliminary_analysis(self, message: str, artifacts: dict[str, Any]) -> dict[str, Any]:
        """
        Enhanced analysis: severity, category, and urgency assessment.
        """
        msg = message.lower()

        # Enhanced severity detection
        critical_keywords = {"crash", "panic", "hang", "data loss", "corruption", "security breach", "down", "outage"}
        high_keywords = {"fail", "error", "timeout", "not working", "broken", "unresponsive", "stuck"}
        medium_keywords = {"issue", "problem", "bug", "glitch", "inconsistent", "unexpected"}

        if any(k in msg for k in critical_keywords):
            severity = "critical"
        elif any(k in msg for k in high_keywords):
            severity = "high"
        elif any(k in msg for k in medium_keywords):
            severity = "medium"
        else:
            severity = "low"

        # Enhanced category detection
        categories = {
            "configuration": ["config", "setting", "enable", "disable", "parameter", "option", "preference"],
            "connectivity": ["connect", "link", "network", "connection", "reach", "accessible", "ping"],
            "performance": ["slow", "latency", "throughput", "speed", "lag", "delay", "bottleneck"],
            "authentication": ["login", "auth", "credential", "password", "token", "permission", "access"],
            "data": ["database", "storage", "file", "record", "query", "sql", "persistence"],
            "api": ["endpoint", "request", "response", "http", "rest", "graphql", "service"],
            "deployment": ["deploy", "build", "release", "environment", "server", "container", "kubernetes"],
        }

        category = "unknown"
        for cat, keywords in categories.items():
            if any(k in msg for k in keywords):
                category = cat
                break

        # Urgency assessment
        urgency_indicators = {"urgent", "asap", "immediately", "critical", "blocking", "production"}
        urgency = "high" if any(k in msg for k in urgency_indicators) else "normal"

        # Impact assessment
        impact_keywords = {"users", "customers", "production", "live", "revenue", "business"}
        impact = "high" if any(k in msg for k in impact_keywords) else "medium"

        return {
            "severity": severity,
            "category": category,
            "urgency": urgency,
            "impact": impact,
            "summary": f"{category.title()} issue (severity: {severity}, urgency: {urgency})",
        }

    def _checklist_from_signature(self, sig_match: dict[str, Any] | Any, resources: dict[str, Any]) -> list[str]:
        """
        Turn a signature KB match into a checklist.
        Expected fields in sig_match (if available): steps, fix, refs.
        """
        # Handle both dict and SignatureMatch object
        if hasattr(sig_match, "workflow_id"):
            # This is a SignatureMatch object, get the workflow and use its checklist
            workflow_id = sig_match.workflow_id
            # For now, return a generic checklist based on the workflow type
            if "uart" in workflow_id.lower():
                return [
                    "- Verify TX/RX pin connections",
                    "- Check baud rate matches on both ends",
                    "- Verify ground connection",
                    "- Test with known working configuration",
                    "- Check for electrical interference",
                ]
            elif "network" in workflow_id.lower():
                return [
                    "- Check physical network connections",
                    "- Verify network adapter is enabled",
                    "- Test with different network cable",
                    "- Check firewall and antivirus settings",
                    "- Verify DNS settings",
                ]
            elif "hardware" in workflow_id.lower():
                return [
                    "- Check device power connections",
                    "- Verify device is recognized in Device Manager",
                    "- Test with different USB port/cable",
                    "- Check device drivers and updates",
                    "- Test device on different computer",
                ]
            else:
                return ["- Reproduce the issue", "- Collect minimal logs/configs", "- Apply the recommended fix", "- Re-test and report"]
        else:
            # This is a dict, use the original logic
            steps = sig_match.get("steps") or []
            fix = sig_match.get("fix")
            checklist: list[str] = [f"- {s}" if not s.startswith("- ") else s for s in steps]
            if fix:
                checklist.append(f"- Apply fix: {fix}")
            # Optionally attach refs from resources/sig
            refs = sig_match.get("refs") or resources.get("docs") or []
            if refs:
                checklist.append(f"- References: {', '.join(self._ref_titles(refs)[:3])}")
            return checklist or [
                "- Reproduce the issue",
                "- Collect minimal logs/configs",
                "- Apply the recommended fix",
                "- Re-test and report",
            ]

    def _checklist_from_result(self, result: dict[str, Any], resources: dict[str, Any]) -> list[str]:
        status = str(result.get("status", "ok"))
        name = result.get("name") or "diagnostic workflow"
        checklist = [f"- Review output of {name} (status: {status})"]
        if status != "ok":
            checklist += [
                "- Re-run with additional logs",
                "- Consider alternative diagnostic workflow",
                "- Escalate with artifacts attached",
            ]
        refs = resources.get("docs") or []
        if refs:
            checklist.append(f"- References: {', '.join(self._ref_titles(refs)[:3])}")
        return checklist

    def _draft_checklist(
        self,
        message: str,
        entities: dict[str, Any],
        resources: dict[str, Any],
        preliminary: dict[str, Any],
    ) -> list[str]:
        """
        Domain-agnostic checklist skeleton.
        """
        base = [
            "- Reproduce the issue with a minimal test, note exact steps.",
            "- Verify configuration and environment assumptions.",
            "- Inspect recent logs for errors/warnings near the failure time.",
            "- Try the simplest corrective action (restart/reinit/clear cache).",
            "- Collect a focused artifact bundle (logs, config, version).",
            "- Re-test and confirm whether behavior changes.",
        ]
        # Light tailoring
        if preliminary.get("category") == "performance":
            base.insert(3, "- Capture basic metrics (latency/throughput/CPU) and compare to baseline.")
        if entities:
            base.append(f"- Include identifiers (context: {', '.join(f'{k}={v}' for k, v in entities.items() if v)})")
        refs = resources.get("docs") or []
        if refs:
            base.append(f"- References: {', '.join(self._ref_titles(refs)[:3])}")
        return base

    def _ref_titles(self, refs: list[Any]) -> list[str]:
        titles: list[str] = []
        for r in refs:
            if isinstance(r, dict):
                t = r.get("title") or r.get("name") or str(r.get("id", ""))[:8]
            else:
                t = str(r)
            titles.append(t)
        return titles
