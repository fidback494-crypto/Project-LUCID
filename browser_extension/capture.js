/** 요청 본문에 페어링 토큰을 붙여 로컬 브리지에 전송한다. 실패하면 오류를 던진다. */
export async function postToBridge({ token, port }, path, data, timeout = 10000) {
  const portNumber = Number(port);
  if (!Number.isInteger(portNumber) || portNumber < 1 || portNumber > 65535) {
    throw new Error("1부터 65535 사이의 포트를 입력해 줘.");
  }
  const response = await fetch(`http://127.0.0.1:${portNumber}/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, ...data }),
    signal: AbortSignal.timeout(timeout)
  });
  const result = await response.json();
  if (!response.ok) {
    const message = response.status === 403 ? "페어링 토큰을 확인해 줘." : result.error;
    throw new Error(message || `LUCID 연결 오류 (${response.status})`);
  }
  return result;
}

/** 사용자가 선택한 화면 ID를 오디오 없는 영상 스트림으로 연다. */
export function openDesktopStream(streamId) {
  return navigator.mediaDevices.getUserMedia({
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
}

/** 영상의 현재 장면을 비율을 유지하며 최대 maxSize 픽셀로 축소해 캔버스에 그린다. */
export function drawFrame(video, canvas, maxSize) {
  const scale = Math.min(1, maxSize / Math.max(video.videoWidth, video.videoHeight));
  canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
  canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
  canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
}
