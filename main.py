"""저장소 루트에서 python main.py로 대화 콘솔을 실행한다."""

from lucid.cli import main as run_console

# True이면 모델·기억·도구의 상세 로그를 함께 표시한다.
DEBUG = False


def main() -> None:
    """이 파일의 DEBUG 설정으로 대화 콘솔을 실행한다."""
    run_console(debug=DEBUG)


if __name__ == "__main__":
    main()
