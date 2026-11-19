import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.midpoint_app import build
from apps.runtime import launch

if __name__ == "__main__":
    launch(build())
