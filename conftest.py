import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH so `import app` works when pytest is executed
# from different working directories / IDEs.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

