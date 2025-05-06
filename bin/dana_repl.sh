#!/bin/bash
script_dir="$(dirname "$(realpath "$0")")"
cd $script_dir/..
exec python opendxa/dana/dana_repl.py
