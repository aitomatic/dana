#!/usr/bin/env python
"""Fix pattern handlers in DANA transcoder by replacing them completely."""

import sys


def fix_transcoder(file_path):
    with open(file_path) as f:
        content = f.read()

    # Find the start of the transcode method
    transcode_start = content.find("async def transcode(")
    if transcode_start == -1:
        print("Could not find transcode method!")
        return False

    # Find where we should insert our new pattern handlers
    # (after the declaration of input_lower)
    input_lower_line = content.find("input_lower = input_text.lower().strip()", transcode_start)
    if input_lower_line == -1:
        print("Could not find input_lower initialization!")
        return False

    # Find the end of the first pattern handling section
    first_try_direct_parsing = content.find("# 1. Try direct parsing first", transcode_start)
    if first_try_direct_parsing == -1:
        print("Could not find start of direct parsing section!")
        return False

    # Extract the part of the file before and after the pattern handlers
    content_before = content[: input_lower_line + len("input_lower = input_text.lower().strip()") + 1]
    content_after = content[first_try_direct_parsing:]

    # Define new pattern handlers
    new_pattern_handlers = """
        # 0. Check for common patterns we can directly convert without LLM
        input_lower = input_text.lower().strip()
        import re

        # Handle "calculate X" pattern
        if input_lower.startswith("calculate "):
            expression = input_text[10:].strip()  # Remove "calculate "
            print(f"🔄 Direct conversion of 'calculate' pattern: {expression}")

            # Convert natural language math to DANA operators
            expression = expression.replace(" plus ", " + ")
            expression = expression.replace(" minus ", " - ")
            expression = expression.replace(" times ", " * ")
            expression = expression.replace(" divided by ", " / ")
            expression = expression.replace(" multiplied by ", " * ")

            dana_code = f"private.result = {expression}"
            print(f"🔄 Converted to: {dana_code}")

            try:
                result = parse(dana_code)
                if result.is_valid:
                    print(f"✅ Direct conversion successful: {dana_code}")
                    return result, dana_code
            except Exception as e:
                print(f"⚠️ Direct conversion failed: {e}")

        # Handle "add X and Y" pattern
        if input_lower.startswith("add ") and " and " in input_lower:
            parts = input_lower[4:].split(" and ")  # Split "add X and Y" into ["X", "Y"]
            if len(parts) == 2:
                try:
                    # Try to convert to numbers
                    x_str = parts[0].strip()
                    y_str = parts[1].strip()

                    # Check if these are numbers or variables
                    x_is_num = all(c.isdigit() or c == '.' for c in x_str)
                    y_is_num = all(c.isdigit() or c == '.' for c in y_str)

                    if x_is_num and y_is_num:
                        # Convert and evaluate the expression
                        dana_code = f"private.result = {x_str} + {y_str}"
                        print(f"🔄 Direct conversion of 'add X and Y' pattern: {dana_code}")
                        result = parse(dana_code)
                        if result.is_valid:
                            print(f"✅ Direct conversion successful: {dana_code}")
                            return result, dana_code
                except Exception as e:
                    print(f"⚠️ Direct 'add' conversion failed: {e}")

        # Handle "multiply X and Y" pattern
        if input_lower.startswith("multiply ") and " and " in input_lower:
            parts = input_lower[9:].split(" and ")  # Split "multiply X and Y" into ["X", "Y"]
            if len(parts) == 2:
                try:
                    # Try to convert to numbers
                    x_str = parts[0].strip()
                    y_str = parts[1].strip()

                    # Check if these are numbers or variables
                    x_is_num = all(c.isdigit() or c == '.' for c in x_str)
                    y_is_num = all(c.isdigit() or c == '.' for c in y_str)

                    if x_is_num and y_is_num:
                        # Convert and evaluate the expression
                        dana_code = f"private.result = {x_str} * {y_str}"
                        print(f"🔄 Direct conversion of 'multiply X and Y' pattern: {dana_code}")
                        result = parse(dana_code)
                        if result.is_valid:
                            print(f"✅ Direct conversion successful: {dana_code}")
                            return result, dana_code
                except Exception as e:
                    print(f"⚠️ Direct 'multiply' conversion failed: {e}")

        # Handle "what is X plus/minus/times Y" pattern
        if input_lower.startswith("what is "):
            expression = input_lower[8:].strip()  # Remove "what is "

            # Convert natural language to operators
            expression = expression.replace(" plus ", " + ")
            expression = expression.replace(" minus ", " - ")
            expression = expression.replace(" times ", " * ")
            expression = expression.replace(" divided by ", " / ")
            expression = expression.replace(" multiplied by ", " * ")

            dana_code = f"private.result = {expression}"
            print(f"🔄 Direct conversion of 'what is' pattern: {dana_code}")

            try:
                result = parse(dana_code)
                if result.is_valid:
                    print(f"✅ Direct conversion successful: {dana_code}")
                    return result, dana_code
            except Exception as e:
                print(f"⚠️ Direct 'what is' conversion failed: {e}")

        # Handle "compute X" pattern
        if input_lower.startswith("compute "):
            expression = input_text[8:].strip()  # Remove "compute "
            print(f"🔄 Direct conversion of 'compute' pattern: {expression}")
            dana_code = f"private.result = {expression}"
            try:
                result = parse(dana_code)
                if result.is_valid:
                    print(f"✅ Direct conversion successful: {dana_code}")
                    return result, dana_code
            except Exception as e:
                print(f"⚠️ Direct 'compute' conversion failed: {e}")

        # Handle direct math expressions like "10 + 20"
        if re.match(r'^\\s*\\d+\\s*[+\\-*/]\\s*\\d+\\s*$', input_text):
            print(f"🔄 Direct conversion of bare math expression: {input_text}")
            dana_code = f"private.result = {input_text}"
            try:
                result = parse(dana_code)
                if result.is_valid:
                    print(f"✅ Direct conversion successful: {dana_code}")
                    return result, dana_code
            except Exception as e:
                print(f"⚠️ Direct math expression conversion failed: {e}")

        # Handle single number inputs like "42" or "-899"
        if re.match(r'^\\s*-?\\d+\\.?\\d*\\s*$', input_text):
            print(f"🔄 Direct conversion of single number: {input_text}")
            dana_code = f"private.result = {input_text.strip()}"
            try:
                result = parse(dana_code)
                if result.is_valid:
                    print(f"✅ Direct conversion successful: {dana_code}")
                    return result, dana_code
            except Exception as e:
                print(f"⚠️ Direct number conversion failed: {e}")

        # Handle simple variable assignment like "a=5"
        if re.match(r'^\\s*([a-zA-Z_][a-zA-Z0-9_]*)\\s*=\\s*(.+)\\s*$', input_text):
            print(f"🔄 Direct conversion of simple assignment: {input_text}")
            match = re.match(r'^\\s*([a-zA-Z_][a-zA-Z0-9_]*)\\s*=\\s*(.+)\\s*$', input_text)
            var_name = match.group(1)
            value = match.group(2)
            dana_code = f"private.{var_name} = {value}"
            try:
                result = parse(dana_code)
                if result.is_valid:
                    print(f"✅ Direct conversion successful: {dana_code}")
                    return result, dana_code
            except Exception as e:
                print(f"⚠️ Direct assignment conversion failed: {e}")

        # Handle "print X" pattern
        if input_lower.startswith("print "):
            message = input_text[6:].strip()  # Remove "print "
            # Add quotes if needed
            if not (message.startswith('"') and message.endswith('"')) and \
               not (message.startswith("'") and message.endswith("'")):
                message = f'"{message}"'
            dana_code = f"print({message})"
            print(f"🔄 Direct conversion of 'print' pattern: {dana_code}")
            try:
                result = parse(dana_code)
                if result.is_valid:
                    print(f"✅ Direct conversion successful: {dana_code}")
                    return result, dana_code
            except Exception as e:
                print(f"⚠️ Direct 'print' conversion failed: {e}")

        # Handle "log X" pattern
        if input_lower.startswith("log "):
            message = input_text[4:].strip()  # Remove "log "
            # Add quotes if needed
            if not (message.startswith('"') and message.endswith('"')) and \
               not (message.startswith("'") and message.endswith("'")):
                message = f'"{message}"'
            dana_code = f"log.info({message})"
            print(f"🔄 Direct conversion of 'log' pattern: {dana_code}")
            try:
                result = parse(dana_code)
                if result.is_valid:
                    print(f"✅ Direct conversion successful: {dana_code}")
                    return result, dana_code
            except Exception as e:
                print(f"⚠️ Direct 'log' conversion failed: {e}")
    """

    # Combine the parts
    new_content = content_before + new_pattern_handlers + content_after

    # Write the new content
    with open(file_path, "w") as f:
        f.write(new_content)

    print(f"Updated pattern handlers in {file_path}")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_transcoder(sys.argv[1])
    else:
        print("Usage: python new_pattern_handlers.py <file_path>")
