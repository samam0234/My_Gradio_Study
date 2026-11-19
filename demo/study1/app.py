import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.hello import build
from apps.runtime import launch

if __name__ == "__main__":
    launch(build())
