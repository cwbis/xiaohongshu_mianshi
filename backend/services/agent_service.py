from __future__ import annotations

import json
import re
from typing import Optional

from backend.errors import ApiError
from backend.repositories.db import StorageRepository
from backend.repositories.session_repo import SessionRepository
from backend.services.classifier_service import classify_question
from backend.services.llm_service import LlmService
from backend.services.retrieval_service import RetrievalService


DEFAULT_TOPIC_LIBRARY = [
    ("MySQL", ["mysql", "索引", "事务", "mvcc", "锁"]),
    ("Redis", ["redis", "缓存", "分布式锁", "一致性"]),
    ("Java", ["java", "集合", "并发", "thread"]),
    ("JVM", ["jvm", "gc", "内存", "类加载"]),
    ("Spring", ["spring", "ioc", "aop", "事务传播"]),
    ("消息队列", ["mq", "消息队列", "kafka", "rocketmq"]),
    ("计算机网络", ["tcp", "http", "https", "网络"]),
    ("操作系统", ["进程", "线程", "操作系统", "调度"]),
    ("场景设计", ["秒杀", "高并发", "限流", "设计"]),
]

QUESTION_TEMPLATES = {
    "MySQL": "MySQL 中最容易被追问的知识点是什么？请你按原理、场景和排查思路回答。",
    "Redis": "如果面试官围绕 Redis 缓存一致性继续深挖，你会怎么完整回答？",
    "Java": "Java 并发题里你最常见的失分点是什么？请举一个你会怎么答的例子。",
    "JVM": "请从内存结构、垃圾回收和线上排查三个角度聊聊 JVM。",
    "Spring": "如果面试官问你 Spring 事务为什么会失效，你会怎么讲？",
    "消息队列": "请你解释消息队列在项目里的价值，以及幂等、顺序和堆积怎么处理。",
    "计算机网络": "请从连接建立、可靠传输和排查思路三个角度回答一个经典网络题。",
    "操作系统": "请围绕进程、线程、锁和调度挑一个操作系统高频题来回答。",
    "场景设计": "如果给你一个高并发场景设计题，你会先从哪些稳定性点展开？",
}


def build_context_text(sources: list[dict]) -> str:
    if not sources:
        return "暂无本地上下文。"
    lines = []
    for item in sources:
        lines.append(f"[{item['type']}] {item['title']}: {item.get('summary', '')}")
    return "\n".join(lines[:8])


