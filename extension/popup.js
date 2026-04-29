const output = document.querySelector("#output");
const statusBox = document.querySelector("#status");
const collectBtn = document.querySelector("#collectBtn");
const copyBtn = document.querySelector("#copyBtn");
const downloadBtn = document.querySelector("#downloadBtn");

let latestPayload = "";

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function setStatus(text) {
  statusBox.textContent = text;
}

async function collectCurrentTab() {
  const tab = await getActiveTab();
  if (!tab?.id) {
    setStatus("未找到当前标签页");
    return;
  }

  const response = await chrome.tabs.sendMessage(tab.id, { type: "COLLECT_POST" }).catch(() => null);
  if (!response?.ok) {
    setStatus(response?.error || "当前页面不是可采集的帖子详情页");
    return;
  }

  latestPayload = JSON.stringify(response.payload, null, 2);
  output.value = latestPayload;
  setStatus("采集完成，可以复制或下载 JSON");
}

async function copyPayload() {
  if (!latestPayload) {
    setStatus("请先采集页面");
    return;
  }

  await navigator.clipboard.writeText(latestPayload);
  setStatus("JSON 已复制到剪贴板");
}

function downloadPayload() {
  if (!latestPayload) {
    setStatus("请先采集页面");
    return;
  }

  const blob = new Blob([latestPayload], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `offerscope-collected-post-${Date.now()}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
  setStatus("JSON 已下载");
}

collectBtn.addEventListener("click", () => {
  collectCurrentTab().catch((error) => {
    console.error(error);
    setStatus("采集失败，请检查当前页面");
  });
});

copyBtn.addEventListener("click", () => {
  copyPayload().catch((error) => {
    console.error(error);
    setStatus("复制失败");
  });
});

downloadBtn.addEventListener("click", downloadPayload);
