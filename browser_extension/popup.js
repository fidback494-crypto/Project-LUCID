const tokenInput = document.getElementById("token");
const status = document.getElementById("status");

chrome.storage.local.get(["lucidToken"], ({ lucidToken }) => {
  tokenInput.value = lucidToken || "";
});

function getPageSnapshot() {
  const selection = window.getSelection ? window.getSelection().toString() : "";

  return {
    title: document.title,
    url: location.href,
    selection: selection.slice(0, 4000),
    text: (document.body?.innerText || "").slice(0, 16000)
  };
}

async function sendToLucid(token, snapshot) {
  const response = await fetch("http://127.0.0.1:8765/context", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, ...snapshot })
  });

  if (!response.ok) {
    throw new Error((await response.json()).error || "전송 실패");
  }

  await chrome.storage.local.set({ lucidToken: token });
}

function getToken() {
  const token = tokenInput.value.trim();

  if (!token) {
    throw new Error("LUCID 콘솔에 표시된 연결 토큰을 입력해 줘.");
  }

  return token;
}

async function imageFromDesktopStream(stream) {
  try {
    const video = document.createElement("video");
    video.srcObject = stream;
    await video.play();
    const scale = Math.min(1, 1600 / Math.max(video.videoWidth, video.videoHeight));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
    canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.82).split(",")[1];
  } finally {
    stream.getTracks().forEach((track) => track.stop());
  }
}

async function chooseDesktop() {
  const streamId = await new Promise((resolve) => {
    chrome.desktopCapture.chooseDesktopMedia(["screen", "window"], resolve);
  });

  if (!streamId) {
    throw new Error("화면 또는 창 선택이 취소됐어.");
  }

  return streamId;
}

async function captureDesktopOnce() {
  const streamId = await chooseDesktop();
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: false,
    video: {
      mandatory: {
        chromeMediaSource: "desktop",
        chromeMediaSourceId: streamId,
        maxWidth: 1920,
        maxHeight: 1080
      }
    }
  });

  return imageFromDesktopStream(stream);
}

async function ensureOffscreenDocument() {
  const offscreenUrl = chrome.runtime.getURL("offscreen.html");
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ["OFFSCREEN_DOCUMENT"],
    documentUrls: [offscreenUrl]
  });

  if (contexts.length > 0) {
    return;
  }

  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: ["DISPLAY_MEDIA"],
    justification: "사용자가 선택한 화면 또는 창을 LUCID에 이어서 관찰하게 합니다."
  });
}

document.getElementById("share").addEventListener("click", async () => {
  try {
    const token = getToken();
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const [{ result: snapshot }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: getPageSnapshot
    });
    await sendToLucid(token, snapshot);
    status.textContent = "현재 페이지를 LUCID에 전달했어.";
  } catch (error) {
    status.textContent = `전송하지 못했어: ${error.message}`;
  }
});

document.getElementById("share-screen").addEventListener("click", async () => {
  try {
    const token = getToken();
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    status.textContent = "공유할 화면 또는 창을 선택해 줘.";
    const imageBase64 = await captureDesktopOnce();
    await sendToLucid(token, {
      title: "사용자가 공유한 화면 또는 창",
      url: tab.url || "",
      selection: "",
      text: "",
      image_base64: imageBase64,
      image_mime: "image/jpeg",
      continuous: false
    });
    status.textContent = "화면 이미지를 LUCID에 전달했어.";
  } catch (error) {
    status.textContent = `전송하지 못했어: ${error.message}`;
  }
});

document.getElementById("start-observing").addEventListener("click", async () => {
  try {
    const token = getToken();
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    await ensureOffscreenDocument();
    status.textContent = "관찰할 화면 또는 창을 선택해 줘.";
    const streamId = await chooseDesktop();
    const response = await chrome.runtime.sendMessage({
      type: "lucid-start-observing",
      target: "offscreen",
      options: { streamId, token, url: tab.url || "" }
    });

    if (!response?.ok) {
      throw new Error(response?.error || "관찰을 시작하지 못했어.");
    }

    await chrome.storage.local.set({ lucidToken: token });
    status.textContent = "루시드가 화면 변화를 곁에서 관찰 중이야.";
  } catch (error) {
    status.textContent = `관찰을 시작하지 못했어: ${error.message}`;
  }
});

document.getElementById("stop-observing").addEventListener("click", async () => {
  try {
    await chrome.runtime.sendMessage({
      type: "lucid-stop-observing",
      target: "offscreen"
    });
    status.textContent = "이어지는 화면 관찰을 멈췄어.";
  } catch (error) {
    status.textContent = `관찰을 중지하지 못했어: ${error.message}`;
  }
});
