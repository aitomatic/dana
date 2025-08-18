from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)
import re
from typing import Optional


class AttemptCompletionTool(BaseTool):
    def __init__(self):
        tool_info = BaseToolInformation(
            name="attempt_completion",
            description="Present information to the user. Use for: 1) Final results after workflow completion, 2) Direct answers to agent information requests ('Tell me about Sofia'), 3) System capability questions ('What can you help me with?'), 4) Out-of-scope request redirection. DO NOT use for knowledge structure questions - use explore_knowledge instead.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="summary",
                        type="string",
                        description="Summary of what was accomplished OR direct answer/explanation to user's question",
                        example="Successfully generated 10 knowledge artifacts OR Sofia is your Personal Finance Advisor that I'm helping you build OR I specialize in building knowledge for Sofia through structure design and content generation",
                    ),
                    BaseArgument(
                        name="response_type",
                        type="string",
                        description="Optional: Type of response for better formatting. Auto-detected if not provided.",
                        example="guidance|capabilities|status|completion|information",
                        required=False,
                    ),
                    BaseArgument(
                        name="format_style",
                        type="string",
                        description="Optional: Formatting style preference. Defaults to 'markdown'.",
                        example="markdown|simple|detailed",
                        required=False,
                    ),
                ],
                required=["summary"],
            ),
        )
        super().__init__(tool_info)

    def _detect_response_type(self, summary: str) -> str:
        """Intelligently detect the type of response for appropriate formatting."""
        summary_lower = summary.lower()
        
        # Completion indicators
        completion_indicators = [
            "knowledge generation complete",
            "workflow is now complete", 
            "all knowledge has been generated",
            "generation workflow complete",
            "successfully generated",
            "workflow finished",
            "completed successfully"
        ]
        
        if any(phrase in summary_lower for phrase in completion_indicators):
            return "completion"
        
        # Agent enhancement guidance indicators
        guidance_indicators = [
            "enhance", "improve", "build", "develop", "approach", "strategy", 
            "systematic", "methodology", "recommended", "best practice",
            "step by step", "process", "framework", "roadmap"
        ]
        
        if any(phrase in summary_lower for phrase in guidance_indicators):
            return "guidance"
        
        # Capabilities and system information indicators
        capability_indicators = [
            "can help", "specialize in", "capabilities", "features", "what i do",
            "how i work", "my role", "assistant", "help you with"
        ]
        
        if any(phrase in summary_lower for phrase in capability_indicators):
            return "capabilities"
        
        # Status and progress indicators
        status_indicators = [
            "current state", "exists", "progress", "status", "what exists",
            "how complete", "what's missing", "current knowledge"
        ]
        
        if any(phrase in summary_lower for phrase in status_indicators):
            return "status"
        
        # Default to information
        return "information"

    def _format_guidance_response(self, summary: str) -> str:
        """Format agent enhancement guidance responses with structured markdown."""
        # DISABLED: This method was overly complex and didn't work well
        # Instead, just return the summary with basic markdown formatting
        return f"{summary}"

    def _format_capabilities_response(self, summary: str) -> str:
        """Format system capabilities and role information responses."""
        lines = summary.split('. ')
        
        role_info = []
        capabilities = []
        how_to_use = []
        general_info = []
        
        for line in lines:
            line_lower = line.lower()
            
            if any(phrase in line_lower for phrase in ["role", "specialize", "expert", "assistant", "help"]):
                role_info.append(line)
            elif any(phrase in line_lower for phrase in ["can help", "capabilities", "features", "what i do"]):
                capabilities.append(line)
            elif any(phrase in line_lower for phrase in ["how to", "use", "request", "ask"]):
                how_to_use.append(line)
            else:
                general_info.append(line)
        
        content = "# 🤖 System Capabilities\n\n"
        
        if role_info:
            content += "## 🎭 My Role\n"
            for line in role_info:
                content += f"{line.strip()}\n\n"
        
        if capabilities:
            content += "## 🛠️ What I Can Do\n"
            for line in capabilities:
                content += f"- {line.strip()}\n"
            content += "\n"
        
        if how_to_use:
            content += "## 📖 How to Use My Services\n"
            for line in how_to_use:
                content += f"- {line.strip()}\n"
            content += "\n"
        
        if general_info:
            content += "## ℹ️ Additional Information\n"
            for line in general_info:
                if line.strip():
                    content += f"{line.strip()}\n\n"
        
        return content

    def _format_status_response(self, summary: str) -> str:
        """Format status and progress information responses."""
        lines = summary.split('. ')
        
        current_status = []
        progress_info = []
        gaps = []
        recommendations = []
        
        for line in lines:
            line_lower = line.lower()
            
            if any(phrase in line_lower for phrase in ["current", "exists", "status", "state"]):
                current_status.append(line)
            elif any(phrase in line_lower for phrase in ["progress", "complete", "generated", "built"]):
                progress_info.append(line)
            elif any(phrase in line_lower for phrase in ["missing", "gaps", "need", "require"]):
                gaps.append(line)
            elif any(phrase in line_lower for phrase in ["recommend", "suggest", "should", "could"]):
                recommendations.append(line)
        
        content = "## 📊 Current Status & Progress\n\n"
        
        if current_status:
            content += "### 🔍 Current State\n"
            for line in current_status:
                content += f"- {line.strip()}\n"
            content += "\n"
        
        if progress_info:
            content += "### ✅ What's Been Accomplished\n"
            for line in progress_info:
                content += f"- {line.strip()}\n"
            content += "\n"
        
        if gaps:
            content += "### ⚠️ Identified Gaps\n"
            for line in gaps:
                content += f"- {line.strip()}\n"
            content += "\n"
        
        if recommendations:
            content += "### 💡 Recommendations\n"
            for line in recommendations:
                content += f"- {line.strip()}\n"
            content += "\n"
        
        return content

    def _format_completion_response(self, summary: str) -> str:
        """Format workflow completion responses."""
        return f"""🎉 Knowledge Generation Complete

{summary}

✅ All knowledge has been:
- Generated with high accuracy
- Validated for quality  
- Stored to vector database
- Made available for agent usage

The knowledge generation workflow is now complete. Your agent has been enhanced with new domain expertise!"""

    def _format_information_response(self, summary: str) -> str:
        """Format general information responses with basic structure."""
        # Try to identify natural paragraph breaks and structure
        paragraphs = summary.split('\n\n')
        
        if len(paragraphs) == 1:
            # Single paragraph - add some basic formatting
            return f"\n{summary}"
        else:
            # Multiple paragraphs - structure them
            for i, para in enumerate(paragraphs):
                if para.strip():
                    content += f"{para.strip()}\n\n"
            return content.strip()

    def _format_response(self, summary: str, response_type: str, format_style: str) -> str:
        """Format the response based on type and style preference."""
        if format_style == "simple":
            return summary
        
        # Auto-detect response type if not provided
        if not response_type or response_type == "auto":
            response_type = self._detect_response_type(summary)
        
        # Apply appropriate formatting
        if response_type == "completion":
            return self._format_completion_response(summary)
        elif response_type == "guidance":
            return self._format_guidance_response(summary)
        elif response_type == "capabilities":
            return self._format_capabilities_response(summary)
        elif response_type == "status":
            return self._format_status_response(summary)
        else:  # information or default
            return self._format_information_response(summary)

    async def _execute(self, summary: str, response_type: str = "auto", format_style: str = "markdown") -> ToolResult:
        # Format the response based on type and style
        formatted_content = self._format_response(summary, response_type, format_style)
        
        # Determine if this is a completion response
        is_completion = self._detect_response_type(summary) == "completion"
        
        if is_completion:
            return ToolResult(
                name="attempt_completion", 
                result=formatted_content, 
                require_user=True
            )
        else:
            return ToolResult(
                name="attempt_completion", 
                result=formatted_content, 
                require_user=True
            )
