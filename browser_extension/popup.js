import { mountClickAssist } from "./click-assist.js";
import { drawFrame, openDesktopStream, postToBridge } from "./capture.js";

const tokenInput = document.getElementById("token");
const portInput = document.getElementById("port");
const status = document.getElementById("status");

chrome.storage.local.get(["lucidToken", "lucidPort"], ({ lucidToken, lucidPort }) => {
  portInput.value = lucidPort || 8765;
  tokenInput.value = lucidToken || "";
});

/** 활성 탭에서 제목·주소·선택 영역·본문 일부를 읽어 공유용 객체를 반환한다. */
function getPageSnapshot() {
  const selection = window.getSelection ? window.getSelection().toString() : "";

  return {
    title: document.title,
    url: location.href,
    selection: selection.slice(0, 4000),
    text: (document.body?.innerText || "").slice(0, 16000)
  };
}

/** 공유에 성공한 연결 설정을 다음번 팝업에서도 사용한다. */
function rememberConnection({ token, port }) {
  return chrome.storage.local.set({ lucidToken: token, lucidPort: port });
}

/** 사용자가 입력한 로컬 포트와 토큰을 확인해 반환한다. */
function getConnection() {
  const token = tokenInput.value.trim();
  const port = portInput.valueAsNumber;
  if (!token) throw new Error("LUCID 콘솔에 표시된 연결 토큰을 입력해 줘.");
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error("1부터 65535 사이의 포트를 입력해 줘.");
  }
  return { token, port };
}

/** 영상 스트림에서 한 장면을 JPEG Base64로 반환하고 캡처를 종료한다. */
async function imageFromDesktopStream(stream) {
  try {
    const video = document.createElement("video");
    video.srcObject = stream;
    await video.play();
    const canvas = document.createElement("canvas");
    drawFrame(video, canvas, 1600);
    return canvas.toDataURL("image/jpeg", 0.82).split(",")[1];
  } finally {
    stream.getTracks().forEach((track) => track.stop());
  }
}

/** 화면 선택 대화상자를 열고 선택한 스트림의 ID를 반환한다. */
async function chooseDesktop() {
  const streamId = await new Promise((resolve) => {
    chrome.desktopCapture.chooseDesktopMedia(["screen", "window"], resolve);
  });

  if (!streamId) {
    throw new Error("화면 또는 창 선택이 취소됐어.");
  }

  return streamId;
}

/** 운영체제 선택창에서 고른 화면의 첫 장면을 JPEG Base64로 반환한다. */
async function captureDesktopOnce() {
  const streamId = await chooseDesktop();
  const stream = await openDesktopStream(streamId);
  return imageFromDesktopStream(stream);
}

/** 팝업이 닫힌 뒤에도 공유를 계속할 백그라운드 문서를 준비한다. */
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
    const connection = getConnection();
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const [{ result: snapshot }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: getPageSnapshot
    });
    await postToBridge(connection, "context", snapshot);
    await rememberConnection(connection);
    status.textContent = "현재 페이지를 LUCID에 전달했어.";
  } catch (error) {
    status.textContent = `전송하지 못했어: ${error.message}`;
  }
});

document.getElementById("share-screen").addEventListener("click", async () => {
  try {
    const connection = getConnection();
    status.textContent = "공유할 화면 또는 창을 선택해 줘.";
    const imageBase64 = await captureDesktopOnce();
    await postToBridge(connection, "context", {
      title: "사용자가 공유한 화면 또는 창",
      url: "",
      selection: "",
      text: "",
      image_base64: imageBase64,
      image_mime: "image/jpeg",
      continuous: false
    });
    await rememberConnection(connection);
    status.textContent = "화면 이미지를 LUCID에 전달했어.";
  } catch (error) {
    status.textContent = `전송하지 못했어: ${error.message}`;
  }
});

document.getElementById("start-observing").addEventListener("click", async () => {
  try {
    const connection = getConnection();
    await ensureOffscreenDocument();
    status.textContent = "관찰할 화면 또는 창을 선택해 줘.";
    const streamId = await chooseDesktop();
    const response = await chrome.runtime.sendMessage({
      type: "lucid-start-observing",
      target: "offscreen",
      options: { streamId, ...connection }
    });

    if (!response?.ok) {
      throw new Error(response?.error || "관찰을 시작하지 못했어.");
    }

    await rememberConnection(connection);
    status.textContent = "루시드가 화면 변화를 곁에서 관찰 중이야.";
  } catch (error) {
    status.textContent = `관찰을 시작하지 못했어: ${error.message}`;
  }
});

document.getElementById("stop-observing").addEventListener("click", async () => {
  try {
    const response = await chrome.runtime.sendMessage({
      type: "lucid-stop-observing",
      target: "offscreen"
    });
    if (!response?.ok) throw new Error(response?.error || "종료를 확인하지 못했어.");
    status.textContent = "이어지는 화면 관찰을 멈췄어.";
  } catch (error) {
    status.textContent = `관찰을 중지하지 못했어: ${error.message}`;
  }
});

mountClickAssist(getConnection, rememberConnection);
