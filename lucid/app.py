"""대화 엔진의 조립, 콘솔 명령 처리, 서비스 수명 관리를 담당한다."""

from threading import RLock, Thread

from lucid.actions.engine import ActionEngine
from lucid.actions.tools.calculator import CalculatorTool
from lucid.actions.tools.files import FileTool
from lucid.actions.tools.memory import MemoryTool
from lucid.actions.tools.python import PythonTool
from lucid.actions.tools.time import TimeTool
from lucid.actions.tools.web import WebTool
from lucid.autonomy import AutonomousEngine
from lucid.browser import BrowserBridge, PageContextStore
from lucid.cognition.engine import CognitiveEngine
from lucid.conversation import ConversationManager
from lucid.core.kernel import Kernel
from lucid.core.workspace import WorkspaceEngine
from lucid.emotion.engine import EmotionEngine
from lucid.language.engine import LanguageEngine
from lucid.life.loop import LifeLoop
from lucid.life.signals import Consciousness, Heartbeat
from lucid.log import Logger
from lucid.memory.facts import MemoryExtractor
from lucid.memory.search import MemorySearch
from lucid.memory.store import LongTermMemory
from lucid.memory.working import WorkingMemory
from lucid.mind.decisions import DecisionEngine
from lucid.mind.feedback import ExperienceEngine, ReflectionEngine
from lucid.mind.goals import GoalEngine
from lucid.mind.observation import ObservationEngine
from lucid.mind.planning import PlanningEngine
from lucid.mind.reasoning import ReasoningEngine
from lucid.mind.thinking import ThoughtEngine
from lucid.persona import SelfModel
from lucid.vision import VisionEngine, VisualPresence
from lucid.voice import KoreanTTSClient


