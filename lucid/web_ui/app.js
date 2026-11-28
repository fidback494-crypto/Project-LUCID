"use strict";

// 브라우저는 화면과 전송만 담당한다. 대화 순서와 실행 상태는 로컬 엔진에서 받는다.
const ui = {
  status: document.querySelector("#status"),
  model: document.querySelector("#model"),
  scroll: document.querySelector("#thread-scroll"),
  timeline: document.querySelector("#timeline"),
  welcome: document.querySelector("#welcome"),
  logs: document.querySelector("#logs"),
  emptyLog: document.querySelector("#empty-log"),
  composer: document.querySelector("#composer"),
  message: document.querySelector("#message"),
  send: document.querySelector("#send"),
  feedback: document.querySelector("#feedback"),
  commands: document.querySelectorAll(".command"),
  menu: document.querySelector("#menu-toggle"),
  sidebar: document.querySelector(".sidebar"),
};

const states = {
  connecting: "연결 중", starting: "엔진 준비 중", ready: "대화 가능",
  busy: "응답 중", stopped: "대화 종료", failed: "시작 실패", offline: "연결 끊김",
};
let engineStatus = "connecting";
let online = false;
let session = "";
let cursor = 0;
let sending = false;
let awaitingState = false;
let mutation = 0;
let draftVersion = 0;
let composing = false;
let pollTimer = null;
let polling = false;
let pollAgain = false;
let lastAssistant = null;
let uncertain = null;

/** 일시적인 전송 문제나 다시 입력해야 하는 이유를 입력란 위에 표시한다. */
function feedback(text) {
  ui.feedback.textContent = text;
  ui.feedback.hidden = !text;
}

/** 전송 가능 상태와 현재 입력값으로 버튼·상태·읽기 전용 여부를 갱신한다. */
function renderControls() {
  const state = !online && engineStatus !== "connecting" ? "offline" : engineStatus;
  const canSend = state === "ready" && !sending && !awaitingState;
  document.body.dataset.state = state;
  const label = sending ? "전송 중" : states[state];
  if (ui.status.textContent !== label) ui.status.textContent = label;
  ui.send.disabled = !canSend || !ui.message.value.trim();
  for (const button of ui.commands) button.disabled = !canSend;
  ui.message.readOnly = state === "stopped" || state === "failed";
}

/** 구조를 만드는 코드와 서버의 문장을 분리해 페이지 본문·모델 출력도 텍스트로 표시한다. */
function addMessage(kind, label, text) {
  const article = document.createElement("article");
  article.className = "message " + kind;
  const heading = document.createElement("h2");
  heading.textContent = label;
  const body = document.createElement("div");
  body.className = "text";
  body.append(document.createTextNode(text));
  article.append(heading, body);
  ui.timeline.append(article);
  ui.welcome.hidden = true;
  return body;
}

/** 같은 명령에서 여러 번 출력한 줄을 하나의 응답으로 합친다. */
function appendEvent(event) {
  if (event.kind === "log") {
    const row = document.createElement("li");
    row.textContent = event.text.trimEnd();
    ui.logs.append(row);
    ui.emptyLog.hidden = true;
    return;
  }
  if (event.kind === "user") {
    addMessage("user", "나", event.text);
    lastAssistant = null;
    if (uncertain && uncertain.session === session && event.id > uncertain.cursor &&
        event.text.trim() === uncertain.text) {
      clearSubmittedDraft(uncertain);
      uncertain = null;
      feedback("");
    }
    return;
  }
  if (event.kind === "error") {
    addMessage("error", "오류", event.text.trim());
    lastAssistant = null;
    return;
  }
  if (event.kind !== "output" || !event.text.trim()) return;
  const prefix = /^\s*LUCID(?:\s*\[([^\]\n]+)\])?\s*>[ \t]*/i.exec(event.text);
  const text = (prefix ? event.text.slice(prefix[0].length) : event.text).trimEnd();
  if (!lastAssistant || prefix) {
    const label = prefix?.[1] ? "LUCID · " + prefix[1] : "LUCID";
    lastAssistant = addMessage("assistant", label, text.trimStart());
  } else {
    lastAssistant.append(document.createTextNode("\n" + text.replace(/^\n/, "")));
  }
}

function clearHistory() {
  ui.timeline.replaceChildren();
  ui.logs.replaceChildren();
  ui.emptyLog.hidden = false;
  ui.welcome.hidden = false;
  lastAssistant = null;
  cursor = 0;
}

