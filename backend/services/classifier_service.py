from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainRule:
    name: str
    tags: tuple[str, ...]


RULES = (
    DomainRule("缓存一致性", ("redis", "缓存", "一致性", "延迟双删", "双写", "库存")),
    DomainRule("高并发", ("高并发", "秒杀", "吞吐", "削峰", "流量")),
    DomainRule("分布式事务", ("分布式事务", "tcc", "saga", "2pc", "事务一致性")),
    DomainRule("限流", ("限流", "滑动窗口", "令牌桶", "漏桶")),
    DomainRule("消息可靠性", ("mq", "kafka", "rabbitmq", "消息队列", "重复消费", "顺序消息")),
    DomainRule("MySQL", ("mysql", "索引", "事务", "主从", "sql", "回表")),
    DomainRule("系统设计", ("设计", "架构", "拆分", "幂等", "可用性", "状态流转")),
)


def classify_question(question: str, previous_question: str = "", previous_answer: str = "") -> dict:
    haystack = " ".join([question or "", previous_question or "", previous_answer or ""]).lower()
    scores: list[tuple[int, DomainRule, list[str]]] = []
    for rule in RULES:
        matched = [tag for tag in rule.tags if tag.lower() in haystack]
        if matched:
            scores.append((len(matched), rule, matched))
    if scores:
        scores.sort(key=lambda item: item[0], reverse=True)
        _, best_rule, matched = scores[0]
        tags = list(dict.fromkeys([best_rule.name, *matched]))
        intent = "follow_up" if previous_question and len(question) < 40 else "question"
        return {
            "domain": best_rule.name,
            "tags": tags,
            "intent": intent,
            "matchedRules": matched,
        }
    intent = "follow_up" if previous_question and len(question) < 40 else "question"
    return {
        "domain": "通用后端面试",
        "tags": ["通用后端面试"],
        "intent": intent,
        "matchedRules": [],
    }
