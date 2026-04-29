const XHS_HOSTS = ["www.xiaohongshu.com", "edith.xiaohongshu.com"];
const XHS_SHARE_HOSTS = ["xhslink.com"];

function normalizeUrl(raw) {
  try {
    const url = new URL(raw);
    url.hash = "";
    return url.toString();
  } catch {
    return "";
  }
}

function isXiaohongshuUrl(raw) {
  try {
    const { hostname } = new URL(raw);
    return XHS_HOSTS.includes(hostname) || XHS_SHARE_HOSTS.includes(hostname);
  } catch {
    return false;
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function collectFromTab(tabId, { requireContent = false, timeoutMs = 20000 } = {}) {
  const started = Date.now();
  let lastError = "未能从目标标签页提取帖子内容";

  while (Date.now() - started <= timeoutMs) {
    const response = await chrome.tabs.sendMessage(tabId, { type: "COLLECT_POST" }).catch(() => null);
    if (response?.ok) {
      if (!requireContent || response.payload?.content) {
        return response.payload;
      }
      lastError = "页面已打开，但正文还没有完成渲染";
    } else if (response?.error) {
      lastError = response.error;
    }

    await sleep(800);
  }

  throw new Error(lastError);
}

async function findBestOpenTab(targetUrl) {
  const tabs = await chrome.tabs.query({});
  const xhsTabs = tabs.filter((tab) => isXiaohongshuUrl(tab.url || ""));

  if (targetUrl) {
    const normalizedTarget = normalizeUrl(targetUrl);
    const exact = xhsTabs.find((tab) => normalizeUrl(tab.url || "") === normalizedTarget);
    if (exact) {
      return exact;
    }
  }

  const activeXhsTab = xhsTabs.find((tab) => tab.active);
  if (activeXhsTab) {
    return activeXhsTab;
  }

  return xhsTabs[0] || null;
}

async function waitForTabComplete(tabId, timeoutMs = 15000) {
  const started = Date.now();

  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      const tab = await chrome.tabs.get(tabId).catch(() => null);
      if (!tab) {
        clearInterval(timer);
        reject(new Error("目标标签页已关闭"));
        return;
      }

      if (tab.status === "complete") {
        clearInterval(timer);
        setTimeout(resolve, 1200);
        return;
      }

      if (Date.now() - started > timeoutMs) {
        clearInterval(timer);
        reject(new Error("等待页面加载超时"));
      }
    }, 500);
  });
}

async function collectByUrl(targetUrl) {
  const existing = await findBestOpenTab(targetUrl);
  if (existing && normalizeUrl(existing.url || "") === normalizeUrl(targetUrl)) {
    return collectFromTab(existing.id, { requireContent: true });
  }

  const created = await chrome.tabs.create({ url: targetUrl, active: false });
  await waitForTabComplete(created.id);
  return collectFromTab(created.id, { requireContent: true });
}

async function collectCurrent() {
  const tab = await findBestOpenTab("");
  if (!tab?.id) {
    throw new Error("没有找到已打开的小红书帖子页，请先打开目标帖子。");
  }
  return collectFromTab(tab.id);
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "OFFERSCOPE_AUTOFILL_REQUEST") {
    return;
  }

  (async () => {
    const mode = message.payload?.mode;
    const sourceUrl = message.payload?.sourceUrl || "";

    if (mode === "link") {
      if (!sourceUrl || !isXiaohongshuUrl(sourceUrl)) {
        throw new Error("请输入有效的小红书帖子链接。");
      }
      return collectByUrl(sourceUrl);
    }

    return collectCurrent();
  })()
    .then((payload) => sendResponse({ ok: true, payload }))
    .catch((error) => sendResponse({ ok: false, error: error.message || "自动填充失败" }));

  return true;
});