/** 대화 세션별 커서 이후의 이벤트만 추가한다. 다른 세션의 커서를 재사용하지 않는다. */
function applyState(data, requestedAfter) {
  if (!Object.hasOwn(states, data.status) || !Array.isArray(data.events) ||
      !Number.isSafeInteger(data.cursor) || typeof data.session !== "string") {
    throw new Error("상태 응답을 읽지 못했습니다.");
  }
  const restarted = session !== "" && session !== data.session;
  if (restarted || data.reset || data.cursor < cursor) clearHistory();
  session = data.session;
  online = true;
  engineStatus = data.status;
  ui.model.textContent = typeof data.model === "string" ? data.model : "";
  ui.model.title = ui.model.textContent;
  ui.model.hidden = !ui.model.textContent;
  if (restarted) {
    uncertain = null;
    feedback("새 엔진 세션에 연결했습니다.");
    if (requestedAfter > 0) {
      pollAgain = true;
      return;
    }
  }

  const follow = !ui.timeline.childElementCount ||
    ui.scroll.scrollHeight - ui.scroll.scrollTop - ui.scroll.clientHeight < 80;
  let added = false;
  for (const event of data.events) {
    if (!Number.isSafeInteger(event.id) || event.id <= cursor || typeof event.text !== "string") continue;
    appendEvent(event);
    cursor = event.id;
    if (event.kind !== "log") added = true;
  }
  cursor = Math.max(cursor, data.cursor);
  if (follow && added) ui.scroll.scrollTop = ui.scroll.scrollHeight;
  awaitingState = false;
  if (uncertain && data.status !== "busy") {
    feedback("전송 결과를 확인할 수 없습니다. 대화 기록을 확인한 뒤 다시 보내세요.");
    uncertain = null;
  }
}

/** 탭이 여러 번 새로고침을 요청해도 상태 요청은 항상 하나씩 실행한다. */
function schedulePoll(delay = 0) {
  if (polling) {
    pollAgain = true;
    return;
  }
  clearTimeout(pollTimer);
  pollTimer = setTimeout(poll, delay);
}

async function poll() {
  polling = true;
  pollAgain = false;
  const requestedAfter = cursor;
  const revision = mutation;
  try {
    const response = await fetch("/api/state?after=" + requestedAfter, {
      cache: "no-store", signal: AbortSignal.timeout(9000),
    });
    if (!response.ok) throw new Error("연결할 수 없습니다.");
    const data = await response.json();
    if (revision === mutation && !sending) applyState(data, requestedAfter);
  } catch {
    if (revision === mutation) {
      online = false;
      engineStatus = "offline";
    }
  } finally {
    polling = false;
    renderControls();
    const interval = !online ? 2200 : document.hidden ? 2600 : 750;
    schedulePoll(pollAgain ? 0 : interval);
  }
}

function clearSubmittedDraft(sent) {
  if (sent.fromDraft && sent.draftVersion === draftVersion) {
    ui.message.value = "";
    draftVersion += 1;
  }
}

/** 서버가 수락한 메시지만 기록에 표시한다. 응답이 유실된 요청은 자동으로 재전송하지 않는다. */
async function sendMessage(value, fromDraft) {
  const text = value.trim();
  if (!text || !online || engineStatus !== "ready" || sending || awaitingState) return;
  if (text.length > 8000) {
    feedback("메시지를 8,000자 이내로 입력하세요.");
    return;
  }
  const sent = {text, fromDraft, draftVersion, cursor, session};
  sending = true;
  mutation += 1;
  feedback("");
  renderControls();
  try {
    const response = await fetch("/api/message", {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-Lucid-Client": "web"},
      body: JSON.stringify({text}),
      signal: AbortSignal.timeout(12000),
    });
    if (response.status === 202) {
      clearSubmittedDraft(sent);
    } else {
      let detail;
      try { detail = (await response.json()).error; } catch { /* 본문이 없는 HTTP 오류 */ }
      feedback(typeof detail === "string" ? detail : "메시지를 보내지 못했습니다.");
    }
  } catch {
    uncertain = sent;
    feedback("전송 결과를 확인하는 중입니다.");
  } finally {
    sending = false;
    awaitingState = true;
    mutation += 1;
    renderControls();
    schedulePoll();
  }
}

ui.composer.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!composing) void sendMessage(ui.message.value, true);
});
ui.message.addEventListener("input", () => {
  draftVersion += 1;
  renderControls();
});
ui.message.addEventListener("compositionstart", () => { composing = true; });
ui.message.addEventListener("compositionend", () => { composing = false; });
ui.message.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey || event.ctrlKey || event.altKey || event.metaKey ||
      event.isComposing || composing || event.keyCode === 229) return;
  event.preventDefault();
  if (!event.repeat) ui.composer.requestSubmit();
});
for (const button of ui.commands) {
  button.addEventListener("click", () => {
    ui.sidebar.classList.remove("expanded");
    ui.menu.setAttribute("aria-expanded", "false");
    void sendMessage(button.dataset.command, false);
  });
}
ui.menu.addEventListener("click", () => {
  const expanded = ui.sidebar.classList.toggle("expanded");
  ui.menu.setAttribute("aria-expanded", String(expanded));
});
document.addEventListener("visibilitychange", () => { if (!document.hidden) schedulePoll(); });
window.addEventListener("online", () => schedulePoll());
renderControls();
schedulePoll();
