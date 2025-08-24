import argparse
import json
from pathlib import Path
import re

from dana.core.lang.dana_sandbox import DanaSandbox


from .dana_input_args_parser import parse_dana_input_args

MAIN_FUNC_NAME: str = "__main__"
# Regex pattern to match "def __main__(" at the beginning of a line with zero whitespace before "def"
DEF_MAIN_PATTERN: re.Pattern = re.compile(r"^def\s+__main__\s*\(")


def main():
    """
    CLI entry point for running a Dana .na script with input arguments.
    Usage: dana2 <file.na> [key1=val1 key2=val2 ...]
    """
    arg_parser = argparse.ArgumentParser(description="Run a Dana .na script with input arguments.")
    arg_parser.add_argument("file_path", type=str, help="Path to the .na file to execute")
    arg_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    arg_parser.add_argument("inputs", nargs=argparse.REMAINDER, help="Input arguments as key=value pairs")
    args = arg_parser.parse_args()

    # TODO: fix bug with --debug handling
    if "--debug" in args.inputs:
        args.debug = True
        args.inputs.remove("--debug")

    # load the .env file if it exists in the same directory as the script
    # Note: Environment loading is now handled automatically by initlib startup

    # Get the file's directory for module search paths
    file_dir = str(Path(args.file_path).parent.resolve())

    with open(args.file_path, encoding="utf-8") as f:
        source_code = f.read()

    # if there is a special `def __main__(...)` function, run it with the input arguments
    if any(DEF_MAIN_PATTERN.search(line) for line in source_code.splitlines()):
        # Parse input arguments into a dictionary
        input_dict = parse_dana_input_args(args.inputs)

        # append source code
        source_code_with_main_call = f"""
{source_code}

{MAIN_FUNC_NAME}({
            ", ".join(
                [
                    f"{key}={
                        json.dumps(
                            obj=value,
                            skipkeys=False,
                            ensure_ascii=False,
                            check_circular=True,
                            allow_nan=False,
                            cls=None,
                            indent=None,
                            separators=None,
                            default=None,
                            sort_keys=False,
                        )
                    }"
                    for key, value in input_dict.items()
                ]
            )
        })
"""

        # run the appended source code with custom search paths
        DanaSandbox.execute_string_once(
            source_code=source_code_with_main_call, filename=args.file_path, debug_mode=args.debug, module_search_paths=[file_dir]
        )
    # otherwise, run the script
    else:
        # For regular file execution, we can rely on execute_file to set up the search paths
        DanaSandbox.execute_file_once(file_path=args.file_path, debug_mode=args.debug)
