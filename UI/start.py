"""
MAGGxDND UI Launcher
Wrapper that calls the root start.py
"""

import os
import sys

# Change to project root
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
os.chdir(root_dir)

# Import and run root start.py
start_script = os.path.join(root_dir, "start.py")
with open(start_script, 'r', encoding='utf-8') as f:
    exec(f.read())
