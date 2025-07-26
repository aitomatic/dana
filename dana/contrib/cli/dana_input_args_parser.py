"""Dana CLI Input Arguments Parser."""

from pathlib import Path
import json
import re
import yaml

DANA_KEY_VALUE_INPUT_PATTERN = re.compile(
    r"([a-zA-Z_][a-zA-Z0-9_]*)"  # group 1: key (valid_Python_identifier_with_no_spaces_or_special_chars)
    r"\s*=\s*"  # equal sign with optional spaces around it
    r"(?:"  # non-capturing group for value (one of the following)
    r"@\s*'([^']+)'"  # group 2: @ optional spaces 'single-quoted file path'
    r"|"  # or
    r'@\s*"([^"]+)"'  # group 3: @ optional spaces "double-quoted file path"
    r"|"  # or
    r"@\s*([^\s'\"]+)"  # group 4: @ optional spaces unquoted file path (no spaces or quotes)
    r"|"  # or
    r"'([^']*)'"  # group 5: single-quoted value (not a file)
    r"|"  # or
    r'"([^\"]*)"'  # group 6: double-quoted value (not a file)
    r"|"  # or
    r"([^\'\"\s][^=]*?(?=\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=|$))"  # group 7: unquoted value with spaces (not a file)
    r")"  # end of non-capturing group for value
    r"(?=\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=|$)"  # lookahead for next key= or end
)


def parse_dana_input_args(input_strs: list[str] | tuple[str, ...]) -> dict[str, str]:
    """Parse input arguments tuple into a dictionary.

    The inputs have been preliminarily parsed from a string with key-value pairs in various formats such as
     ` this_key= this-value   THAT_KEY  ="  That Other's Value   "  Yet_Another_Key = ' Yet Another Value'  `.

    - the keys are valid_Python_identifier_with_no_spaces_or_special_chars
    - the values are strings that may have spaces and special characters,
      and may be enclosed in single or double quotes

    The parsed output is a dictionary with the keys and values parsed as:
        {
            'this_key': 'this-value',
            'THAT_KEY': "  That Other's Value   ",
            'Yet_Another_Key': ' Yet Another Value',
        }

    Args:
        inputs: A tuple of strings containing key-value pairs in various formats.

    Returns:
        A dictionary mapping keys to their values.

    Example Cases:
        ('this_key=this-value', 'that_key=that-value')
            -> {'this_key': 'this-value', 'that_key': 'that-value'}
        ('this_key', '=', 'this-value', 'that_key', '=', 'that-value')
            -> {'this_key': 'this-value', 'that_key': 'that-value'}
        ('this_key=', 'this-value', 'that_key', '=that-value')
            -> {'this_key': 'this-value', 'that_key': 'that-value'}
        ('this_key=', " this person's value ", "that_key", '=" what that person values "')
            -> {'this_key': " this person's value ", 'that_key': ' what that person values '}

    ---
    @file convention:
        If the value after '=' (with optional spaces) starts with '@', the CLI will treat the following as a
        file path and use the file's contents as the value.
        The file path can be:
            - Unquoted (no spaces): key = @ path/to/file
            - Single-quoted: key = @ 'my long path/file.txt'
            - Double-quoted: key = @ "another path/file.txt"
        Quotes are stripped from the file path before reading. If the file cannot be read, a ValueError is raised.
    """

    def resolve_at_file(value: str, is_file: bool) -> str:
        if is_file:
            file_path = Path(value).expanduser()
            try:
                if value.endswith(".json"):
                    with open(file_path, encoding="utf-8") as f:
                        return json.load(f)

                if value.endswith(".yaml") or value.endswith(".yml"):
                    with open(file_path, encoding="utf-8") as f:
                        return yaml.safe_load(f)

                return file_path.read_text(encoding="utf-8")

            except Exception as e:
                raise ValueError(f"Could not read file for value '@{value}': {e}")

        return value

    input_dict: dict[str, str] = {}

    if len(input_strs) == 1:
        # Single string: use regex finditer to extract all key-value pairs
        for match in DANA_KEY_VALUE_INPUT_PATTERN.finditer(input_strs[0]):
            _key: str = match.group(1)

            # Check for file path groups first
            if (v := match.group(2)) is not None:
                # @'single-quoted file path'
                _value: str = v
                is_file: bool = True

            elif (v := match.group(3)) is not None:
                # @"double-quoted file path"
                _value: str = v
                is_file: bool = True

            elif (v := match.group(4)) is not None:
                # @unquoted file path
                _value: str = v
                is_file: bool = True

            elif (v := match.group(5)) is not None:
                # single-quoted value (not a file)
                _value: str = v
                is_file: bool = False

            elif (v := match.group(6)) is not None:
                # double-quoted value (not a file)
                _value: str = v
                is_file: bool = False

            else:
                # unquoted value (not a file)
                _value: str = v if ((v := match.group(7)) is not None) else ""
                is_file: bool = False

            input_dict[_key] = resolve_at_file(value=_value, is_file=is_file)

        return input_dict

    # Multi-token case: accumulate until '=' is found, then parse key and value
    tokens: list[str] = list(input_strs)
    acc: list[str] = []

    while tokens:
        acc.append(tokens.pop(0))

        # Check if any token in acc contains '='
        eq_index: int = -1
        for i, t in enumerate(acc):
            if "=" in t:
                eq_index: int = i
                break

        if eq_index != -1:
            # Build key and value
            key_value_str: str = "".join(acc[: eq_index + 1])
            key, value = key_value_str.split("=", 1)
            value_right: str = value + "".join(acc[eq_index + 1 :])
            if (value_stripped_str := value_right.strip()) == "":
                continue  # keep accumulating

            # Detect @file convention in multi-token case, allowing optional spaces after @
            if value_stripped_str.startswith("@"):
                after_at: str = value_stripped_str[1:].lstrip()

                if after_at.startswith("'") and after_at.endswith("'"):
                    _value: str = after_at[1:-1]
                    is_file: bool = True

                elif after_at.startswith('"') and after_at.endswith('"'):
                    _value: str = after_at[1:-1]
                    is_file: bool = True

                elif after_at and not any(after_at.startswith(p) for p in ["'", '"']):
                    _value: str = after_at
                    is_file: bool = True

                else:
                    _value: str = value_stripped_str
                    is_file: bool = True

            else:
                _value: str = value_right
                is_file: bool = False

            input_dict[key.strip()] = resolve_at_file(value=_value, is_file=is_file)

            acc: list[str] = []

    return input_dict
