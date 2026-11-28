"""저장소 루트에서 LUCID의 콘솔, 데스크톱 창 또는 로컬 웹 화면을 실행한다."""

# True이면 모델·기억·도구의 상세 로그를 함께 표시한다.
DEBUG = False
# True이면 터미널 대신 데스크톱 창을 연다.
GUI = False
# True이면 로컬 웹 화면을 연다. 웹 포트는 확장 프로그램의 브리지 포트와 별개다.
WEB = False
WEB_PORT = 8787


def main(
    gui: bool | None = None,
    *,
    web: bool | None = None,
    port: int | None = None,
    open_browser: bool = True,
) -> None:
    """명시한 화면을 실행한다. 인자가 없으면 이 파일의 WEB, GUI 순으로 설정을 적용한다."""
    use_web = (WEB and gui is None) if web is None else web
    if use_web:
        from lucid.web import main as launch_web

        launch_web(
            debug=DEBUG,
            port=WEB_PORT if port is None else port,
            open_browser=open_browser,
        )
        return

    use_window = GUI if gui is None else gui
    if use_window:
        from lucid.gui import main as launch
    else:
        from lucid.cli import main as launch

    launch(debug=DEBUG)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="LUCID 콘솔, 데스크톱 창 또는 로컬 웹 화면을 엽니다."
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=("WEB=True", "WEB=False", "GUI=True", "GUI=False"),
        help="이번 실행에 사용할 화면을 선택합니다.",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="웹 서버의 로컬 포트. 0은 사용 가능한 포트를 선택합니다.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="웹 주소만 표시하고 브라우저 자동 열기를 생략합니다.",
    )
    args = parser.parse_args()
    gui = {"GUI=True": True, "GUI=False": False}.get(args.mode)
    web = {"WEB=True": True, "WEB=False": False}.get(args.mode)
    if args.port is not None and not 0 <= args.port <= 65535:
        parser.error("--port는 0~65535 사이의 정수여야 합니다.")
    if (args.port is not None or args.no_browser) and not (
        web or (args.mode is None and WEB)
    ):
        parser.error("--port와 --no-browser는 WEB=True로 실행할 때 사용할 수 있습니다.")
    main(gui=gui, web=web, port=args.port, open_browser=not args.no_browser)
