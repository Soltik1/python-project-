import os
import sys

# Ensure project root is on sys.path so 'core' package is importable when running pytest from repo root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
