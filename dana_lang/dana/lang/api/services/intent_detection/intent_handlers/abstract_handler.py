from abc import ABC, abstractmethod
import re
from typing import Any


class AbstractHandler(ABC):
    @abstractmethod
    def handle(self, *args, **kwargs) -> Any:
        pass

    def _parse_xml_tool_call(self, xml_content: str) -> tuple[str, dict, str]:
        """
        Parse XML tool call to extract tool name, parameters, and thinking content.

        Example input:
        I need to first explore the structure...

        <thinking>...</thinking>
        <ask_follow_up_question>
        <question>What type of ratios?</question>
        <options>
          <option>financial</option>
          <option>mathematical</option>
        </options>
        </ask_follow_up_question>

        Returns: ("ask_follow_up_question", {"question": "...", "options": [...]}, "thinking content")
        """
        # Clean up the content - remove any extra whitespace
        xml_content = xml_content.strip()

        # Find the first XML tag (either <thinking> or a tool tag)
        first_tag_match = re.search(r"<(\w+)(?:\s[^>]*)?>", xml_content)
        if not first_tag_match:
            raise ValueError("""Could not find any XML tags. Please reformat the original request to include exactly TWO XML blocks, in this order:
1) Planning
<thinking>
Your thinking logic here...
</thinking>

2) Tool call (strict tags as defined)
<tool_name>
  <param1>value</param1>
  ...
  <paramN>value</paramN>
</tool_name>""")

        first_tag_start = first_tag_match.start()

        # Extract any text before the first XML tag as additional thinking content
        text_before_xml = xml_content[:first_tag_start].strip() if first_tag_start > 0 else ""

        # Extract thinking content from <thinking> tags if present
        thinking_match = re.search(r"<thinking>(.*?)</thinking>", xml_content, flags=re.DOTALL)
        thinking_tag_content = thinking_match.group(1).strip() if thinking_match else ""

        # Combine text before XML and thinking tag content
        thinking_parts = []
        if text_before_xml:
            thinking_parts.append(text_before_xml)
        if thinking_tag_content:
            thinking_parts.append(thinking_tag_content)

        thinking_content = "\n\n".join(thinking_parts) if thinking_parts else ""

        # Remove thinking tags and text before XML for tool parsing
        xml_for_parsing = xml_content
        if text_before_xml:
            xml_for_parsing = xml_content[first_tag_start:]
        xml_without_thinking = re.sub(r"<thinking>.*?</thinking>\s*", "", xml_for_parsing, flags=re.DOTALL)

        # Extract tool name - look for the first tag that's not 'thinking'
        tool_match = re.search(r"<(\w+)(?:\s[^>]*)?>(?!.*<thinking>)", xml_without_thinking)
        if not tool_match:
            raise ValueError(f"Could not find tool name in XML: {xml_content}")

        tool_name = tool_match.group(1)

        if tool_name not in self.tools:
            raise ValueError("""Could not parse tool name from the request. Please reformat the original request to include exactly TWO XML blocks, in this order:
1) Planning
<thinking>
Your thinking logic here...
</thinking>

2) Tool call (strict tags as defined)
<tool_name>
  <param1>value</param1>
  ...
  <paramN>value</paramN>
</tool_name>""")

        # Extract just the tool XML block
        tool_pattern = rf"<{tool_name}.*?>(.*?)</{tool_name}>"
        tool_content_match = re.search(tool_pattern, xml_without_thinking, re.DOTALL)
        if not tool_content_match:
            raise ValueError(f"""Could not extract tool content for {tool_name}. Please reformat the original request to include exactly TWO XML blocks, in this order:
1) Planning
<thinking>
Your thinking logic here...
</thinking>

2) Tool call (strict tags as defined)
<tool_name>
  <param1>value</param1>
  ...
  <paramN>value</paramN>
</tool_name>""")

        tool_xml = tool_content_match.group(1)

        # Extract parameters recursively
        params = self.tools[tool_name].parse_arguments_from_xml_string(tool_xml)

        return tool_name, params, thinking_content
