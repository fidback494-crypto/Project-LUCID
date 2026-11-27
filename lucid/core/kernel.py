"""엔진의 공통 수명 주기와 실행 순서를 관리한다."""

from lucid.log import Logger


class BaseModule:
    """커널에 등록할 모듈의 기본 수명 주기. 추가 작업이 있는 단계만 재정의한다."""

    def __init__(self, name: str | None = None) -> None:
        """커널에 표시할 이름을 정한다. 생략하면 실제 클래스 이름을 쓴다."""
        self.name = type(self).__name__ if name is None else name
        self.enabled = True

    def start(self) -> None:
        """모듈 시작을 기록한다."""
        Logger.info(f"{self.name} Started")

    def update(self) -> None:
        """한 턴의 갱신 지점. 주기 작업이 있는 모듈이 구현한다."""

    def stop(self) -> None:
        """모듈 종료를 기록한다."""
        Logger.info(f"{self.name} Stopped")


class Kernel:
    """모듈을 등록 순서로 시작하고 역순으로 종료한다."""

    def __init__(self) -> None:
        """등록된 모듈과 실제 시작한 모듈을 각각 추적한다."""
        self.modules = []
        self._started_modules = []

    def register(self, module):
        """module을 등록하고 성공 여부를 반환한다. 같은 이름은 한 번만 등록한다."""
        if any(existing.name == module.name for existing in self.modules):
            Logger.warning(f"Module already registered : {module.name}")
            return False
        self.modules.append(module)
        Logger.info(f"Module Registered : {module.name}")
        return True

    def start(self) -> None:
        """활성 모듈을 시작한다. 실패하면 이미 시작한 모듈을 정리하고 예외를 전달한다."""
        if self._started_modules:
            return

        Logger.info("Kernel Started")

        for module in self.modules:
            if not getattr(module, "enabled", True):
                continue
            self._started_modules.append(module)
            try:
                module.start()
            except Exception as error:
                Logger.error(
                    f"Module start failed : {module.name} ({type(error).__name__})"
                )
                self._stop_started_modules()
                raise

    def update(self) -> None:
        """현재 활성화된 모듈마다 한 번씩 갱신을 요청한다."""
        for module in tuple(self._started_modules):
            if not getattr(module, "enabled", True):
                continue
            try:
                module.update()
            except Exception as error:
                Logger.error(
                    f"Module update failed : {module.name} ({type(error).__name__})"
                )

    def stop(self) -> None:
        """실행 중인 모듈을 등록 역순으로 종료한다."""
        Logger.info("Kernel Stopped")
        self._stop_started_modules()

    def _stop_started_modules(self) -> None:
        """시작된 모듈 목록을 비우면서 각 모듈의 자원을 정리한다."""
        while self._started_modules:
            module = self._started_modules.pop()
            try:
                module.stop()
            except Exception as error:
                Logger.error(
                    f"Module stop failed : {module.name} ({type(error).__name__})"
                )
