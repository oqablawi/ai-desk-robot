"""Launch from any directory with: py run_simulator.py"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from robot_display.__main__ import main

if __name__ == "__main__":
    main()
