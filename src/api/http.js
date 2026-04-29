export async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok || data?.ok === false) {
    throw new Error(data?.error || `请求失败：${response.status}`);
  }
  return data;
}

export function postJson(path, payload = {}) {
  return requestJson(path, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
