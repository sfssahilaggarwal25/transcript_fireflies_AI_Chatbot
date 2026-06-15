"""Wrapper to run reingest_dg_only --all with explicit stdout flushing."""
import sys
import os
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, ".")
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from reingest_dg_only import main
main()
