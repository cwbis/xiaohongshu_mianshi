const LEGACY_POST_KEYS = ["offerscope.posts", "xhs_posts", "posts"];
const LEGACY_XHS_CONFIG_KEYS = ["offerscope.xhsConfig", "xhsConfig"];
const LEGACY_LLM_CONFIG_KEYS = ["offerscope.llmConfig", "llmConfig"];

const COMPANY_ALIASES = [
  "美团",
  "腾讯",
  "阿里",
  "字节",
  "百度",
  "京东",
  "快手",
  "小米",
  "网易",
  "拼多多",
  "滴滴",
  "华为",
];

export function createDefaultXhsConfig() {
  return {
    cookiesStr: "",
    pageSize: 20,
    sortTypeChoice: 0,
  };
}

export function createDefaultCollectForm() {
  return {
    company: "美团",
    role: "后端开发实习",
    keyword: "美团 后端开发 面经",
    page: 1,
  };
}

export function nowIso() {
  return new Date().toISOString();
}

export function normalizeText(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  return String(value).trim() || fallback;
}

export function truncateText(value, max = 120) {
  const text = normalizeText(value);
  return text.length > max ? `${text.slice(0, max)}...` : text;
}

export function normalizeDateLabel(value) {
  const text = normalizeText(value);
  if (!text) return "未记录";
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) return text.slice(0, 10);
  if (/^\d{2}-\d{2}$/.test(text)) return text;
  return text;
}

export function inferCompany(record) {
  const explicit = normalizeText(record?.company);
  if (explicit) return explicit;
  const haystack = [record?.title, record?.keyword, record?.content, record?.excerpt].join(" ");
  return COMPANY_ALIASES.find((name) => haystack.includes(name)) || "未分组公司";
}

export function inferRole(record) {
  const explicit = normalizeText(record?.role);
  if (explicit) return explicit;
  const haystack = [record?.title, record?.keyword, record?.content, record?.excerpt].join(" ");
  if (/前端/.test(haystack)) return "前端开发";
  if (/后端|Java|Go|C\+\+/.test(haystack)) return "后端开发";
  if (/产品/.test(haystack)) return "产品";
  if (/算法|机器学习|AI/.test(haystack)) return "算法";
  if (/测试|QA/.test(haystack)) return "测试";
  return "通用面经";
}

export function postIdentity(record) {
  if (record?.noteId) return `note:${record.noteId}`;
  if (record?.sourceUrl) return `url:${record.sourceUrl}`;
  return `id:${record?.id || crypto.randomUUID()}`;
}

export function normalizePostRecord(record, fallback = {}) {
  const company = normalizeText(record?.company, fallback.company || inferCompany(record));
  const role = normalizeText(record?.role, fallback.role || inferRole(record));
  const keyword = normalizeText(record?.keyword, fallback.keyword || `${company} ${role} 面经`);
  const content = normalizeText(record?.content || record?.desc || record?.excerpt);
  return {
    ...record,
    id: normalizeText(record?.id, `post-${crypto.randomUUID()}`),
    noteId: normalizeText(record?.noteId),
    sourceUrl: normalizeText(record?.sourceUrl),
    title: normalizeText(record?.title, "未命名帖子"),
    excerpt: normalizeText(record?.excerpt, truncateText(content, 180)),
    content,
    author: normalizeText(record?.author, "匿名用户"),
    publishTime: normalizeText(record?.publishTime),
    coverUrl: normalizeText(record?.coverUrl),
    likeCount: record?.likeCount ?? "",
    commentCount: record?.commentCount ?? "",
    collectCount: record?.collectCount ?? "",
    noteTypeLabel: normalizeText(record?.noteTypeLabel, "图文"),
    company,
    role,
    keyword,
    collectedAt: normalizeText(record?.collectedAt, nowIso()),
  };
}

export function mergePostRecords(records) {
  const map = new Map();
  for (const item of records || []) {
    const normalized = normalizePostRecord(item);
    const key = postIdentity(normalized);
    const current = map.get(key);
    map.set(key, current ? { ...current, ...normalized, id: current.id || normalized.id } : normalized);
  }
  return [...map.values()].sort((a, b) => String(b.collectedAt || "").localeCompare(String(a.collectedAt || "")));
}

