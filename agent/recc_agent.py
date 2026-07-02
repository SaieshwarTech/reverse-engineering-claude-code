#!/usr/bin/env python3
"""Standalone launcher — real code lives in recc_cli/agent.py."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from recc_cli.agent import main
if __name__ == "__main__":
    main()
