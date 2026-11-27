import { drawFrame, openDesktopStream, postToBridge } from "./capture.js";

let activeSession = null;
let generation = 0;

const sampleCanvas = document.createElement("canvas");
sampleCanvas.width = 48;
sampleCanvas.height = 27;
const sampleContext = sampleCanvas.getContext("2d", {
  willReadFrequently: true
});

/** 캔버스 이미지를 낮은 해상도의 밝기 표본으로 바꾼다. */
function sampleFrame(canvas) {
  sampleContext.drawImage(
    canvas,
    0,
    0,
    sampleCanvas.width,
    sampleCanvas.height
  );

  const rgba = sampleContext.getImageData(
    0,
    0,
    sampleCanvas.width,
    sampleCanvas.height
  ).data;
  const grayscale = new Uint8Array(sampleCanvas.width * sampleCanvas.height);

  for (let source = 0, target = 0; source < rgba.length; source += 4, target += 1) {
    grayscale[target] = Math.round(
      0.299 * rgba[source] +
      0.587 * rgba[source + 1] +
      0.114 * rgba[source + 2]
    );
  }

  return grayscale;
}

/** 두 장면의 밝기 차이가 커서 새 프레임을 보낼 필요가 있는지 판정한다. */
function hasMeaningfulPixelChange(previous, current) {
  if (!previous) {
    return true;
  }

  let changedSamples = 0;
  let totalDifference = 0;

  for (let index = 0; index < current.length; index += 1) {
    const difference = Math.abs(current[index] - previous[index]);
    totalDifference += difference;

    if (difference >= 24) {
      changedSamples += 1;
    }
  }

  const changedFraction = changedSamples / current.length;
  const meanDifference = totalDifference / current.length;

  // 커서 깜박임은 제외하고 창 전환이나 본문 변화만 보낸다.
  return changedFraction >= 0.006 && meanDifference >= 0.8;
}

/** 처리 중인 전송이 없고 화면이 달라졌을 때만 현재 세션의 JPEG 한 장을 보낸다. */
async function sendFrame(session) {
  if (session !== activeSession || session.pending) return;
  drawFrame(session.video, session.canvas, 1280);
  const frame = sampleFrame(session.canvas);
  if (!hasMeaningfulPixelChange(session.lastFrame, frame)) return;

  session.pending = postToBridge(session.connection, "context", {
    session_id: session.id,
    title: "사용자가 이어서 공유한 화면 또는 창",
    url: "",
    text: "",
    selection: "",
    image_base64: session.canvas.toDataURL("image/jpeg", 0.68).split(",")[1],
    image_mime: "image/jpeg",
    continuous: true
  });
  try {
    await session.pending;
    session.lastFrame = frame;
  } finally {
    session.pending = null;
  }
}

/** 캡처 장치를 즉시 해제하고 마지막 전송이 끝나면 브리지에 이 세션의 종료를 알린다. */
async function closeSession(session) {
  if (!session) return;
  if (activeSession === session) activeSession = null;
  clearInterval(session.timer);
  for (const track of session.stream?.getTracks() || []) {
    track.onended = null;
    track.stop();
  }
  session.video.pause();
  session.video.srcObject = null;

  try {
    await session.pending;
  } catch {
    // 실패한 프레임도 종료 통지를 가로막지 않는다.
  }
  await postToBridge(session.connection, "stop", { session_id: session.id });
}

/** 아직 권한을 기다리는 시작 요청도 무효화하고 현재 캡처를 종료한다. */
async function stopObserving() {
  generation += 1;
  await closeSession(activeSession);
}

/** 사용자가 선택한 장치와 연결 설정으로 새 세션을 열고 3초마다 변화를 확인한다. */
async function startObserving(options) {
  const requested = ++generation;
  await closeSession(activeSession);
  if (requested !== generation) throw new Error("관찰 시작이 취소됐어.");

  const session = {
    id: crypto.randomUUID(),
    connection: options,
    video: document.createElement("video"),
    canvas: document.createElement("canvas"),
    stream: null,
    timer: null,
    lastFrame: null,
    pending: null
  };
  activeSession = session;

  try {
    const stream = await openDesktopStream(options.streamId);
    if (activeSession !== session) {
      stream.getTracks().forEach(track => track.stop());
      throw new Error("관찰 시작이 취소됐어.");
    }
    session.stream = stream;
    const [track] = stream.getVideoTracks();
    track.onended = () => {
      if (activeSession === session) stopObserving().catch(console.error);
    };
    session.video.muted = true;
    session.video.playsInline = true;
    session.video.srcObject = stream;
    await session.video.play();
    await sendFrame(session);
    if (activeSession !== session) throw new Error("관찰 시작이 취소됐어.");
    session.timer = setInterval(() => {
      sendFrame(session).catch(error => {
        console.error("화면 공유 오류", error);
        if (activeSession === session) stopObserving().catch(console.error);
      });
    }, 3000);
  } catch (error) {
    if (activeSession === session) {
      await closeSession(session).catch(console.error);
    }
    throw error;
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.target !== "offscreen") return;
  let operation;
  if (message.type === "lucid-start-observing") {
    operation = startObserving(message.options);
  } else if (message.type === "lucid-stop-observing") {
    operation = stopObserving();
  } else {
    return;
  }
  operation.then(
    () => sendResponse({ ok: true }),
    error => sendResponse({ ok: false, error: error.message })
  );
  return true;
});
