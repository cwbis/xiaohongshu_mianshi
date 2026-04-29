export function resolveChatCompletionsUrl(baseUrl) {
  const trimmed = String(baseUrl || "").trim().replace(/\/$/, "");
  return trimmed.endsWith("/chat/completions") ? trimmed : `${trimmed}/chat/completions`;
}

export async function requestJsonCompletion(config, payload) {
  const response = await fetch(resolveChatCompletionsUrl(config.baseUrl), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${config.apiKey}`,
    },
    body: JSON.stringify({
      model: config.model,
      messages: payload.messages,
      temperature: payload.temperature ?? 0.3,
      response_format: { type: "json_object" },
    }),
  });

  const responsePayload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(responsePayload?.error?.message || `大模型请求失败：${response.status}`);
  }

  const text = responsePayload?.choices?.[0]?.message?.content || "";
  return extractJsonFromText(text);
}

export function extractJsonFromText(text) {
  const raw = String(text || "").trim();
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    const start = raw.indexOf("{");
    const end = raw.lastIndexOf("}");
    if (start >= 0 && end > start) {
      return JSON.parse(raw.slice(start, end + 1));
    }
    throw new Error("大模型返回内容不是有效 JSON。");
  }
}
