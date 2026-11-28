"""서버 설정과 대화 입력을 받는 Tk 창. 엔진과 네트워크 요청은 별도 프로세스에서 실행한다."""

import multiprocessing
import os
import time
from queue import Empty

from lucid.cli import normalize_server_url
from lucid.interactive import run_engine
from lucid.settings import DEFAULT_OLLAMA_URL


class ChatWindow:
    """대화·작동 기록을 표시하고 Tk의 이벤트 루프에서 엔진 상태를 확인한다."""

    def __init__(self, root, *, debug=False):
        """사용할 Tk 루트와 로그 모드로 창을 만든다. 연결은 사용자가 대화 시작을 누르면 연다."""
        import tkinter as tk
        from tkinter import ttk
        from tkinter.scrolledtext import ScrolledText

        self.root = root
        self.debug = debug
        self.worker = None
        self.commands = self.events = self.stopping = None
        self.ready = False
        self.closing = False
        self.deadline = None
        self.failure = None

        root.title("LUCID")
        root.geometry("760x620")
        root.minsize(460, 420)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        frame = ttk.Frame(root, padding=14)
        frame.grid(sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        settings = ttk.LabelFrame(frame, text="서버 설정", padding=(10, 6))
        settings.grid(row=0, column=0, sticky="ew")
        settings.columnconfigure(1, weight=3)
        settings.columnconfigure(3, weight=1)
        self.ollama = tk.StringVar(value=os.getenv("LUCID_OLLAMA_URL") or DEFAULT_OLLAMA_URL)
        self.tts = tk.StringVar(
            value=os.getenv("LUCID_TTS_URL") or os.getenv("LUCID_UTAUTTS_URL") or ""
        )
        self.token = tk.StringVar()
        self.speaker = tk.StringVar(value=os.getenv("LUCID_TTS_SPEAKER", "Sohee"))
        self.fields = []
        for row, label, variable in (
            (0, "Ollama 주소", self.ollama), (1, "TTS 주소 (선택)", self.tts)
        ):
            ttk.Label(settings, text=label).grid(row=row, column=0, sticky="w")
            field = ttk.Entry(settings, textvariable=variable, width=28)
            field.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=2)
            self.fields.append(field)
        ttk.Label(settings, text="TTS 토큰").grid(row=2, column=0, sticky="w")
        password = ttk.Entry(settings, textvariable=self.token, show="•", width=14)
        password.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=2)
        ttk.Label(settings, text="화자").grid(row=2, column=2, padx=(10, 4))
        speaker = ttk.Entry(settings, textvariable=self.speaker, width=10)
        speaker.grid(row=2, column=3, sticky="ew")
        self.fields.extend((password, speaker))

        toolbar = ttk.Frame(frame)
        toolbar.grid(row=1, column=0, sticky="ew", pady=7)
        toolbar.columnconfigure(1, weight=1)
        self.connect = ttk.Button(toolbar, text="대화 시작", command=self.start)
        self.connect.grid(row=0, column=0)
        self.status = tk.StringVar(value="연결 전")
        ttk.Label(toolbar, textvariable=self.status, wraplength=420).grid(
            row=0, column=1, sticky="w", padx=(10, 0)
        )

        notebook = ttk.Notebook(frame)
        notebook.grid(row=2, column=0, sticky="nsew")
        self.history = ScrolledText(notebook, wrap="word", state="disabled", padx=8, pady=8)
        self.log = ScrolledText(notebook, wrap="word", state="disabled", padx=8, pady=8)
        notebook.add(self.history.frame, text="대화")
        notebook.add(self.log.frame, text="작동 기록")

        composer = ttk.Frame(frame)
        composer.grid(row=3, column=0, sticky="ew", pady=(9, 0))
        composer.columnconfigure(1, weight=1)
        ttk.Label(composer, text="메시지").grid(row=0, column=0, padx=(0, 6))
        self.message = tk.StringVar()
        self.entry = ttk.Entry(composer, textvariable=self.message)
        self.entry.grid(row=0, column=1, sticky="ew")
        self.entry.bind("<Return>", self.send)
        self.submit = ttk.Button(composer, text="전송", command=self.send, state="disabled")
        self.submit.grid(row=0, column=2, padx=(6, 0))
        root.after(50, self._poll)

    @staticmethod
    def _append(widget, text):
        """읽기 전용 기록에 문자열을 추가하고 가장 최근 줄을 표시한다."""
        widget.configure(state="normal")
        widget.insert("end", text)
        widget.see("end")
        widget.configure(state="disabled")

    def _set_settings(self, editable):
        """연결 전이나 재시도 시에만 서버 설정을 수정할 수 있게 한다."""
        state = "normal" if editable else "disabled"
        for field in self.fields:
            field.configure(state=state)
        self.connect.configure(state=state)

    def start(self):
        """입력 주소를 검증하고 엔진 프로세스를 시작한다. 네트워크 작업은 기다리지 않는다."""
        if self.worker is not None or self.closing:
            return
        try:
            ollama = normalize_server_url(self.ollama.get() or DEFAULT_OLLAMA_URL)
            tts = normalize_server_url(self.tts.get()) if self.tts.get().strip() else None
        except ValueError as error:
            self.status.set(str(error))
            return

        context = multiprocessing.get_context("spawn")
        self.commands, self.events = context.Queue(), context.Queue()
        self.stopping = context.Event()
        worker = context.Process(
            target=run_engine,
            args=((ollama, tts, self.token.get(), self.speaker.get()),
                  self.debug, self.commands, self.events, self.stopping),
            name="LUCIDChatEngine",
        )
        try:
            worker.start()
        except (OSError, RuntimeError) as error:
            self._release_queues()
            self.status.set(f"시작하지 못했어. {error}")
            return
        self.worker = worker
        self.failure = None
        self._set_settings(False)
        self.status.set("엔진과 서버를 준비하는 중…")

    def send(self, _event=None):
        """입력란의 문장을 대화 기록과 작업 큐에 한 번 추가한다. Enter도 같은 동작이다."""
        text = self.message.get().strip()
        if self.ready and text and not self.closing:
            self.ready = False
            self.submit.configure(state="disabled")
            self.message.set("")
            self._append(self.history, f"나 > {text}\n")
            self.status.set("응답을 기다리는 중…")
            self.commands.put(text)
        return "break"

    def close(self):
        """대기 중인 작업을 해제하고 정상 종료를 먼저 요청한다."""
        if self.closing:
            return
        self.closing = True
        self.ready = False
        if self.worker is None:
            self.root.destroy()
            return
        self._set_settings(False)
        self.submit.configure(state="disabled")
        self.status.set("연결을 닫는 중…")
        self.stopping.set()
        self.commands.put(None)
        self.deadline = time.monotonic() + 6

    def _drain_events(self):
        """한 번에 제한된 수의 출력·상태 이벤트를 반영해 입력 이벤트가 밀리지 않게 한다."""
        for _ in range(100):
            try:
                kind, text = self.events.get_nowait()
            except Empty:
                return True
            if kind == "output":
                self._append(self.history, text)
            elif kind == "log":
                self._append(self.log, text)
            elif kind == "ready" and not self.closing:
                self.ready = True
                self.status.set("대화 가능")
                self.submit.configure(state="normal")
                self.entry.focus_set()
            elif kind == "failed":
                self.failure = text
                self._append(self.log, f"시작 실패: {text}\n")
            elif kind == "quit":
                self.close()
        return False

    def _release_queues(self):
        """종료한 작업 프로세스와 통신하던 두 큐를 닫는다."""
        for channel in (self.commands, self.events):
            channel.cancel_join_thread()
            channel.close()
        self.commands = self.events = self.stopping = None

    def _poll(self):
        """작업 상태를 확인하고, 종료 요청 후 응답이 없는 프로세스만 제한 시간 뒤 중단한다."""
        if self.worker is not None:
            alive = self.worker.is_alive()
            drained = self.deadline == 0 or self._drain_events()
            if alive and self.closing and self.deadline and 0 < self.deadline <= time.monotonic():
                self.worker.terminate()
                self.deadline = 0
            if not alive and drained:
                self.worker.join()
                code = self.worker.exitcode
                self.worker.close()
                self.worker = None
                self._release_queues()
                if self.closing:
                    self.root.destroy()
                    return
                self.ready = False
                self.submit.configure(state="disabled")
                self._set_settings(True)
                self.status.set(f"시작 실패: {self.failure}" if self.failure else f"엔진 종료 ({code})")
        self.root.after(50, self._poll)


def main(*, debug: bool = False) -> None:
    """GUI 모드의 데스크톱 창을 열고 창과 작업 프로세스가 종료될 때까지 이벤트를 처리한다."""
    try:
        import tkinter as tk
    except ImportError as error:
        raise SystemExit(
            "Tk를 불러올 수 없습니다. 현재 Python에 맞는 Tk 패키지를 설치하거나 "
            "main.py의 GUI = False로 터미널 대화를 실행하세요."
        ) from error
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise SystemExit(
            f"데스크톱 창을 열지 못했습니다 ({error}). 그래픽 데스크톱에서 실행하거나 "
            "main.py의 GUI = False로 터미널 대화를 실행하세요."
        ) from error
    window = ChatWindow(root, debug=debug)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        window.close()
        if window.worker is not None:
            root.mainloop()
