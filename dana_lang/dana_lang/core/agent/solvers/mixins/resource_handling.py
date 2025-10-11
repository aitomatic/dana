"""
Resource handling mixin for solvers.

This mixin provides functionality for executing resource calls, processing results,
and handling POST_PROCESSING_PROMPT patterns.
"""


class ResourceHandlingMixin:
    """Mixin providing resource execution and processing capabilities."""

    def _execute_resource_calls(self, response: str) -> str:
        """Execute resource calls found in LLM response."""
        import re

        # Find all RESOURCE_CALL patterns
        pattern = r"RESOURCE_CALL:\s*(\w+)\.(\w+)\(([^)]*)\)"
        matches = re.findall(pattern, response)

        if not matches:
            return response

        print(f"🔧 Found {len(matches)} resource call matches: {matches}")

        # Get dependencies
        wc, ri, _ = self._inject_dependencies()
        if not ri:
            print("⚠️ No resource registry available")
            return response

        # Get available resources
        resources = ri.get_available_resources()
        if not resources:
            print("⚠️ No resources available")
            return response

        # Execute each resource call
        resource_results = []
        for resource_name, method_name, args in matches:
            print(f"🔧 Processing resource call: {resource_name}.{method_name}({args})")

            # Try to find resource by friendly name first, then by instance_id
            resource = None
            for instance_id, res in resources.items():
                if hasattr(ri, "_instance_metadata") and instance_id in ri._instance_metadata:
                    metadata = ri._instance_metadata[instance_id]
                    friendly_name = metadata.get("name", instance_id)
                    if friendly_name == resource_name:
                        resource = res
                        print(f"🔧 [DEBUG] Found resource by friendly name: {resource_name}")
                        break

            # If not found by friendly name, try by instance_id
            if resource is None and resource_name in resources:
                resource = resources[resource_name]
                print(f"🔧 [DEBUG] Found resource by instance_id: {resource_name}")

            if resource is None:
                print(f"❌ Resource '{resource_name}' not found")
                continue

            # Parse arguments
            args_clean = args.strip("\"'")  # Initialize outside try block
            try:
                # Simple argument parsing - remove quotes and handle basic types
                if args_clean.lower() in ["true", "false"]:
                    parsed_args = args_clean.lower() == "true"
                elif args_clean.isdigit():
                    parsed_args = int(args_clean)
                else:
                    parsed_args = args_clean
            except Exception as e:
                print(f"⚠️ Error parsing arguments '{args}': {e}")
                parsed_args = args_clean

            # Execute the resource call
            try:
                if hasattr(resource, method_name):
                    method = getattr(resource, method_name)
                    result = method(parsed_args)

                    # Store result with metadata
                    resource_results.append(
                        {
                            "resource_name": resource_name,
                            "method_name": method_name,
                            "args": parsed_args,
                            "result": result,
                            "result_str": str(result),
                            "url": args_clean if args_clean.startswith(("http://", "https://")) else None,
                        }
                    )
                    print(f"✅ Resource call successful: {resource_name}.{method_name}")
                else:
                    print(f"❌ Method '{method_name}' not found on resource '{resource_name}'")
            except Exception as e:
                print(f"❌ Error executing resource call: {e}")

        # Replace resource calls in response with results
        if resource_results:
            # Create a summary of results
            result_summary = "Resource calls executed successfully:\n"
            for result in resource_results:
                result_summary += f"- {result['resource_name']}.{result['method_name']}: {result['result_str'][:100]}...\n"

            # Remove resource call lines from response
            lines = response.split("\n")
            filtered_lines = [line for line in lines if not line.strip().startswith("RESOURCE_CALL:")]
            response = "\n".join(filtered_lines)

            # Add result summary
            response += f"\n\n{result_summary}"

        return response

    def _execute_resources_iteratively(self, response: str, system_prompt: str) -> str:
        """Execute resource calls iteratively, sending results back to LLM for processing."""
        import re

        max_iterations = 5  # Prevent infinite loops
        iteration = 0

        while response and "RESOURCE_CALL:" in response and iteration < max_iterations:
            iteration += 1
            print(f"🔧 [ITERATION {iteration}] Processing resource calls...")

            # Find all RESOURCE_CALL patterns
            pattern = r"RESOURCE_CALL:\s*(\w+)\.(\w+)\(([^)]*)\)"
            matches = re.findall(pattern, response)

            if not matches:
                break

            print(f"🔧 [ITERATION {iteration}] Found {len(matches)} resource call matches: {matches}")

            # Execute all resource calls and collect results
            resource_results = []
            for resource_name, method_name, args in matches:
                print(f"🔧 [ITERATION {iteration}] Processing resource call: {resource_name}.{method_name}({args})")

                # Get dependencies
                wc, ri, _ = self._inject_dependencies()
                if not ri:
                    print(f"❌ [ITERATION {iteration}] No resource registry available")
                    continue

                # Get available resources
                resources = ri.get_available_resources()
                if not resources:
                    print(f"❌ [ITERATION {iteration}] No resources available")
                    continue

                # Try to find resource by friendly name first, then by instance_id
                resource = None
                for instance_id, res in resources.items():
                    if hasattr(ri, "_instance_metadata") and instance_id in ri._instance_metadata:
                        metadata = ri._instance_metadata[instance_id]
                        friendly_name = metadata.get("name", instance_id)
                        if friendly_name == resource_name:
                            resource = res
                            break

                # If not found by friendly name, try by instance_id
                if resource is None and resource_name in resources:
                    resource = resources[resource_name]

                if resource is None:
                    print(f"❌ [ITERATION {iteration}] Resource '{resource_name}' not found")
                    continue

                # Parse arguments
                args_clean = args.strip("\"'")  # Initialize outside try block
                try:
                    if args_clean.lower() in ["true", "false"]:
                        parsed_args = args_clean.lower() == "true"
                    elif args_clean.isdigit():
                        parsed_args = int(args_clean)
                    else:
                        parsed_args = args_clean
                except Exception as e:
                    print(f"⚠️ [ITERATION {iteration}] Error parsing arguments '{args}': {e}")
                    parsed_args = args_clean

                # Execute the resource call
                try:
                    if hasattr(resource, method_name):
                        method = getattr(resource, method_name)
                        result = method(parsed_args)

                        # Store result with metadata
                        resource_results.append(
                            {
                                "resource_name": resource_name,
                                "method_name": method_name,
                                "args": parsed_args,
                                "result": result,
                                "result_str": str(result),
                                "url": args_clean if args_clean.startswith(("http://", "https://")) else None,
                            }
                        )
                        print(f"🔧 [ITERATION {iteration}] Resource execution successful")
                    else:
                        print(f"❌ [ITERATION {iteration}] Method '{method_name}' not found on resource '{resource_name}'")
                except Exception as e:
                    print(f"❌ [ITERATION {iteration}] Error executing resource call: {e}")

            # Check for POST_PROCESSING_PROMPT in the response
            post_processing_prompt = self._extract_post_processing_prompt(response)
            if post_processing_prompt:
                print(f"🔧 [ITERATION {iteration}] Found POST_PROCESSING_PROMPT: {post_processing_prompt}")

            # Process resource results
            if resource_results:
                print(f"🔧 [ITERATION {iteration}] Processing resource results...")

                if post_processing_prompt:
                    # Use POST_PROCESSING_PROMPT to process content, then continue the conversation
                    processed_content = self._process_with_post_processing_prompt(
                        response, resource_results, post_processing_prompt, system_prompt, iteration
                    )
                    # Feed processed content back into the main conversation loop
                    response = self._continue_conversation_with_processed_content(response, processed_content, system_prompt, iteration)
                else:
                    # Use existing behavior - send results back to LLM
                    response = self._process_with_standard_flow(response, resource_results, system_prompt, iteration)

        if iteration >= max_iterations:
            print(f"⚠️ [WARNING] Reached maximum iterations ({max_iterations}), stopping resource execution")

        return response

    def _continue_conversation_with_processed_content(
        self, response: str, processed_content: str, system_prompt: str, iteration: int
    ) -> str:
        """Continue the conversation with processed content, allowing LLM to work with it."""
        print(f"🔧 [ITERATION {iteration}] Continuing conversation with processed content...")

        # Create a follow-up message with the processed content
        follow_up_prompt = f"""The resource calls were executed and the content was processed according to your instructions. Here are the processed results:

{processed_content}

Please continue working with this information. You can make additional resource calls if needed, or provide your final response to the user based on this processed content."""

        # Create a conversation-style prompt for the LLM
        conversation_prompt = f"""User: {response}

Assistant: I'll execute those resource calls and process the content for you.

System: Resource response: {follow_up_prompt}"""

        # Use _query_llm_with_prteng to maintain full conversation context and capabilities
        try:
            response = self._query_llm_with_prteng(conversation_prompt, system_prompt)
            if response:
                print(f"🔧 [ITERATION {iteration}] LLM continued conversation with processed content")
                return response
            else:
                print(f"⚠️ [ITERATION {iteration}] LLM failed to continue conversation")
                return response
        except Exception as e:
            print(f"❌ [ITERATION {iteration}] Error continuing conversation: {e}")
            return response

    def _extract_post_processing_prompt(self, response: str) -> str | None:
        """Extract POST_PROCESSING_PROMPT from LLM response."""
        import re

        # Look for POST_PROCESSING_PROMPT: "instructions"
        pattern = r'POST_PROCESSING_PROMPT:\s*"([^"]+)"'
        match = re.search(pattern, response)

        if match:
            return match.group(1)

        return None

    def _get_smart_truncation_limit(self) -> int:
        """Get smart truncation limit based on context window size."""
        # Conservative estimate: assume 50% of context window is available for content
        # Most models have 4K-32K context windows, so 15K is a reasonable default
        return 15000

    def _process_with_post_processing_prompt(
        self, response: str, resource_results: list, post_processing_prompt: str, system_prompt: str, iteration: int
    ) -> str:
        """Process resource results using POST_PROCESSING_PROMPT."""
        print(f"🔧 [ITERATION {iteration}] Using POST_PROCESSING_PROMPT for content processing...")

        # Extract the actual content from resource results
        content_to_process = []
        truncation_limit = self._get_smart_truncation_limit()

        for result in resource_results:
            if isinstance(result, dict) and "result_str" in result:
                # Use smart truncation limit for better content processing
                result_str = result["result_str"]
                if len(result_str) > truncation_limit:
                    result_str = result_str[:truncation_limit] + f"... [truncated from {len(result['result_str'])} chars]"
                content_to_process.append(f"Content from {result['resource_name']}: {result_str}")
            elif isinstance(result, str):
                content_to_process.append(result)

        if not content_to_process:
            print(f"⚠️ [ITERATION {iteration}] No content to process")
            return response

        # Combine all content
        combined_content = "\n\n".join(content_to_process)

        # Create processing prompt
        processing_prompt = f"""Content to process:

{combined_content}

Processing instructions: {post_processing_prompt}

Please process the content according to the instructions and provide a helpful response to the user."""

        # Use existing LLM query method for processing
        try:
            processed_response = self._query_llm_with_prteng(
                prompt=processing_prompt,
                system_prompt="You are a content processing assistant. Follow the user's instructions exactly to process the provided content.",
                max_turns=1,
            )

            if processed_response:
                print(f"🔧 [ITERATION {iteration}] Content processing successful")
                print(f"📄 Processed response preview: {processed_response[:100]}{'...' if len(processed_response) > 100 else ''}")
                return processed_response
            else:
                print(f"⚠️ [ITERATION {iteration}] Content processing failed, falling back to standard flow")
                return self._process_with_standard_flow(response, resource_results, system_prompt, iteration)

        except Exception as e:
            print(f"⚠️ [ITERATION {iteration}] Error in content processing: {e}")
            return self._process_with_standard_flow(response, resource_results, system_prompt, iteration)

    def _process_with_standard_flow(self, response: str, resource_results: list, system_prompt: str, iteration: int) -> str:
        """Process resource results using the standard flow (existing behavior)."""
        print(f"🔧 [ITERATION {iteration}] Using standard flow for resource results...")

        # Convert resource results to string format for standard processing
        resource_context_parts = []
        truncation_limit = self._get_smart_truncation_limit()

        for result in resource_results:
            if isinstance(result, dict) and "result_str" in result:
                # Use smart truncation limit for better content processing
                result_str = result["result_str"]
                if len(result_str) > truncation_limit:
                    result_str = result_str[:truncation_limit] + f"... [truncated from {len(result['result_str'])} chars]"
                resource_context_parts.append(f"web_browser('{result.get('url', 'unknown')}'): {result_str}")
            elif isinstance(result, str):
                resource_context_parts.append(result)

        resource_context = "\n\n".join(resource_context_parts)

        # Create a follow-up message with resource results
        follow_up_prompt = f"""The following resource calls were executed and returned these results:

{resource_context}

Please process these results and provide a helpful response to the user. If you need to make additional resource calls, you can do so."""

        # Create a conversation-style prompt for the LLM
        conversation_prompt = f"""User: {response}

Assistant: I'll execute those resource calls for you.

System: Resource response: {follow_up_prompt}"""

        # Use _query_llm_with_prteng to maintain full conversation context and capabilities
        try:
            response = self._query_llm_with_prteng(conversation_prompt, system_prompt)
            if response:
                print(f"🔧 [ITERATION {iteration}] LLM processed resource results:")
                print(f"🤖 FOLLOW_UP_RESPONSE:\n{response}")
                print("=" * 80)
            else:
                print(f"⚠️ [ITERATION {iteration}] LLM failed to process resource results")
        except Exception as e:
            print(f"❌ [ITERATION {iteration}] Error processing resource results: {e}")

        return response

    def _get_available_resources_text(self) -> str:
        """Get formatted available resources text."""
        try:
            # Get dependencies through injection
            wc, ri, _ = self._inject_dependencies()

            if not ri or not hasattr(ri, "get_available_resources"):
                return "No resources available"

            resources = ri.get_available_resources()
            if not resources:
                return "No resources available"

            return self._format_resources_from_registry(resources, ri)

        except Exception as e:
            print(f"⚠️ Error getting available resources: {e}")
            return "Error retrieving resource information"

    def _enhance_system_prompt_with_resources(self, system_prompt: str) -> str:
        """Enhance system prompt with available resources information."""
        try:
            available_resources = self._get_available_resources_text()
            if available_resources and available_resources not in ["No resources available", "Error retrieving resource information"]:
                # Check if system prompt has {available_resources} placeholder
                if "{available_resources}" in system_prompt:
                    # Replace the placeholder with actual resources
                    # Handle case where other placeholders might exist but we only replace available_resources
                    try:
                        return system_prompt.format(available_resources=available_resources)
                    except KeyError:
                        # If there are other placeholders that can't be filled, just replace available_resources
                        import re

                        return re.sub(r"\{available_resources\}", available_resources, system_prompt)
                else:
                    # No placeholder, append resources
                    return f"{system_prompt}\n\n<available_resources>\n{available_resources}\n</available_resources>"
        except Exception as e:
            print(f"⚠️ Error enhancing system prompt with resources: {e}")

        return system_prompt

    def _format_resources_from_registry(self, resources: dict, ri) -> str:
        """Format resources from registry into readable text."""
        try:
            resource_descriptions = []

            for instance_id, resource in resources.items():
                # Get friendly name from metadata if available
                friendly_name = instance_id
                if hasattr(ri, "_instance_metadata") and instance_id in ri._instance_metadata:
                    metadata = ri._instance_metadata[instance_id]
                    friendly_name = metadata.get("name", instance_id)

                # Get resource type
                resource_type = getattr(resource, "kind", "unknown")

                # Get resource type name for display
                resource_type_name = getattr(resource, "__class__", type(resource)).__name__

                # Handle specific resource types with hard-coded metadata
                if resource_type == "browser":
                    description = "Browse websites and extract content using curl"
                    methods = "query(url) - Browse a website and return its contents"
                    example = "web_browser.query('https://example.com')"
                    resource_descriptions.append(
                        f"- {friendly_name} ({resource_type_name}): {description}\n  Methods: {methods}\n  Example: {example}"
                    )
                else:
                    # For other resources, use generic formatting
                    try:
                        description = getattr(resource, "description", "No description available")

                        # If we have a meaningful description (not a Mock), use it
                        if description != "No description available" and not hasattr(description, "_mock_name"):
                            resource_descriptions.append(f"- {friendly_name} ({resource_type_name}): {description}")
                        else:
                            # Fall back to method listing if no description
                            methods = []
                            for attr_name in dir(resource):
                                if not attr_name.startswith("_") and callable(getattr(resource, attr_name)):
                                    methods.append(attr_name)

                            methods_str = ", ".join(methods[:5])  # Limit to first 5 methods
                            if len(methods) > 5:
                                methods_str += f" (and {len(methods) - 5} more)"

                            resource_descriptions.append(f"- {friendly_name} ({resource_type_name}): {methods_str}")
                    except Exception:
                        # If there's an error getting the description, raise it to be caught by outer try/catch
                        raise

            if resource_descriptions:
                return "\n".join(resource_descriptions)
            else:
                return "No resources available"

        except Exception as e:
            print(f"⚠️ Error formatting resources: {e}")
            return "Error retrieving resource information"

    def _process_resource_calls(self, response: str) -> str:
        """Process resource calls in the response (legacy method for backward compatibility)."""
        return self._execute_resource_calls(response)
