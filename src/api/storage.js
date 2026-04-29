import { requestJson } from "./http";

function safeLoadJson(key, fallbackValue) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallbackValue;
  } catch (error) {
    console.error(`Failed to load legacy ${key}`, error);
    return fallbackValue;
  }
}

export function bootstrap() {
  return requestJson("/api/storage/bootstrap", { method: "GET" });
}

export async function persistPosts(posts) {
  const result = await requestJson("/api/storage/posts", {
    method: "PUT",
    body: JSON.stringify({ posts })
  });
  return {
    posts: Array.isArray(result.posts) ? result.posts : [],
    count: result.count ?? posts.length
  };
}

export async function persistLLMConfig(config) {
  const result = await requestJson("/api/storage/settings/llmConfig", {
    method: "PUT",
    body: JSON.stringify({ value: config })
  });
  return result.value || {};
}

export async function persistXhsConfig(config) {
  const result = await requestJson("/api/storage/settings/xhsConfig", {
    method: "PUT",
    body: JSON.stringify({ value: config })
  });
  return result.value || {};
}

export function importLegacyData(payload) {
  return requestJson("/api/storage/import-local", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function readLegacyData(storageKeys) {
  const posts = safeLoadJson(storageKeys.postsKey, []);
  return {
    posts: Array.isArray(posts) ? posts : [],
    llmConfig: safeLoadJson(storageKeys.llmConfigKey, {}),
    xhsConfig: safeLoadJson(storageKeys.xhsConfigKey, {})
  };
}

export function clearLegacyData(storageKeys = {}) {
  [storageKeys.postsKey, storageKeys.llmConfigKey, storageKeys.xhsConfigKey].forEach((key) => {
    if (!key) return;
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error(`Failed to clear legacy ${key}`, error);
    }
  });
}
