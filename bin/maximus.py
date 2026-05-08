#!/usr/bin/env python
"""Maximus - Unified entry point.

This is the single command to start Maximus:
    maximus                    # Start interactive session
    maximus --model 14b       # Use specific model
    maximus --verbose          # Show debug info
    maximus --help            # Show help
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maximus.ui.terminal import main

if __name__ == "__main__":
    main()