def build_answer_messages(question: str, context_text: str, domain: str, tags: list[str], session_summary: str = "") -> list[dict]:
    prompt = {
        "instruction": "你是中文技术面试辅导助手。请生成适合真实面试表达的结构化回答，采用自然分点表达，并尽量结合给定上下文。",
        "question": question,
        "domain": domain,
        "tags": tags,
        "sessionSummary": session_summary,
        "context": context_text,
        "output": {
            "summary": "一句话总结",
            "sections": [{"title": "问题本质", "content": "..."}, {"title": "回答思路", "content": "..."}],
            "projectExample": "项目化表达",
            "pitfalls": ["易错点"],
            "followUps": ["可能追问"],
        },
    }
    return [
        {"role": "system", "content": "只输出合法 JSON，不要输出 Markdown 代码块。"},
        {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
    ]


def build_evaluate_messages(goal: dict, active_question: dict, answer: str, context_text: str) -> list[dict]:
    prompt = {
        "instruction": "你是面试训练教练。请评估用户回答，先生成机器可消费的训练信号，再生成简短反馈。评估要保守，不要泛泛表扬。",
        "goal": goal,
        "activeQuestion": active_question,
        "answer": answer,
        "context": context_text,
        "output": {
            "answerQuality": "poor|fair|good",
            "keyPointCoverage": {
                "coverageLevel": "low|medium|high",
                "expectedKeyPoints": ["关键点"],
                "hitKeyPoints": ["已覆盖"],
                "missingKeyPoints": ["遗漏点"],
            },
            "factualRisk": "low|medium|high",
            "expressionClarity": "weak|okay|strong",
            "shouldFollowUp": "none|clarify|repair|deepen",
            "weaknessTags": ["topic-tag"],
            "confidence": "low|medium|high",
            "feedback": {
                "strengths": ["优点"],
                "gaps": ["缺口"],
                "suggestion": "下一步建议",
            },
        },
    }
    return [
        {"role": "system", "content": "只输出合法 JSON，不要输出 Markdown 代码块。"},
        {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
    ]


class AgentService:
    def __init__(
        self,
        *,
        storage: StorageRepository,
        retrieval_service: RetrievalService,
        llm_service: LlmService,
        session_repo: SessionRepository,
    ):
        self.storage = storage
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service
        self.session_repo = session_repo

    def classify(self, question: str, previous_question: str = "", previous_answer: str = "") -> dict:
        return classify_question(question, previous_question=previous_question, previous_answer=previous_answer)

    def retrieve(self, question: str, domain: str, tags: list[str], filters: Optional[dict] = None, limit: int = 5) -> dict:
        sources = self.retrieval_service.retrieve(question, domain, tags, filters=filters, limit=limit)
        return {
            "domain": domain,
            "tags": tags,
            "sources": sources,
            "contextInsufficient": not bool(sources),
        }

    def answer(self, question: str, llm_config: dict, filters: Optional[dict] = None, top_n: int = 5) -> dict:
        classification = self.classify(question)
        retrieval = self.retrieve(question, classification["domain"], classification["tags"], filters=filters, limit=top_n)
        answer_payload = self.llm_service.complete_json(
            llm_config,
            build_answer_messages(question, build_context_text(retrieval["sources"]), classification["domain"], classification["tags"]),
            temperature=0.35,
        )
        session_id = self.session_repo.create(
            question=question,
            domain=classification["domain"],
            tags=classification["tags"],
            answer_payload=answer_payload,
            filters=filters or {},
            sources=retrieval["sources"],
        )
        return {
            "sessionId": session_id,
            "mode": "qa",
            "state": "ANSWER_READY",
            "domain": classification["domain"],
            "tags": classification["tags"],
            "summary": answer_payload.get("summary") or "暂无总结",
            "sections": answer_payload.get("sections") or [],
            "projectExample": answer_payload.get("projectExample") or "",
            "pitfalls": answer_payload.get("pitfalls") or [],
            "followUps": answer_payload.get("followUps") or [],
            "sources": retrieval["sources"],
            "contextInsufficient": retrieval["contextInsufficient"],
        }

    def follow_up(self, session_id: str, question: str, llm_config: dict) -> dict:
        session = self.session_repo.get(session_id)
        if not session:
            raise ApiError("会话不存在。")
        previous_messages = session["messages"]
        last_assistant = next((msg for msg in reversed(previous_messages) if msg["role"] == "assistant"), None)
        session_summary = json.dumps(last_assistant["content"], ensure_ascii=False) if last_assistant else ""
        classification = self.classify(
            question,
            previous_question=session["session"]["question"],
            previous_answer=session_summary,
        )
        retrieval = self.retrieve(question, classification["domain"], classification["tags"], filters={}, limit=5)
        answer_payload = self.llm_service.complete_json(
            llm_config,
            build_answer_messages(
                question,
                build_context_text(retrieval["sources"]),
                classification["domain"],
                classification["tags"],
                session_summary=session_summary,
            ),
            temperature=0.35,
        )
        self.session_repo.append(session_id, question, answer_payload)
        return {
            "sessionId": session_id,
            "mode": "qa",
            "state": "ANSWER_READY",
            "domain": classification["domain"],
            "tags": classification["tags"],
            "summary": answer_payload.get("summary") or "暂无总结",
            "sections": answer_payload.get("sections") or [],
            "projectExample": answer_payload.get("projectExample") or "",
            "pitfalls": answer_payload.get("pitfalls") or [],
            "followUps": answer_payload.get("followUps") or [],
            "sources": retrieval["sources"],
            "contextInsufficient": retrieval["contextInsufficient"],
        }

    def start_training(self, goal: dict, filters: Optional[dict] = None) -> dict:
        effective_filters = self._normalize_filters(filters, goal)
        normalized_goal = self._normalize_goal(goal, effective_filters)
        topic_progress = self._build_topic_progress(normalized_goal, effective_filters)
        active_question = self._build_active_question(topic_progress[0], effective_filters, question_number=1, follow_up_count=0)
        title = self._build_training_title(normalized_goal, topic_progress[0]["topic"])
        session_id = self.storage.create_training_session(
            title=title,
            question=active_question["prompt"],
            goal=normalized_goal,
            filters=effective_filters,
            active_question=active_question,
            topic_progress=topic_progress,
            sources=active_question["sourceHints"],
        )
        return {
            "sessionId": session_id,
            "mode": "training",
            "state": "WAIT_ANSWER",
            "goal": normalized_goal,
            "topicProgress": topic_progress,
            "activeQuestion": active_question,
            "lastEvaluation": None,
            "suggestedAction": "",
            "reviewSummary": None,
            "availableActions": [],
            "attemptCount": 0,
            "sources": active_question["sourceHints"],
        }

    def submit_training_answer(self, session_id: str, answer: str, llm_config: Optional[dict]) -> dict:
        session = self.storage.get_session(session_id)
        if not session or session["session"]["mode"] != "training":
            raise ApiError("训练会话不存在。")
        active_question = session.get("activeQuestion") or {}
        if not active_question.get("prompt"):
            raise ApiError("当前训练会话没有可作答的问题。")
        evaluation = self._evaluate_training_answer(
            goal=session["session"]["goal"],
            active_question=active_question,
            answer=answer,
            llm_config=llm_config or {},
            context_sources=session.get("sources") or [],
        )
        updated_progress = self._apply_attempt_to_progress(session.get("topicProgress") or [], active_question["topic"], evaluation)
        next_action = self._decide_next(
            goal=session["session"]["goal"],
            progress=updated_progress,
            evaluation=evaluation,
            follow_up_count=int(active_question.get("followUpCount") or 0),
            attempt_count=len(session.get("attempts") or []) + 1,
            current_topic=active_question["topic"],
        )
        self.storage.record_training_attempt(
            session_id,
            topic=active_question["topic"],
            question=active_question["prompt"],
            answer=answer,
            evaluation=evaluation,
            next_action=next_action,
        )
        review_summary = self._build_review_summary(updated_progress, session["session"]["goal"]) if next_action == "SUMMARY" else None
        next_state = "SUMMARY_READY" if next_action == "SUMMARY" else "DECIDE_NEXT"
        self.storage.update_training_session(
            session_id,
            state=next_state,
            question=active_question["prompt"],
            topic_progress=updated_progress,
            review_summary=review_summary or {},
            last_evaluation=evaluation,
            suggested_action=next_action,
        )
        return {
            "sessionId": session_id,
            "mode": "training",
            "state": next_state,
            "goal": session["session"]["goal"],
            "topicProgress": updated_progress,
            "activeQuestion": active_question,
            "lastEvaluation": evaluation,
            "suggestedAction": next_action,
            "reviewSummary": review_summary,
            "availableActions": self._available_actions(next_action),
            "attemptCount": len(session.get("attempts") or []) + 1,
            "sources": active_question.get("sourceHints") or [],
        }

    def advance_training(self, session_id: str, action: str) -> dict:
        session = self.storage.get_session(session_id)
        if not session or session["session"]["mode"] != "training":
            raise ApiError("训练会话不存在。")
        goal = session["session"]["goal"]
        progress = session.get("topicProgress") or []
        current_question = session.get("activeQuestion") or {}
        last_evaluation = session.get("lastEvaluation") or {}
        if action == "SUMMARY":
            review_summary = session.get("reviewSummary") or self._build_review_summary(progress, goal)
            self.storage.update_training_session(
                session_id,
                state="SUMMARY_READY",
                review_summary=review_summary,
                suggested_action="SUMMARY",
            )
            return {
                "sessionId": session_id,
                "mode": "training",
                "state": "SUMMARY_READY",
                "goal": goal,
                "topicProgress": progress,
                "activeQuestion": None,
                "lastEvaluation": last_evaluation or None,
                "suggestedAction": "SUMMARY",
                "reviewSummary": review_summary,
                "availableActions": [],
                "attemptCount": len(session.get("attempts") or []),
                "sources": session.get("sources") or [],
            }
        next_question = self._build_next_question(action, session)
        self.storage.update_training_session(
            session_id,
            state="WAIT_ANSWER",
            question=next_question["prompt"],
            sources=next_question["sourceHints"],
            active_question=next_question,
            topic_progress=progress,
            review_summary={},
            suggested_action="",
        )
        return {
            "sessionId": session_id,
            "mode": "training",
            "state": "WAIT_ANSWER",
            "goal": goal,
            "topicProgress": progress,
            "activeQuestion": next_question,
            "lastEvaluation": last_evaluation or None,
            "suggestedAction": "",
            "reviewSummary": None,
            "availableActions": [],
            "attemptCount": len(session.get("attempts") or []),
            "sources": next_question["sourceHints"],
        }

    def _normalize_filters(self, filters: Optional[dict], goal: dict) -> dict:
        filters = dict(filters or {})
        filters.setdefault("company", goal.get("company", ""))
        filters.setdefault("role", goal.get("role", ""))
        return {"company": filters.get("company", ""), "role": filters.get("role", "")}

    def _normalize_goal(self, goal: Optional[dict], filters: dict) -> dict:
        raw_topics = goal.get("preferredTopics", []) if isinstance(goal, dict) else []
        normalized_topics = []
        for item in raw_topics:
            text = str(item or "").strip()
            if text and text not in normalized_topics:
                normalized_topics.append(text)
        return {
            "company": str((goal or {}).get("company") or filters.get("company") or "").strip(),
            "role": str((goal or {}).get("role") or filters.get("role") or "").strip(),
            "mode": (goal or {}).get("mode") or "speed",
            "preferredTopics": normalized_topics,
        }

    def _build_training_title(self, goal: dict, topic: str) -> str:
        parts = [goal.get("company", ""), goal.get("role", ""), topic]
        return " / ".join([item for item in parts if item]) or "面试训练"

    def _build_topic_progress(self, goal: dict, filters: dict) -> list[dict]:
        topics = []
        for index, topic in enumerate(goal.get("preferredTopics") or []):
            topics.append(
                {
                    "topic": topic,
                    "sourceType": "preferred",
                    "priority": index + 1,
                    "questionCount": 0,
                    "poorCount": 0,
                    "fairCount": 0,
                    "goodCount": 0,
                    "followUpCount": 0,
                    "completed": False,
                }
            )
        if topics:
            return topics

        filtered_posts = [
            post
            for post in self.storage.list_posts()
            if (not filters.get("company") or post.get("company") == filters["company"])
            and (not filters.get("role") or post.get("role") == filters["role"])
        ]
        text_blob = "\n".join(
            f"{post.get('title', '')}\n{post.get('content', '')}\n{post.get('excerpt', '')}" for post in filtered_posts
        ).lower()
        scored = []
        for topic, keywords in DEFAULT_TOPIC_LIBRARY:
            score = sum(text_blob.count(keyword.lower()) for keyword in keywords)
            scored.append((topic, score))
        ranked = [item for item in sorted(scored, key=lambda value: value[1], reverse=True) if item[1] > 0][:4]
        selected = ranked or [(topic, 0) for topic, _ in DEFAULT_TOPIC_LIBRARY[:3]]
        return [
            {
                "topic": topic,
                "sourceType": "local_hot" if score > 0 else "fallback_template",
                "priority": index + 1,
                "questionCount": 0,
                "poorCount": 0,
                "fairCount": 0,
                "goodCount": 0,
                "followUpCount": 0,
                "completed": False,
            }
            for index, (topic, score) in enumerate(selected)
        ]

    def _build_active_question(self, topic_entry: dict, filters: dict, *, question_number: int, follow_up_count: int, previous_evaluation: Optional[dict] = None) -> dict:
        topic = topic_entry["topic"]
        sources = self.storage.search_context(topic, filters=filters, limit=3)
        prompt = self._select_question_prompt(topic, sources, previous_evaluation=previous_evaluation, follow_up_count=follow_up_count)
        return {
            "topic": topic,
            "prompt": prompt,
            "sourceHints": sources,
            "questionNumber": question_number,
            "followUpCount": follow_up_count,
            "kind": "follow_up" if follow_up_count else "main",
        }

    def _select_question_prompt(self, topic: str, sources: list[dict], previous_evaluation: Optional[dict], follow_up_count: int) -> str:
        if follow_up_count and previous_evaluation:
            follow_up_type = previous_evaluation.get("shouldFollowUp") or "clarify"
            missing_points = previous_evaluation.get("keyPointCoverage", {}).get("missingKeyPoints") or []
            target = "、".join(missing_points[:2]) or topic
            if follow_up_type == "repair":
                return f"你刚才这题在 {target} 上有明显偏差。现在请你纠正并重新说明。"
            if follow_up_type == "deepen":
                return f"你刚才已经答到核心方向了。现在请你进一步展开 {target}，说出更像真实面试的完整表达。"
            return f"你刚才在 {target} 上说得还不够清楚。现在请你再讲一遍，并补上关键细节。"
        for source in sources:
            if source.get("type") == "question" and source.get("title"):
                return source["title"]
        for source in sources:
            if source.get("type") == "post" and source.get("summary"):
                return f"结合这类真实面经，围绕 {topic} 回答：{source['summary'][:48]}"
        return QUESTION_TEMPLATES.get(topic, f"请围绕 {topic} 选一道你最常见的面试题来回答。")

    def _evaluate_training_answer(self, *, goal: dict, active_question: dict, answer: str, llm_config: dict, context_sources: list[dict]) -> dict:
        if llm_config.get("apiKey") and llm_config.get("baseUrl") and llm_config.get("model"):
            evaluation = self.llm_service.complete_json(
                llm_config,
                build_evaluate_messages(goal, active_question, answer, build_context_text(context_sources)),
                temperature=0.2,
            )
            return self._normalize_evaluation(evaluation, active_question["topic"])
        return self._heuristic_evaluation(active_question, answer)

    def _normalize_evaluation(self, evaluation: dict, topic: str) -> dict:
        coverage = evaluation.get("keyPointCoverage") or {}
        feedback = evaluation.get("feedback") or {}
        return {
            "answerQuality": evaluation.get("answerQuality") or "fair",
            "keyPointCoverage": {
                "coverageLevel": coverage.get("coverageLevel") or "medium",
                "expectedKeyPoints": coverage.get("expectedKeyPoints") or [topic],
                "hitKeyPoints": coverage.get("hitKeyPoints") or [],
                "missingKeyPoints": coverage.get("missingKeyPoints") or [],
            },
            "factualRisk": evaluation.get("factualRisk") or "low",
            "expressionClarity": evaluation.get("expressionClarity") or "okay",
            "shouldFollowUp": evaluation.get("shouldFollowUp") or "none",
            "weaknessTags": evaluation.get("weaknessTags") or [topic.lower()],
            "confidence": evaluation.get("confidence") or "medium",
            "feedback": {
                "strengths": feedback.get("strengths") or [],
                "gaps": feedback.get("gaps") or [],
                "suggestion": feedback.get("suggestion") or "继续围绕当前题补全关键点。",
            },
        }

    def _heuristic_evaluation(self, active_question: dict, answer: str) -> dict:
        text = answer.strip()
        topic = active_question["topic"]
        keywords = next((items for name, items in DEFAULT_TOPIC_LIBRARY if name == topic), [topic.lower()])
        hit_keywords = [keyword for keyword in keywords if keyword.lower() in text.lower()]
        quality = "good" if len(text) >= 140 and hit_keywords else "fair" if len(text) >= 60 else "poor"
        coverage_level = "high" if len(hit_keywords) >= 2 else "medium" if hit_keywords else "low"
        follow_up_type = "repair" if quality == "poor" else "deepen" if quality == "fair" else "none"
        return {
            "answerQuality": quality,
            "keyPointCoverage": {
                "coverageLevel": coverage_level,
                "expectedKeyPoints": keywords[:3],
                "hitKeyPoints": hit_keywords[:3],
                "missingKeyPoints": [keyword for keyword in keywords[:3] if keyword not in hit_keywords],
            },
            "factualRisk": "medium" if quality == "poor" else "low",
            "expressionClarity": "weak" if len(text) < 60 else "okay",
            "shouldFollowUp": follow_up_type,
            "weaknessTags": [topic.lower().replace(" ", "-")],
            "confidence": "low",
            "feedback": {
                "strengths": ["已经尝试围绕当前专题作答。"] if text else [],
                "gaps": ["回答过短，关键点展开不够。"] if len(text) < 60 else ["还可以再补上更清晰的关键点。"],
                "suggestion": "下一步先补足关键点，再尽量按原理、场景、排查思路组织表达。",
            },
        }

    def _apply_attempt_to_progress(self, progress: list[dict], topic: str, evaluation: dict) -> list[dict]:
        updated = []
        for item in progress:
            if item["topic"] != topic:
                updated.append(item)
                continue
            next_item = dict(item)
            next_item["questionCount"] = int(next_item.get("questionCount") or 0) + 1
            quality = evaluation.get("answerQuality") or "fair"
            if quality == "poor":
                next_item["poorCount"] = int(next_item.get("poorCount") or 0) + 1
            elif quality == "fair":
                next_item["fairCount"] = int(next_item.get("fairCount") or 0) + 1
            else:
                next_item["goodCount"] = int(next_item.get("goodCount") or 0) + 1
            if evaluation.get("shouldFollowUp") != "none":
                next_item["followUpCount"] = int(next_item.get("followUpCount") or 0) + 1
            updated.append(next_item)
        return updated

    def _decide_next(
        self,
        *,
        goal: dict,
        progress: list[dict],
        evaluation: dict,
        follow_up_count: int,
        attempt_count: int,
        current_topic: str,
    ) -> str:
        if attempt_count >= 5:
            return "SUMMARY"
        quality = evaluation.get("answerQuality") or "fair"
        mode = goal.get("mode") or "speed"
        if quality == "poor" and follow_up_count < 2:
            return "FOLLOW_UP"
        if quality == "fair" and mode == "deep" and follow_up_count < 1:
            return "FOLLOW_UP"
        current_progress = next((item for item in progress if item["topic"] == current_topic), {})
        question_count = int(current_progress.get("questionCount") or 0)
        non_poor_count = int(current_progress.get("fairCount") or 0) + int(current_progress.get("goodCount") or 0)
        if question_count >= 3 and non_poor_count >= 2:
            remaining_topics = [item for item in progress if item["topic"] != current_topic and not item.get("completed")]
            if remaining_topics:
                return "SWITCH_TOPIC"
            return "SUMMARY"
        return "NEXT_QUESTION"

    def _available_actions(self, suggested_action: str) -> list[str]:
        if suggested_action == "FOLLOW_UP":
            return ["FOLLOW_UP", "NEXT_QUESTION", "SUMMARY"]
        if suggested_action == "SWITCH_TOPIC":
            return ["SWITCH_TOPIC", "NEXT_QUESTION", "SUMMARY"]
        if suggested_action == "SUMMARY":
            return ["SUMMARY"]
        return ["NEXT_QUESTION", "SUMMARY"]

    def _build_next_question(self, action: str, session: dict) -> dict:
        filters = session["session"]["goal"]
        progress = [dict(item) for item in session.get("topicProgress") or []]
        current = session.get("activeQuestion") or {}
        current_topic = current.get("topic") or (progress[0]["topic"] if progress else "")
        if action == "SWITCH_TOPIC":
            for item in progress:
                if item["topic"] == current_topic:
                    item["completed"] = True
            next_topic = next((item for item in progress if not item.get("completed")), progress[0])
            question_number = int(next_topic.get("questionCount") or 0) + 1
            return self._build_active_question(next_topic, self._normalize_filters({}, session["session"]["goal"]), question_number=question_number, follow_up_count=0)
        if action == "FOLLOW_UP":
            current_topic_entry = next((item for item in progress if item["topic"] == current_topic), {"topic": current_topic})
            return self._build_active_question(
                current_topic_entry,
                self._normalize_filters({}, session["session"]["goal"]),
                question_number=int(current.get("questionNumber") or 1),
                follow_up_count=int(current.get("followUpCount") or 0) + 1,
                previous_evaluation=session.get("lastEvaluation") or {},
            )
        current_topic_entry = next((item for item in progress if item["topic"] == current_topic), {"topic": current_topic})
        return self._build_active_question(
            current_topic_entry,
            self._normalize_filters({}, session["session"]["goal"]),
            question_number=int(current_topic_entry.get("questionCount") or 0) + 1,
            follow_up_count=0,
        )

    def _build_review_summary(self, progress: list[dict], goal: dict) -> dict:
        topic_performance = []
        weak_topics = []
        for item in progress:
            if item.get("poorCount", 0) > item.get("goodCount", 0):
                result = "需要补强"
                weak_topics.append(item["topic"])
            elif item.get("questionCount", 0) == 0:
                result = "尚未开始"
            else:
                result = "可以继续推进"
            topic_performance.append(
                {
                    "topic": item["topic"],
                    "questionCount": item.get("questionCount", 0),
                    "result": result,
                }
            )
        next_suggestion = (
            f"优先回看 {'、'.join(weak_topics[:2])}，再继续 {goal.get('mode') == 'deep' and '深挖追问' or '高频速刷'}。"
            if weak_topics
            else "当前节奏稳定，可以继续下一轮训练。"
        )
        return {
            "headline": "本轮训练已完成，下面是你的阶段复盘。",
            "topicPerformance": topic_performance,
            "nextSuggestion": next_suggestion,
        }
