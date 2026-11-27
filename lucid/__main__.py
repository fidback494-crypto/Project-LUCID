"""python -m lucid에서도 프로젝트 실행기의 DEBUG 설정을 사용한다."""

from pathlib import Path
from runpy import run_path

if __name__ == "__main__":
    launcher = Path(__file__).resolve().parent.parent / "main.py"
    run_path(str(launcher), run_name="__main__")