class LucidEngine:
    """한 세션의 서비스, 사용자 대화와 백그라운드 관찰을 관리한다."""

    def __init__(self, output=None):
        """모듈과 저장소를 연결하고 명령 결과와 답변을 보낼 출력 함수를 지정한다."""
        self.output = print if output is None else output
        self.action = ActionEngine()
        self.action.register("calculator", CalculatorTool())
        self.action.register("file", FileTool())
        self.action.register("python", PythonTool())
        self.action.register("web", WebTool())

        self.workspace = WorkspaceEngine()

        self.kernel = Kernel()
        self.conversation = ConversationManager()

        self.heartbeat = Heartbeat()
        self.consciousness = Consciousness()

        self.self_model = SelfModel()
        self.experience = ExperienceEngine()

        self.observation = ObservationEngine()

        self.memory = WorkingMemory()
        self.long_memory = LongTermMemory()
        self.action.register("memory", MemoryTool(self.long_memory))
        self.action.register("time", TimeTool())
        self.extractor = MemoryExtractor()
        self.search = MemorySearch(self.long_memory)

        self.emotion = EmotionEngine()
        self.cognitive = CognitiveEngine()
        self.browser_context = PageContextStore()
        self.browser_bridge = BrowserBridge(self.browser_context)
        self.vision = VisionEngine()
        self.voice = KoreanTTSClient()
        self._life_lock = RLock()
        self.visual_presence = VisualPresence(
            self.browser_context,
            self.vision,
            self._on_visual_observation,
        )
        self.autonomy = AutonomousEngine(
            self.self_model,
            self.long_memory,
        )

        self.reasoning = ReasoningEngine()
        self.goal = GoalEngine()
        self.thought = ThoughtEngine()
        self.planning = PlanningEngine()
        self.decision = DecisionEngine()

        self.language = LanguageEngine()

        self.reflection = ReflectionEngine()

        self.life = LifeLoop(
            conversation_manager=self.conversation,
            observation_engine=self.observation,
            emotion_engine=self.emotion,
            working_memory=self.memory,
            reasoning_engine=self.reasoning,
            thought_engine=self.thought,
            goal_engine=self.goal,
            planning_engine=self.planning,
            decision_engine=self.decision,
            language_engine=self.language,
            reflection_engine=self.reflection,
            experience_engine=self.experience,
            self_model=self.self_model,
            long_memory=self.long_memory,
            extractor=self.extractor,
            search=self.search,
            workspace_engine=self.workspace,
            action_engine=self.action,
            cognitive_engine=self.cognitive,
            browser_context_store=self.browser_context,
        )

        self.running = False
        self._shutdown_complete = False
        self._shutdown_started = False

    def boot(self):
        """등록 순서대로 커널과 주변 서비스를 시작하고 대화 입력을 활성화한다."""
        Logger.info("========== LUCID BOOT ==========")
        for module in (
            self.workspace,
            self.action,
            self.heartbeat,
            self.consciousness,
            self.observation,
            self.memory,
            self.emotion,
            self.cognitive,
            self.autonomy,
            self.reasoning,
            self.goal,
            self.thought,
            self.planning,
            self.decision,
            self.language,
            self.reflection,
            self.experience,
        ):
            self.kernel.register(module)

        self.kernel.start()
        self.voice.start()
        self.browser_bridge.start()
        self.running = True
        self.visual_presence.start()

        Logger.info("LUCID is Alive.")

    def run(self):
        """한 줄씩 명령이나 대화를 처리하며 EOF·중단·종료 명령으로 세션을 닫는다."""
        while self.running:
            try:
                if not self.handle_input(input("\n시드 > ")):
                    break
            except (EOFError, KeyboardInterrupt):
                break
        self.shutdown()

    def handle_input(self, user: str) -> bool:
        """콘솔이나 창에서 받은 한 줄을 처리한다. 종료 요청이면 False를 반환한다."""
        user = user.strip()
        if not user:
            return True
        if user.lower() in {"exit", "quit"}:
            return False
        try:
            self.autonomy.note_interaction()
            self._dispatch(user)
        except Exception as error:
            Logger.notice("입력을 처리하지 못했어. 다시 시도해 줘.")
            Logger.error(str(error))
        return True

    def _dispatch(self, user):
        """콘솔 입력을 해당 명령으로 보내거나 일반 대화로 처리한다."""
        command = user.partition(" ")[0]
        if command == "/memory":
            self._memory_command(user)
            return
        if command in {"/page", "/page-think"}:
            self._page_command(user)
            return
        if command in {"/screen", "/screen-think"}:
            self._screen_command(user)
            return
        if user == "/count":
            self.output(f"\nMemory Count : {self.long_memory.count()}")

            return

        if user == "/tools":
            self.output("\n========== Registered Tools ==========")
            self.output(", ".join(self.action.registry.names()))
            self.output(
                "파일 도구는 프로젝트 안의 읽기 전용, Python 도구는 안전한 표현식만 실행해."
            )

            return

        if user == "/inner":
            self.output("\n========== Inner Life ==========")

            experiences = self.long_memory.recent_inner_experiences()

            if not experiences:
                self.output("아직 기록된 자율 내적 경험이 없습니다.")

            for experience in experiences:
                self.output(f"- {experience['name']}: {experience['meaning']}")

            return

        if user == "/goal":
            self.output("\n========== Autonomous Goal ==========")

            goal = self.self_model.autonomous_goal

            if goal is None:
                self.output("아직 형성된 자율 목표가 없습니다.")

            else:
                self.output(goal.describe())

            return

        if user == "/working":
            self.output("\n========== Working Memory ==========")

            for item in self.memory.recent():
                self.output(item)

            return

        if user == "/status":
            inner_life = self.self_model.emotion

            self.output("\n========== STATUS ==========")
            self.output("Working Memory :", self.memory.size())
            self.output("Long Memory    :", self.long_memory.count())
            self.output("Identity       :", self.self_model.identity.name)

            self.output("Inner Life     :", inner_life.summary())

            return

        self._respond(user)

    def _memory_command(self, user):
        """기억 조회·검색·이력·삭제 명령의 결과를 콘솔에 표시한다."""
        if user == "/memory":
            self.output("\n========== Long Memory ==========")

            memories = self.long_memory.all()

            if not memories:
                self.output("저장된 장기 기억이 없어.")

            for memory in memories:
                self.output(
                    f"#{memory['id']} [{memory['predicate']}] "
                    f"{memory['content']} "
                    f"(신뢰도 {memory['confidence']:.2f})"
                )

            return

        if user.startswith("/memory "):
            command = user.removeprefix("/memory ").strip()
            action, _, argument = command.partition(" ")

            if action == "search" and argument.strip():
                results = self.search.search(argument.strip())
                self.output("\n========== Memory Search ==========")

                if not results:
                    self.output("관련 기억을 찾지 못했어.")

                for result in results:
                    self.output("-", result)

            elif action == "canon":
                self.output("\n========== LUCID Official Setting ==========")
                self.output(self.self_model.identity.persona_prompt())

            elif action == "last":
                last = self.long_memory.last_conversation_gap()
                self.output("\n========== Last Conversation ==========")
                self.output(f"기록 시각: {last['last_at']}")
                self.output(f"경과: {last['elapsed_text']}")
                if last.get("is_approximate"):
                    self.output(
                        "주의: 대화 로그가 아닌 내적 경험 시각으로 추정한 값이야."
                    )

            elif action == "history":
                self.output("\n========== Memory History ==========")
                memories = self.long_memory.all(include_history=True)

                if not memories:
                    self.output("기억 이력이 없어.")

                for memory in memories:
                    self.output(
                        f"#{memory['id']} [{memory['status']}] {memory['content']}"
                    )

            elif action == "sessions":
                sessions = self.long_memory.session_summaries(
                    argument.strip(), limit=10
                )
                if not sessions:
                    self.output("아직 압축된 대화가 없어.")
                for session in sessions:
                    self.output(
                        f"#{session['id']} · {session['started_at']} · {session['turn_count']}턴\n{session['summary']}"
                    )

            elif action == "session":
                try:
                    session_id = int(argument.strip())
                    if not 1 <= session_id <= 2**63 - 1:
                        raise ValueError
                except ValueError:
                    self.output("사용법: /memory session <세션 번호>")
                    return
                self._show_episodes(self.long_memory.session_episodes(session_id))

            elif action == "episodes":
                self._show_episodes(self.long_memory.recent_conversation_episodes(10))

            elif action == "delete":
                try:
                    memory_id = int(argument.strip())
                except ValueError:
                    self.output("\n사용법: /memory delete <기억 번호>")
                    return

                if self.long_memory.delete(memory_id):
                    self.output(f"\n기억 #{memory_id}을 목록에서 삭제했어.")
                else:
                    self.output("\n해당 번호의 활성 기억을 찾지 못했어.")

            else:
                self.output(
                    "\n기억 명령: /memory, /memory canon, /memory last, "
                    "/memory search <질문>, "
                    "/memory history, /memory episodes, "
                    "/memory sessions [검색어], /memory session <번호>, /memory delete <번호>"
                )

            return

    def _show_episodes(self, episodes):
        """조회한 대화 원문을 시각·화자와 함께 현재 출력 환경에 표시한다."""
        if not episodes:
            self.output("표시할 대화 기록이 없어.")
        for episode in episodes:
            self.output(
                f"\n#{episode['id']} {episode['created_at']} [{episode['intent']}]\n"
                f"시드: {episode['user_text']}\nLUCID: {episode['assistant_text']}"
            )

    def _page_command(self, user):
        """마지막으로 공유한 웹페이지 정보를 표시하거나 그 본문으로 질문에 답한다."""
        page = self.browser_context.latest_page()
        if page is None:
            self.output("\n먼저 브라우저에서 페이지를 공유해 줘.")
            return
        if user == "/page":
            self.output("\n========== Shared Page ==========")
            self.output("Title :", page.title or "(제목 없음)")
            self.output("URL   :", page.url)
            self.output("Selected text :", page.selection or "(없음)")
            return
        if user == "/page-think":
            question = "사용자가 공유한 현재 웹페이지를 보고, 사실을 꾸며내지 말고 LUCID로서 짧은 혼잣말을 해 줘."
        else:
            question = (
                "사용자가 공유한 현재 웹페이지의 내용만 바탕으로 답해 줘. 질문: "
                + user.partition(" ")[2].strip()
            )
        self._respond(question, allow_tools=False, conversation_text=user)

    def _screen_command(self, user):
        """공유 화면 상태를 표시하거나 해당 캡처의 관찰 결과로 질문에 답한다."""
        page = self.browser_context.latest_screen()
        if page is None or not page.has_image:
            self.output("\n먼저 브라우저 확장에서 ‘화면 또는 창 공유’를 눌러 줘.")
            return
        if user == "/screen":
            self.output("\n========== Shared Screen ==========")
            self.output("Source :", page.title or "공유된 화면")
            self.output("Captured at :", page.received_at.strftime("%H:%M:%S"))
            return
        think = user == "/screen-think"
        question = (
            "이 화면에서 실제로 보이는 내용과 분위기를 관찰해 줘."
            if think
            else user.partition(" ")[2].strip()
        )
        with self.autonomy.interaction():
            observation = self.vision.observe(page, question)
            if not observation:
                self.output(
                    "\n화면을 분석하지 못했어. 설정한 Ollama 비전 모델을 확인해 줘."
                )
                return
            self._respond(
                question,
                visual_observation=observation,
                allow_tools=False,
                conversation_text=user,
            )

    def _respond(
        self,
        user,
        *,
        visual_observation="",
        allow_tools=True,
        record_dialogue=True,
        conversation_text=None,
        label="LUCID >",
    ):
        """입력과 선택적 화면 관찰을 처리하고 같은 턴의 문장·음성 스타일을 전달한다."""
        with self.autonomy.interaction():
            with self._life_lock:
                if not self.running:
                    return
                self.kernel.update()
                reply = self.life.process(
                    user,
                    visual_observation=visual_observation,
                    allow_tools=allow_tools,
                    record_dialogue=record_dialogue,
                    conversation_text=conversation_text,
                )
                workspace = self.workspace.current()
                speech = workspace.voice_response or reply
                style = workspace.speech_style
            self._present_reply(
                reply, label=label, voice_reply=speech, speech_style=style
            )

    def shutdown(self):
        """백그라운드 처리와 세션 자원을 종료한다. 반복 호출해도 안전하다."""
        if self._shutdown_started:
            return
        self._shutdown_started = True
        self.running = False
        Logger.info("Shutting Down...")
        self.visual_presence.stop()
        self.browser_bridge.stop()
        if self._life_lock.acquire(timeout=2):
            try:
                self._close_services()
            finally:
                self._life_lock.release()
        else:
            # 관찰 요청이 HTTP 응답을 기다리는 동안에는 사용 중인 세션을 닫지 않는다.
            Thread(
                target=self._finish_shutdown, name="lucid-cleanup", daemon=True
            ).start()

    def _finish_shutdown(self):
        """진행 중이던 관찰의 자원 사용이 끝나면 남은 서비스를 정리한다."""
        with self._life_lock:
            self._close_services()

    def _close_services(self):
        """커널을 멈추고 음성·비전·기억 연결을 각각 정리한다."""
        self.kernel.stop()
        for name, close in (
            ("voice", self.voice.stop),
            ("vision", self.vision.close),
            ("memory", self.long_memory.close),
        ):
            try:
                close()
            except Exception as error:
                Logger.warning(
                    f"[Shutdown] {name} cleanup failed: {type(error).__name__}"
                )
        self._shutdown_complete = True

    def _on_visual_observation(self, observation):
        """자동 화면 변화에 응답한다. 관찰자가 만든 지시는 사용자 발화로 저장하지 않는다."""
        try:
            self._respond(
                "시야에 변화가 있었어. 방금 본 장면을 바탕으로 LUCID답게 "
                "한두 문장의 짧은 혼잣말을 해 줘. 사용자의 행동이나 의도를 "
                "단정하지 말고, 보이는 사실만 말해.",
                visual_observation=observation,
                allow_tools=False,
                record_dialogue=False,
                label="LUCID [beside you] >",
            )
        except Exception as error:
            Logger.error(f"[Vision Presence] {error}")

    def _present_reply(
        self, reply, label="LUCID >", voice_reply=None, speech_style="neutral"
    ):
        """답변을 먼저 출력하고 이 턴의 음성 문장과 스타일을 재생 대기열로 보낸다."""
        self.output(f"\n{label} {reply}")
        speech = voice_reply or reply
        enqueue = getattr(self.voice, "speak_async", None)
        if callable(enqueue):
            enqueue(speech, style=speech_style)
        else:
            self.voice.speak(speech, style=speech_style)
