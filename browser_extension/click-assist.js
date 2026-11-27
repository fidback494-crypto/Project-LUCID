import { postToBridge } from "./capture.js";
import { targetOnPage } from "./target-page.js";

/** 현재 팝업이 열린 브라우저 창의 활성 탭을 반환한다. */
async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error("클릭할 탭을 찾지 못했어.");
  return tab;
}

/** 선택한 문서에 함수를 주입한다. Chrome이 반환한 문서 ID로 탐색 후 재사용을 막는다. */
async function inDocument(tabId, documentId, ...args) {
  const target = documentId ? { tabId, documentIds: [documentId] } : { tabId, frameIds: [0] };
  const [result] = await chrome.scripting.executeScript({ target, func: targetOnPage, args });
  if (!result?.documentId) throw new Error("페이지가 바뀌었어. 대상을 다시 찾아 줘.");
  return result;
}

/** 스크린샷을 한 장의 JPEG로 줄이고 후보에 번호를 표시한다. */
async function annotatedImage(dataUrl, snapshot) {
  const original = new Image();
  original.src = dataUrl;
  await original.decode();
  const scale = Math.min(1, 1600 / Math.max(original.width, original.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(original.width * scale));
  canvas.height = Math.max(1, Math.round(original.height * scale));
  const ctx = canvas.getContext("2d");
  ctx.drawImage(original, 0, 0, canvas.width, canvas.height);
  const sx = canvas.width / snapshot.width, sy = canvas.height / snapshot.height;
  ctx.font = "bold 15px sans-serif";
  ctx.textBaseline = "top";
  for (const c of snapshot.candidates) {
    const x = c.left * sx, y = c.top * sy;
    ctx.strokeStyle = "#006deb";
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, c.width * sx, c.height * sy);
    const text = String(c.id);
    const badgeWidth = Math.ceil(ctx.measureText(text).width) + 6;
    const badgeX = Math.min(x, canvas.width - badgeWidth);
    const badgeY = y >= 19 ? y - 18 : y;
    ctx.fillStyle = "#073c88";
    ctx.fillRect(badgeX, badgeY, badgeWidth, 18);
    ctx.fillStyle = "white";
    ctx.fillText(text, badgeX + 3, badgeY + 1);
  }
  return { original, jpeg: canvas.toDataURL("image/jpeg", 0.78).split(",")[1] };
}

/** 확인용 미리보기에는 선택한 요소와 주변 장면을 담고 요소 경계에 테두리를 표시한다. */
function drawPreview(canvas, original, snapshot, c) {
  const sx = original.width / snapshot.width, sy = original.height / snapshot.height;
  const left = Math.max(0, (c.left - 40) * sx), top = Math.max(0, (c.top - 24) * sy);
  const right = Math.min(original.width, (c.left + c.width + 40) * sx);
  const bottom = Math.min(original.height, (c.top + c.height + 24) * sy);
  const scale = Math.min(1, 520 / (right - left), 240 / (bottom - top));
  canvas.width = Math.max(1, Math.ceil((right - left) * scale));
  canvas.height = Math.max(1, Math.ceil((bottom - top) * scale));
  const ctx = canvas.getContext("2d");
  ctx.drawImage(original, left, top, right - left, bottom - top, 0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#006deb";
  ctx.lineWidth = 3;
  ctx.strokeRect((c.left * sx - left) * scale, (c.top * sy - top) * scale,
    c.width * sx * scale, c.height * sy * scale);
}

/** 요청 한 건을 화면에서 찾아 미리 보여 주고 사용자의 확인을 받은 뒤 한 번만 클릭한다. */
export function mountClickAssist(getConnection, rememberConnection) {
  const instruction = document.getElementById("target-request");
  const find = document.getElementById("find-target");
  const confirm = document.getElementById("click-target");
  const cancel = document.getElementById("cancel-target");
  const panel = document.getElementById("target-preview");
  const status = document.getElementById("target-status");
  let selected = null, revision = 0, lastCaptureAt = -Infinity;

  function reset() {
    revision += 1;
    selected = null;
    panel.hidden = true;
    find.disabled = false;
    status.textContent = "";
  }
  instruction.addEventListener("input", reset);
  cancel.addEventListener("click", reset);
  chrome.tabs.onActivated.addListener(reset);
  find.addEventListener("click", async () => {
    reset();
    const version = revision;
    find.disabled = true;
    try {
      const connection = getConnection();
      const request = instruction.value.trim();
      if (!request) throw new Error("클릭할 대상을 입력해 줘.");
      const tab = await activeTab();
      const snapshotId = crypto.randomUUID();
      const { documentId, result: snapshot } = await inDocument(tab.id, null, "collect", snapshotId, 0);
      if (!snapshot.candidates.length) throw new Error("현재 화면에서 클릭할 요소를 찾지 못했어.");
      if ((await activeTab()).id !== tab.id || version !== revision) return;
      const wait = lastCaptureAt + 600 - performance.now();
      if (wait > 0) await new Promise(resolve => setTimeout(resolve, wait));
      if (version !== revision || (await activeTab()).id !== tab.id) return;
      lastCaptureAt = performance.now();
      const capture = await chrome.tabs.captureVisibleTab(tab.windowId, { format: "jpeg", quality: 85 });
      if ((await activeTab()).id !== tab.id || version !== revision) return;
      const current = await inDocument(tab.id, null, "snapshot-current", snapshotId, 0);
      if (current.documentId !== documentId || !current.result) {
        throw new Error("캡처하는 동안 페이지가 바뀌었어. 대상을 다시 찾아 줘.");
      }
      const { original, jpeg } = await annotatedImage(capture, snapshot);
      if (version !== revision) return;
      status.textContent = "비전 모델이 화면에서 대상을 찾고 있어.";
      const { target } = await postToBridge(connection, "click-target", {
        instruction: request, image_base64: jpeg, candidates: snapshot.candidates.map(c => c.label)
      }, 310000);
      if (version !== revision) return;
      if (target === 0) throw new Error("정확히 일치하는 대상을 찾지 못했어.");
      const c = snapshot.candidates.find(c => c.id === target);
      if (!c || (await activeTab()).id !== tab.id ||
        !(await inDocument(tab.id, documentId, "check", snapshotId, target)).result) {
        throw new Error("화면이 바뀌었어. 대상을 다시 찾아 줘.");
      }
      await rememberConnection(connection);
      if (version !== revision) return;
      selected = { tabId: tab.id, documentId, snapshotId, target };
      drawPreview(document.getElementById("target-image"), original, snapshot, c);
      document.getElementById("target-label").textContent = c.label;
      panel.hidden = false;
      status.textContent = "표시한 요소가 맞으면 한 번 클릭해.";
    } catch (error) {
      if (version === revision) status.textContent = error.message;
    } finally {
      if (version === revision) find.disabled = false;
    }
  });

  confirm.addEventListener("click", async () => {
    const choice = selected;
    if (!choice) return;
    reset();
    const version = revision;
    try {
      if ((await activeTab()).id !== choice.tabId ||
        !(await inDocument(choice.tabId, choice.documentId, "click", choice.snapshotId, choice.target)).result) {
        throw new Error("대상이 바뀌었어. 대상을 다시 찾아 줘.");
      }
      if (version === revision) status.textContent = "선택한 요소를 한 번 클릭했어.";
    } catch (error) {
      if (version === revision) status.textContent = error.message;
    }
  });
}
