let stream = null;
let timer = null;
let activeOptions = null;
let lastSentFrame = null;
let captureInFlight = null;

const video = document.createElement("video");
video.muted = true;
video.playsInline = true;

const frameCanvas = document.createElement("canvas");
const sampleCanvas = document.createElement("canvas");
sampleCanvas.width = 48;
sampleCanvas.height = 27;
const sampleContext = sampleCanvas.getContext("2d", {
  willReadFrequently: true
});

async function notifyBridgeStopped(options) {
  if (!options?.token) {
    return;
  }

  try {
    await fetch("http://127.0.0.1:8765/stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: options.token })
    });
  } catch (_error) {
    // The local bridge may already be shutting down.
  }
}

async function stopObserving(notify = true) {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }

  const previousStream = stream;
  const previousOptions = activeOptions;
  const pendingCapture = captureInFlight;
  stream = null;
  activeOptions = null;
  lastSentFrame = null;

  if (previousStream) {
    for (const track of previousStream.getTracks()) {
      track.onended = null;
      track.stop();
    }
  }

  video.pause();
  video.srcObject = null;

  if (pendingCapture) {
    try {
      await pendingCapture;
    } catch (_error) {
      // Stop notification still needs to run after any pending frame request.
    }
  }

  if (notify) {
    await notifyBridgeStopped(previousOptions);
  }
}

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

  // Ignore small cursor/caret flicker and compression noise while keeping
  // text, window, and scene changes that affect a visible part of the screen.
  return changedFraction >= 0.006 && meanDifference >= 0.8;
}

async function captureFrameAndSend() {
  const scale = Math.min(
    1,
    1280 / Math.max(video.videoWidth, video.videoHeight)
  );
  frameCanvas.width = Math.max(1, Math.round(video.videoWidth * scale));
  frameCanvas.height = Math.max(1, Math.round(video.videoHeight * scale));
  frameCanvas.getContext("2d").drawImage(
    video,
    0,
    0,
    frameCanvas.width,
    frameCanvas.height
  );

  const currentFrame = sampleFrame(frameCanvas);

  if (!hasMeaningfulPixelChange(lastSentFrame, currentFrame)) {
    return;
  }

  const imageBase64 = frameCanvas
    .toDataURL("image/jpeg", 0.68)
    .split(",")[1];
  const response = await fetch("http://127.0.0.1:8765/context", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      token: activeOptions.token,
      title: "사용자가 이어서 공유한 화면 또는 창",
      url: activeOptions.url,
      text: "",
      selection: "",
      image_base64: imageBase64,
      image_mime: "image/jpeg",
      continuous: true
    })
  });

  if (!response.ok) {
    throw new Error(`LUCID 연결 오류 (${response.status})`);
  }

  lastSentFrame = currentFrame;
}

async function captureAndSend() {
  if (!stream || !activeOptions || captureInFlight) {
    return;
  }

  const currentCapture = captureFrameAndSend();
  captureInFlight = currentCapture;

  try {
    await currentCapture;
  } finally {
    if (captureInFlight === currentCapture) {
      captureInFlight = null;
    }
  }
}

async function startObserving(options) {
  await stopObserving(false);
  activeOptions = options;

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        mandatory: {
          chromeMediaSource: "desktop",
          chromeMediaSourceId: options.streamId,
          maxWidth: 1920,
          maxHeight: 1080
        }
      }
    });

    video.srcObject = stream;
    await video.play();

    const [track] = stream.getVideoTracks();
    track.onended = () => {
      void stopObserving(true);
    };

    await captureAndSend();
    timer = setInterval(() => {
      captureAndSend().catch(async (error) => {
        console.error("LUCID screen sharing stopped:", error);
        await stopObserving(true);
      });
    }, 3000);
  } catch (error) {
    await stopObserving(false);
    throw error;
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.target && message.target !== "offscreen") {
    return;
  }

  if (message.type === "lucid-start-observing") {
    startObserving(message.options)
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  if (message.type === "lucid-stop-observing") {
    stopObserving(true).then(() => sendResponse({ ok: true }));
    return true;
  }
});