export function buildPostFromSearchItem(item, form) {
  return normalizePostRecord(item, {
    company: form.company,
    role: form.role,
    keyword: form.keyword,
  });
}

export function buildLibraryGroups(posts) {
  const companies = new Map();
  for (const post of mergePostRecords(posts)) {
    const company = inferCompany(post);
    const role = inferRole(post);
    if (!companies.has(company)) {
      companies.set(company, { id: company, title: company, count: 0, roles: new Map(), posts: [] });
    }
    const companyGroup = companies.get(company);
    companyGroup.count += 1;
    companyGroup.posts.push(post);
    if (!companyGroup.roles.has(role)) {
      companyGroup.roles.set(role, { id: role, title: role, count: 0, posts: [] });
    }
    const roleGroup = companyGroup.roles.get(role);
    roleGroup.count += 1;
    roleGroup.posts.push(post);
  }
  return [...companies.values()].map((company) => ({
    ...company,
    roles: [...company.roles.values()].sort((a, b) => b.count - a.count),
  }));
}

export function getVisibleLibraryPosts(groups, companyId, roleId) {
  const company = groups.find((item) => item.id === companyId) || groups[0];
  if (!company) return { company: null, role: null, posts: [] };
  const role = roleId ? company.roles.find((item) => item.id === roleId) : null;
  return {
    company,
    role,
    posts: role ? role.posts : company.posts,
  };
}

export function readLegacyStorageSnapshot() {
  const readJson = (keys) => {
    for (const key of keys) {
      const raw = window.localStorage.getItem(key);
      if (!raw) continue;
      try {
        return JSON.parse(raw);
      } catch {
        return null;
      }
    }
    return null;
  };
  return {
    posts: readJson(LEGACY_POST_KEYS) || [],
    xhsConfig: readJson(LEGACY_XHS_CONFIG_KEYS),
    llmConfig: readJson(LEGACY_LLM_CONFIG_KEYS),
  };
}

export function hasLegacyStorage(snapshot) {
  return Boolean(
    snapshot?.posts?.length ||
      snapshot?.xhsConfig ||
      snapshot?.llmConfig
  );
}

export function clearLegacyStorage() {
  [...LEGACY_POST_KEYS, ...LEGACY_XHS_CONFIG_KEYS, ...LEGACY_LLM_CONFIG_KEYS].forEach((key) => {
    window.localStorage.removeItem(key);
  });
}

export function makeDemoPosts() {
  return mergePostRecords([
    {
      title: "美团核心本地商业业务研发平台 一面 04-22",
      company: "美团",
      role: "后端开发实习",
      author: "352",
      publishTime: "04-22",
      likeCount: 25,
      content:
        "1. 自我介绍\n2. 唯一订单号怎么设计？\n3. 如何保证订单支付的幂等性，状态流转怎么设计？\n4. 数据库主从延迟、状态校验怎么保证准确？\n5. Redis 库存和数据库不一致怎么办？\n6. Redis 扣减库存怎么处理？\n7. 为什么选择 RabbitMQ？",
      keyword: "美团 后端开发 面经",
    },
    {
      title: "腾讯后台开发实习一面复盘",
      company: "腾讯",
      role: "后端开发实习",
      author: "Gzrrr",
      publishTime: "08-26",
      likeCount: 167,
      content:
        "八股围绕 Redis、MySQL、消息队列展开，项目追问比较细。建议准备限流、缓存一致性、分布式锁和线程池参数。",
      keyword: "腾讯 后端开发 面经",
    },
    {
      title: "美团暑期一面面经",
      company: "美团",
      role: "Java 后端",
      author: "r=Arccos(sinθ)",
      publishTime: "04-17",
      likeCount: 57,
      content: "主要问 Java 集合、JVM、数据库索引、项目里的接口设计，以及为什么选择当前技术栈。",
      keyword: "美团 Java 面经",
    },
  ]);
}
