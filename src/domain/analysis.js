import { inferCompany, inferRole, normalizeText } from "./posts.js";

const TOPIC_RULES = [
  { name: "Redis 与缓存", keys: ["Redis", "缓存", "库存", "分布式锁", "RedLock"] },
  { name: "数据库与事务", keys: ["MySQL", "数据库", "事务", "索引", "主从", "延迟", "SQL"] },
  { name: "消息队列", keys: ["MQ", "RabbitMQ", "Kafka", "消息队列", "异步"] },
  { name: "系统设计", keys: ["设计", "架构", "限流", "幂等", "状态", "订单号"] },
  { name: "项目追问", keys: ["项目", "实习", "业务", "场景", "怎么做"] },
  { name: "语言基础", keys: ["Java", "JVM", "集合", "线程", "Go", "C++"] },
];

export function analyzePosts(posts, filters = {}) {
  const selected = (posts || []).filter((post) => {
    const companyMatched = !filters.company || inferCompany(post) === filters.company;
    const roleMatched = !filters.role || inferRole(post) === filters.role;
    return companyMatched && roleMatched;
  });
  const corpus = selected.map((post) => [post.title, post.content, post.excerpt].join("\n")).join("\n");
  const topics = TOPIC_RULES.map((topic) => ({
    ...topic,
    count: topic.keys.reduce((sum, key) => sum + countKeyword(corpus, key), 0),
  }))
    .filter((topic) => topic.count > 0)
    .sort((a, b) => b.count - a.count);

  const questions = extractQuestionLines(selected);
  const flows = buildFlowInsights(selected, topics);
  return {
    posts: selected,
    topics,
    questions,
    flows,
    report: buildMarkdownReport(selected, topics, questions, flows, filters),
  };
}

function countKeyword(text, keyword) {
  if (!text || !keyword) return 0;
  return (text.match(new RegExp(escapeRegExp(keyword), "gi")) || []).length;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function extractQuestionLines(posts) {
  const lines = [];
  for (const post of posts) {
    const body = normalizeText(post.content || post.excerpt);
    body.split(/\n+/).forEach((line) => {
      const text = normalizeText(line).replace(/^\d+[.、)]\s*/, "");
      if (!text) return;
      if (/[?？]/.test(text) || /怎么|如何|为什么|区别|原理|设计|保证/.test(text)) {
        lines.push({ title: post.title, text });
      }
    });
  }
  return lines.slice(0, 20);
}

function buildFlowInsights(posts, topics) {
  if (!posts.length) {
    return ["帖子库暂无数据，建议先采集或导入面经。"];
  }
  const topTopic = topics[0]?.name || "项目经历";
  return [
    `当前样本共 ${posts.length} 篇，建议先按公司和岗位收窄范围，再看高频题。`,
    `最高频方向是「${topTopic}」，复盘时优先准备可落地的项目例子。`,
    "详情页里的原帖内容适合做逐题拆解，分析页适合沉淀统一答题框架。",
  ];
}

function buildMarkdownReport(posts, topics, questions, flows, filters) {
  const scope = [filters.company, filters.role].filter(Boolean).join(" / ") || "全部帖子";
  const topicText = topics.length
    ? topics.map((topic, index) => `${index + 1}. ${topic.name}：${topic.count} 次`).join("\n")
    : "暂无明显高频主题。";
  const questionText = questions.length
    ? questions.slice(0, 10).map((item, index) => `${index + 1}. ${item.text}`).join("\n")
    : "暂无可识别问题。";
  return `# 面经分析报告

范围：${scope}
样本数：${posts.length}

## 高频主题
${topicText}

## 典型问题
${questionText}

## 复习建议
${flows.map((item) => `- ${item}`).join("\n")}
`;
}

export function buildTopicBankPrompt(analysis) {
  return `请基于以下面经分析生成中文面试专题题库，按主题分组，每组给出 5 个问题、考察点和简短答题方向。\n\n${analysis.report}`;
}
