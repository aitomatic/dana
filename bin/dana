#!/bin/bash
# Launch the DANA REPL with variable reference fixes applied
# This script enables self-references like "private.a = private.a + 1" to work correctly

# Find the script directory
script_dir="$(dirname "$(realpath "$0")")"
cd $script_dir/..

# Activate the virtual environment if it exists and not already activated
if [ -f "./VENV.sh" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source ./VENV.sh
fi

# Run the REPL
echo "Starting DANA REPL with variable reference fixes..."
echo "You can now use expressions like 'private.a = private.a + 1'"
exec python opendxa/dana/dana_repl.py "$@"
