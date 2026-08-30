"""
FitQuest Backend Application Entry Point
Acts as the central backend API server coordinating workout management, scoring, hardware/Arduino integration, and communication with the exercise recognition model.
"""

import os
import sys

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    print("FitQuest Backend Service Placeholder Running...")
    print("This module will manage API routes, workout sets, points calculation, and Arduino hardware signals.")


if __name__ == "__main__":
    main()
