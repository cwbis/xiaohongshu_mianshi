import { postJson } from "./http";

export function searchPosts(payload) {
  return postJson("/api/xhs/search", payload);
}

export function getNoteDetail(payload) {
  return postJson("/api/xhs/note-detail", payload);
}
