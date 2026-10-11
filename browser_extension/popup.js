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

document.getElementById("share").addEventListener("click", async () => {
  const token = tokenInput.value.trim();

  if (!token) {
    status.textContent = "LUCID 콘솔에 표시된 연결 토큰을 입력해 줘.";
    return;
  }

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const [{ result: snapshot }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: getPageSnapshot
    });

    const response = await fetch("http://127.0.0.1:8765/context", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, ...snapshot })
    });

    if (!response.ok) {
      throw new Error((await response.json()).error || "전송 실패");
    }

    await chrome.storage.local.set({ lucidToken: token });
    status.textContent = "현재 페이지를 LUCID에 전달했어.";
  } catch (error) {
    status.textContent = `전송하지 못했어: ${error.message}`;
  }
});
