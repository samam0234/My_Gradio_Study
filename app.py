"""Hugging Face Spaces와 로컬 최종 실행의 입구."""

from apps.project_app import build
from apps.runtime import launch

demo = build()

if __name__ == "__main__":
    launch(demo)
