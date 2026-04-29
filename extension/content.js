function readMetaContent(selectors) {
  for (const selector of selectors) {
    const node = document.querySelector(selector);
    const content = node?.getAttribute?.("content")?.trim();
    if (content) {
      return content;
    }
  }
  return "";
}

function readText(selectors) {
  for (const selector of selectors) {
    const node = document.querySelector(selector);
    const text = node?.textContent?.trim();
    if (text) {
      return text;
    }
  }
  return "";
}

function readAllText(selectors) {
  for (const selector of selectors) {
    const nodes = [...document.querySelectorAll(selector)];
    const text = nodes
      .map((node) => node.textContent?.trim() || "")
      .filter(Boolean)
      .join("\n");

    if (text) {
      return text;
    }
  }
  return "";
}

function readDescriptionFallback() {
  return readMetaContent([
    "meta[name='description']",
    "meta[property='og:description']"
  ]);
}

function cleanupDocumentTitle(rawTitle) {
  return String(rawTitle || "")
    .replace(/\s*-\s*小红书.*$/i, "")
    .replace(/\s*-\s*Red.*$/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeInlineText(text) {
  return String(text || "")
    .replace(/\s+/g, " ")
    .trim();
}

function isSuspiciousTitle(title, content) {
  const normalizedTitle = normalizeInlineText(title);
  const normalizedContent = normalizeInlineText(content);

  if (!normalizedTitle) {
    return true;
  }

  if (normalizedTitle.length > 80) {
    return true;
  }

  if (normalizedContent && normalizedTitle === normalizedContent) {
    return true;
  }

  if (normalizedContent && normalizedContent.startsWith(normalizedTitle) && normalizedTitle.length > 40) {
    return true;
  }

  return false;
}

function getTitle(content) {
  const visibleTitle = readText([
    ".note-content .title",
    ".note-scroller .title",
    "[data-v-6d0ad7a0] .title",
    "h1.title",
    "h1"
  ]);

  if (!isSuspiciousTitle(visibleTitle, content)) {
    return visibleTitle;
  }

  const ogTitle = readMetaContent(["meta[property='og:title']"]);
  if (!isSuspiciousTitle(ogTitle, content)) {
    return ogTitle;
  }

  const documentTitle = cleanupDocumentTitle(document.title);
  if (!isSuspiciousTitle(documentTitle, content)) {
    return documentTitle;
  }

  return visibleTitle || ogTitle || documentTitle;
}

function collectPostPayload() {
  const visibleContent = readAllText([
    ".note-content .desc",
    ".note-content .content",
    ".note-scroller .desc",
    "#detail-desc .note-text",
    ".note-text"
  ]);
  const content = visibleContent || readDescriptionFallback();

  const title = getTitle(content);

  const author = readText([
    ".author-container .name",
    ".author-wrapper .name",
    ".username",
    ".author-info .name"
  ]);

  const publishTime = readText([
    ".date",
    ".publish-time",
    ".note-content .time"
  ]);

  const tags = [...document.querySelectorAll(".tag, .note-tag, .hash-tag")]
    .map((node) => node.textContent?.trim() || "")
    .filter(Boolean);

  if (!title && !content) {
    return null;
  }

  return {
    title: title || "未命名帖子",
    content,
    author,
    publishTime,
    sourceUrl: window.location.href,
    tags,
    collectedAt: new Date().toISOString()
  };
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "COLLECT_POST") {
    return;
  }

  const payload = collectPostPayload();
  if (!payload) {
    sendResponse({ ok: false, error: "没有识别到帖子标题或正文，请确认当前页面是帖子详情页。" });
    return;
  }

  sendResponse({ ok: true, payload });
});
