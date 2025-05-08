"""Pattern handler code for DANA transcoder."""


def add_pattern_handlers(transcoder_file_path):
    """Add pattern handlers to the transcoder file."""
    with open(transcoder_file_path) as f:
        content = f.read()

    # Find where to insert numeric and variable assignment patterns
    # Add after the direct math expressions pattern
    import_re_pos = content.find("import re", content.find("def transcode"))
    if import_re_pos > 0:
        # Find the end of the block after the import re statement
        next_pattern_pos = content.find("# Handle", import_re_pos + 10)
        if next_pattern_pos > 0:
            # Insert our pattern handlers
            numeric_pattern = """
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
"""
            new_content = content[:next_pattern_pos] + numeric_pattern + content[next_pattern_pos:]
            with open(transcoder_file_path, "w") as f:
                f.write(new_content)
            return True
    return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        result = add_pattern_handlers(sys.argv[1])
        print(f"Pattern handlers added: {result}")
    else:
        print("Usage: python transcoder_patterns.py <transcoder_file_path>")
