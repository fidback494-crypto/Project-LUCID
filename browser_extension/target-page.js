/**
 * 현재 문서에서 보이는 클릭 후보를 수집하거나 이전 후보 하나를 검증·클릭한다.
 * Chrome이 함수를 복사해 실행하므로 필요한 코드는 함수 안에 둔다.
 */
export function targetOnPage(action, snapshotId, targetId) {
  const key = "__lucidVisualClickSnapshot";
  const selector = [
    "button", "a[href]", "input:not([type=hidden]):not([type=password]):not([type=file])",
    "select", "textarea", "summary", "[role=button]", "[role=link]", "[role=tab]",
    "[role=menuitem]", "[role=checkbox]", "[role=radio]", "[role=switch]"
  ].join(",");

  function describe(element) {
    if (!element.isConnected || !element.matches(selector) || typeof element.click !== "function") return null;
    if (element.matches(":disabled") || element.closest('[inert], [aria-disabled="true"]')) return null;
    const style = getComputedStyle(element);
    if (style.visibility !== "visible" || element.getClientRects().length === 0) return null;
    for (let node = element; node; node = node.parentElement) {
      if (Number(getComputedStyle(node).opacity) === 0) return null;
    }
    const rect = element.getBoundingClientRect();
    const left = Math.max(0, rect.left), right = Math.min(innerWidth, rect.right);
    const top = Math.max(0, rect.top), bottom = Math.min(innerHeight, rect.bottom);
    if (right - left < 5 || bottom - top < 5) return null;
    const hit = document.elementFromPoint((left + right) / 2, (top + bottom) / 2);
    if (!hit || !element.contains(hit) || hit.closest(selector) !== element) return null;

    const role = element.getAttribute("role") || element.localName;
    const labelIds = (element.getAttribute("aria-labelledby") || "").split(/\s+/);
    const labelledBy = labelIds.map(id => document.getElementById(id)?.innerText || "").join(" ").trim();
    const buttonValue = element.matches('input[type=button],input[type=submit],input[type=reset]')
      ? element.value : "";
    const labelText = labelledBy || element.getAttribute("aria-label")
      || element.labels?.[0]?.innerText || element.innerText || element.title
      || element.querySelector("img[alt]")?.alt || buttonValue || "";
    const label = (role + " " + labelText).replace(/\s+/g, " ").trim().slice(0, 180);
    const identity = JSON.stringify([
      role, element.localName, element.getAttribute("type"), element.getAttribute("href"),
      element.formAction || "", element.form?.action || "", labelText
    ]);
    return { label, identity, left, top, width: right - left, height: bottom - top };
  }

  if (action === "collect") {
    const items = [];
    for (const element of document.querySelectorAll(selector)) {
      const info = describe(element);
      if (!info) continue;
      items.push({ element, info });
      if (items.length === 60) break;
    }
    globalThis[key] = { id: snapshotId, items, width: innerWidth, height: innerHeight, url: location.href };
    return {
      width: innerWidth, height: innerHeight,
      candidates: items.map(({ info: { label, left, top, width, height } }, i) =>
        ({ id: i + 1, label, left, top, width, height }))
    };
  }

  const saved = globalThis[key];
  if (!saved || saved.id !== snapshotId) return false;
  if (action === "snapshot-current") {
    return document.visibilityState === "visible" && saved.url === location.href &&
      saved.width === innerWidth && saved.height === innerHeight;
  }
  const item = saved.items[targetId - 1];
  if (action === "click") delete globalThis[key];
  if (!item || document.visibilityState !== "visible" || saved.url !== location.href || saved.width !== innerWidth || saved.height !== innerHeight) {
    return false;
  }
  const current = describe(item.element);
  if (!current || current.identity !== item.info.identity) return false;
  if (["left", "top", "width", "height"].some(key => Math.abs(current[key] - item.info[key]) > 1)) {
    return false;
  }
  if (action === "click") item.element.click();
  return true;
}
