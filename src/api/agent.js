import { requestJson } from "./http";

export function classifyQuestion(payload) {
  return requestJson("/api/agent/classify", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function retrieveContext(payload) {
  return requestJson("/api/agent/retrieve", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function generateAgentAnswer(payload) {
  return requestJson("/api/agent/answer", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function generateFollowUp(payload) {
  return requestJson("/api/agent/follow-up", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function startTrainingSession(payload) {
  return requestJson("/api/agent/training/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function submitTrainingAnswer(payload) {
  return requestJson("/api/agent/training/answer", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function advanceTrainingSession(payload) {
  return requestJson("/api/agent/training/advance", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listAgentSessions(limit = 20, mode = "") {
  const query = new URLSearchParams({ limit: String(limit) });
  if (mode) {
    query.set("mode", mode);
  }
  return requestJson(`/api/agent/sessions?${query.toString()}`, { method: "GET" });
}

export function getAgentSession(sessionId) {
  return requestJson(`/api/agent/sessions/${sessionId}`, { method: "GET" });
}
