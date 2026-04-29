export const PROVIDERS = [
  {
    id: "dashscope",
    name: "阿里云百炼",
    baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    models: ["qwen-plus", "qwen-turbo-latest", "qwen-max"],
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    baseUrl: "https://api.deepseek.com",
    models: ["deepseek-chat", "deepseek-reasoner"],
  },
  {
    id: "moonshot",
    name: "Kimi / Moonshot",
    baseUrl: "https://api.moonshot.cn/v1",
    models: ["kimi-k2.5", "kimi-k2-thinking", "moonshot-v1-128k"],
  },
  {
    id: "zhipu",
    name: "智谱 GLM",
    baseUrl: "https://open.bigmodel.cn/api/paas/v4",
    models: ["glm-4.5", "glm-4.5-air"],
  },
  {
    id: "openai",
    name: "OpenAI",
    baseUrl: "https://api.openai.com/v1",
    models: ["gpt-5.2", "gpt-4.1", "gpt-4o-mini"],
  },
  {
    id: "custom",
    name: "自定义兼容接口",
    baseUrl: "",
    models: [""],
  },
];

export function getProvider(providerId) {
  return PROVIDERS.find((item) => item.id === providerId) || PROVIDERS[0];
}

export function getDefaultProvider() {
  return getProvider("dashscope");
}

export function getDefaultModel(providerId) {
  return getProvider(providerId).models[0] || "";
}

export function createDefaultLLMConfig() {
  const provider = getDefaultProvider();
  return {
    providerId: provider.id,
    model: getDefaultModel(provider.id),
    baseUrl: provider.baseUrl,
    apiKey: "",
    systemPrompt: "你是中文技术面试辅导助手，回答要清晰、真实、适合口述。",
  };
}

export function normalizeLLMConfig(rawConfig = {}) {
  const providerId = rawConfig.providerId || rawConfig.providerKey || "dashscope";
  const provider = getProvider(providerId);
  const model = rawConfig.model || rawConfig.modelId || getDefaultModel(provider.id);
  return {
    ...createDefaultLLMConfig(),
    ...rawConfig,
    providerId: provider.id,
    model,
    baseUrl: rawConfig.baseUrl || provider.baseUrl,
  };
}

export function applyProviderSelection(config, providerId) {
  const provider = getProvider(providerId);
  const model = provider.id === "custom" ? config.model || "" : getDefaultModel(provider.id);
  return {
    ...config,
    providerId: provider.id,
    model,
    baseUrl: provider.id === "custom" ? config.baseUrl || "" : provider.baseUrl,
  };
}
