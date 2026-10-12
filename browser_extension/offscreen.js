let stream = null;
let timer = null;
let lastFingerprint = null;

function stopObserving() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }

  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }

  lastFingerprint = null;
}

function fingerprint(canvas) {
  const tiny = document.createElement("canvas");
  tiny.width = 32;
  tiny.height = 18;
  const context = tiny.getContext("2d", { willReadFrequently: true });
  context.drawImage(canvas, 0, 0, tiny.width, tiny.height);
  const pixels = context.getImageData(0, 0, tiny.width, tiny.height).data;
  let hash = 2166136261;

  for (let index = 0; index < pixels.length; index += 12) {
    hash ^= pixels[index] + pixels[index + 1] + pixels[index + 2];
    hash = Math.imul(hash, 16777619);
  }

  return hash >>> 0;
}

async function captureAndSend(options) {
  const video = document.createElement("video");
  video.srcObject = stream;
  video.muted = true;
  await video.play();

  const scale = Math.min(1, 1280 / Math.max(video.videoWidth, video.videoHeight));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
  canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
  canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);

  const nextFingerprint = fingerprint(canvas);

  if (nextFingerprint === lastFingerprint) {
    return;
  }

  lastFingerprint = nextFingerprint;
  const imageBase64 = canvas.toDataURL("image/jpeg", 0.68).split(",")[1];

  await fetch("http://127.0.0.1:8765/context", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      token: options.token,
      title: "사용자가 이어서 공유한 화면 또는 창",
      url: options.url,
      text: "",
      selection: "",
      image_base64: imageBase64,
      image_mime: "image/jpeg",
      continuous: true
    })
  });
}

async function startObserving(options) {
  stopObserving();

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

  await captureAndSend(options);
  timer = setInterval(() => {
    captureAndSend(options).catch(() => stopObserving());
  }, 3000);
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
    stopObserving();
    sendResponse({ ok: true });
  }
});
